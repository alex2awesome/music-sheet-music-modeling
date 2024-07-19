
import pandas as pd
import glob
import os
here = os.path.dirname(os.path.abspath(__file__))
hf_cache_dir = '/project/jonmay_231/spangher/huggingface_cache'
os.environ['HF_HOME'] = hf_cache_dir
os.environ['TRANSFORMERS_CACHE'] = hf_cache_dir
os.environ['HF_TOKEN_PATH'] = f'{hf_cache_dir}/token'
os.environ['HF_TOKEN'] = open(f'{hf_cache_dir}/token').read().strip()

from retriv import DenseRetriever
os.environ['RETRIV_BASE_PATH'] = here

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str)

    args = parser.parse_args()

    pre_fetched_files = pd.read_json(f'{args.data_dir}/youtube-links__10-6.jsonl', lines=True)
    atepp_files = pd.concat(list(map(pd.read_csv, glob.glob(f'{args.data_dir}/ATEPP-metadata-1.*')))).reset_index(drop=True)
    quantized_midi_files = pd.read_csv(f'{args.data_dir}/quantized-piano-to-fetch.csv', index_col=0)
    pre_fetched_files['id'] = 'luis-' + pre_fetched_files.reset_index()['index'].astype(str)
    atepp_files['id'] = 'atepp-' + atepp_files.reset_index()['index'].astype(str)
    pre_fetched_files['text'] = pre_fetched_files['title']
    atepp_files['text'] = atepp_files['track'] + ' ' + atepp_files['composer']

    to_index = pd.concat([
        pre_fetched_files[['id', 'text']].dropna(),
        atepp_files[['id', 'text']].dropna()
    ]).to_dict(orient='records')


    dr = DenseRetriever(
        index_name='performance-midis',
        model='Salesforce/SFR-Embedding-2_R',
        normalize=True,
        device='cuda',
        use_ann=True,
        transformers_cache_dir=hf_cache_dir
    )
    dr = dr.index(
        collection=to_index,
        batch_size=32,
        show_progress=True,  # Default value
    )
