import argparse
import json
import os
from tqdm.auto import tqdm
import pandas as pd

instruction_variations = [
    "Instruct: Match this partial and confusing title to a full-length title. Query: ",
    "Instruct: Match this partial title to a full-length title. Query: ",
    "Instruct: Match this partial and confusing song title to a full-length song title. Query: ",
    "Instruct: Match this partial song title to a full-length song title. Query: ",
]
here = os.path.dirname(os.path.abspath(__file__))
hf_cache_dir = '/project/jonmay_231/spangher/huggingface_cache'
HF_HOME = "/project/jonmay_231/spangher/huggingface_cache"
config_data = json.load(open(os.path.expanduser('~/.hf_config.json')))
os.environ['HF_TOKEN'] = config_data["HF_TOKEN"]
os.environ['HF_HOME'] = HF_HOME
os.environ['TRANSFORMERS_CACHE'] = HF_HOME
os.environ['VLLM_WORKER_MULTIPROC_METHOD'] = 'spawn'

BATCH_SIZE = 100

def load_model(model: str):
    import torch
    from vllm import LLM,  SamplingParams
    torch.cuda.memory_summary(device=None, abbreviated=False)
    model = LLM(
        model,
        dtype=torch.float16,
        tensor_parallel_size=torch.cuda.device_count(),
        download_dir=hf_cache_dir, # sometimes the distributed model doesn't pay attention to the
        enforce_eager=True
    )
    return model

def match_retriever(args):
    from retriv import DenseRetriever
    os.environ['RETRIV_BASE_PATH'] = here
    input_df = pd.read_csv(args.input, index_col=0)
    dr = DenseRetriever.load(args.collection_name, use_gpu=True, transformers_cache_dir=hf_cache_dir)
    input_df['query_base'] = (
        input_df['file']
        .str.replace('../data/midi_from_krn', '')
        .str.replace('../data/midi_from_mxl', '')
        .str.replace('Classical Piano Midis', '')
        .str.replace('songs', '')
        .str.replace('early-music', '')
        .str.replace('polyrhythm', '')
        .str.replace('/', ' ')
        .str.replace('-', ' ')
        .str.replace('_', ' ')
        .str.replace('.mid', '')
        .str.strip()
    )

    # get sets of ids to filter to
    to_index = pd.read_csv(args.original_index_file)
    atepp_ids = to_index.loc[lambda df: df['id'].str.contains('atepp')]['id'].tolist()
    luis_ids = to_index.loc[lambda df: df['id'].str.contains('luis')]['id'].tolist()
    longer_ids_to_filter = to_index.loc[lambda df: df['text'].str.split().str.len() > 4]['id'].tolist()
    id_sets_to_filter_to = [longer_ids_to_filter, atepp_ids, luis_ids]

    matched = []
    with open(args.output_file, 'w') as f:
        for _, (quantized_idx, query) in tqdm(input_df.iterrows(), total=len(input_df)):
            for instruction in instruction_variations:
                for ids_to_filter_to in id_sets_to_filter_to:
                    results = dr.search(instruction + query, cutoff=10, include_id_list=ids_to_filter_to)
                    for r in results:
                        f.write(json.dumps({
                            'quantized_idx': quantized_idx,
                            'query': query,
                            'instruction': instruction,
                            'matched_id': r['id'],
                            'matched_text': r['text'],
                            'matched_score': float(r['score']),
                        }))
                        f.write('\n')


def match_llm(args):
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams
    import unicodedata

    input_df = pd.read_json(args.input, lines=True)
    input_df = (
        input_df
            .loc[lambda df: df['matched_score'] > args.llm_threshold]
            .drop_duplicates(['query', 'matched_text'])
            [['query', 'matched_text', 'quantized_idx', 'matched_id']]
    )

    # load model
    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct", download_dir=hf_cache_dir)
    message_batches = []
    id_batches = []
    messages = []
    ids = []
    for idx, (query, matched_text, quant_id, matched_id) in input_df.iterrows():
        prompt = f"""
            Here are two partial titles:
            ```
            Title 1: {query}
            Title 2: {matched_text}
            ```
            Do they refer to the same song? Answer "yes" or "no".
            Be extra careful about numbers.
            Do not say anything else. 
        """
        message = [{"role": "system", "content": "You are a helpful musician's assistant.",},
                   {"role": "user", "content": prompt}]
        formatted_prompt = tokenizer.apply_chat_template(message, tokenize=False, add_generation_prompt=True)

        messages.append(formatted_prompt)
        ids.append((quant_id, matched_id, query, matched_text))

        if len(messages) >= BATCH_SIZE:
            message_batches.append(messages)
            id_batches.append(ids)
            messages = []
            ids = []

    # load the model
    model = load_model('meta-llama/Meta-Llama-3-70B-Instruct')
    sampling_params = SamplingParams(temperature=0.1, max_tokens=1024)
    if args.start_idx is None:
        args.start_idx = 0
    if args.end_idx is None:
        args.end_idx = len(ids)

    # generate the summaries
    start_idx = args.start_idx
    end_idx = start_idx + BATCH_SIZE
    for messages, ids in zip(tqdm(message_batches), id_batches):
        fname = f'matched_data_70b__{start_idx}_{end_idx}.jsonl'
        outputs = model.generate(messages, sampling_params)
        with open(fname, 'wb') as file:
            for id, output in zip(ids, outputs):
                response = output.outputs[0].text
                response = unicodedata.normalize('NFKC', response)
                if response and id:
                    file.write(json.dumps({
                        'quantized_idx': id[0],
                        'matched_id': id[1],
                        'response': response,
                        'query': id[2],
                        'matched_text': id[3],
                    }).encode('utf-8'))
                    file.write(b'\n')
        start_idx = end_idx
        end_idx = start_idx + BATCH_SIZE

    # put all the files together into one and delete the individual files
    with open(args.output_file, 'w') as f:
        for idx in range(args.start_idx, args.end_idx, BATCH_SIZE):
            fname = f'matched_data_70b__{idx}_{idx + BATCH_SIZE}.jsonl'
            with open(fname, 'r') as file:
                f.write(file.read())
            os.remove(fname)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str)
    parser.add_argument('--matching_process', type=str, default='retriever', choices=['retriever', 'llm'])
    parser.add_argument('--collection_name', type=str, default='performance-midis')
    parser.add_argument('--output_file', type=str)
    parser.add_argument('--original_index_file', type=str, default='file-of-performance-midis-to-index.csv')
    parser.add_argument('--llm_threshold', type=float, default=.80)
    parser.add_argument('--start_idx', type=int, default=None)
    parser.add_argument('--end_idx', type=int, default=None)


    args = parser.parse_args()
    if args.matching_process == 'retriever':
        match_retriever(args)
    else:
        match_llm(args)