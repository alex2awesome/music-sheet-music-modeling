import os.path

from pyyoutube import Api
import argparse
import pandas as pd
from tqdm.auto import tqdm
import random
import time
import glob
import logging
from urllib.parse import urlencode
import json
from util import top_100_pianists, api_keys, load_proxies, get_playwright
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import parse_qs
import unicodedata

logging.basicConfig(
    level=logging.INFO,  # Set to logging.INFO or logging.ERROR to reduce output verbosity
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]'
)

REFRESH_BROWSER_EVERY_N_ITER = 10
NUM_TOTAL_TRIES = 20
TIMEOUT = 120_000

norm = lambda x: unicodedata.normalize("NFKD", x)

def query_api(query, fname, performer, with_performer, verbose):
    api_key = random.choice(api_keys)
    api = Api(api_key=api_key)

    try:
        r = api.search_by_keywords(q=query, search_type=["video"], count=3, limit=3)
    except Exception as e:
        print(f"Error fetching data from YouTube API: {e}")
        return

    time.sleep(random.random())

    output = []
    # check if the performer is in the search results
    for r_i in r.items:
        r_i_dict = r_i.to_dict()
        if verbose:
            logging.info(f"Result for {query}:")
            logging.info(str(r_i_dict) + '\n\n')

        vid_id = r_i_dict.get('id', {}).get('videoId')
        if not vid_id:
            continue

        youtube_url = f'https://www.youtube.com/watch?v={vid_id}'
        output_dict = {
            'original_file': fname,
            'youtube_url': youtube_url,
            'attempted_performer': performer,
            'with_performer': with_performer,
        }

        snippet = r_i_dict.get('snippet', {})
        snippet.pop('thumbnails', None)
        snippet.pop('liveBroadcastContent', None)
        output_dict.update(snippet)
    return output


async def query_scrape(browser, proxies, query, fname, performer, with_performer, verbose, num_zero_tries=0):
    try:
        proxy = random.choice(proxies)
        context = await browser.new_context(proxy={'server': proxy})
        page = await context.new_page()
        url_query_term = urlencode({'search_query': query})
        await page.goto(f'https://www.youtube.com/results?{url_query_term}', timeout=TIMEOUT)
        # search for the query
        # await page.locator('input#search').fill(query)
        # search_icon_sel = '#search-icon-legacy'
        # await page.wait_for_selector(search_icon_sel, state='visible')
        # time.sleep(random.random() * 5)
        # await page.locator(search_icon_sel).click()
        # time.sleep(random.random())
        # await page.locator(search_icon_sel).click()
        video_filter_sel = '#chips > yt-chip-cloud-chip-renderer > yt-formatted-string[title="Videos"]'
        time.sleep(random.random() * 3)
        if await page.is_visible(video_filter_sel):
            await page.locator(video_filter_sel).click(timeout=TIMEOUT)
        # await page.wait_for_selector(video_filter_sel, state='visible')
        # await page.locator(video_filter_sel).click()
        time.sleep(random.random() * 2)
    except Exception as e:
        print(f"Error fetching data from YouTube API: {e}")
        return []

    # parse output
    all_outputs = []

    # parse HTML
    html = await page.content()
    soup = BeautifulSoup(html, 'lxml')
    content_div_container = list(filter(lambda x: x.find('a'), soup.select('div#contents')))
    if len(content_div_container) == 0:
        if verbose:
            logging.info(f"No results found for {query}")
        return []
    content_div_container = content_div_container[0]
    video_cards = content_div_container.find_all(attrs={'class': 'text-wrapper style-scope ytd-video-renderer'})

    if verbose:
        logging.info(f"Found {len(video_cards)} video cards for {query}")

    for video_card in video_cards:
        output_dict = {}
        output_dict['original_file'] = fname
        output_dict['attempted_performer'] = performer
        output_dict['with_performer'] = with_performer
        # get
        a_link = video_card.find(attrs={'id': 'meta'}).find('a')
        output_dict['title'] = a_link.attrs['title']
        href = a_link.attrs['href']
        params = parse_qs(href.split('?')[-1])
        vid_id = params.get('v', [None])[0]
        output_dict['youtube_url'] = f'https://www.youtube.com/watch?v={vid_id}'
        ##
        metadata = video_card.find(attrs={'id': 'metadata-line'})
        if metadata is not None:
            metadata_spans = metadata.find_all('span')
            output_dict['metadata'] = list(map(lambda x: norm(x.get_text()), metadata_spans))
        ##
        channel = video_card.find(attrs={'id': 'text-container', 'class': "style-scope ytd-channel-name"})
        if channel is not None:
            output_dict['channel_name'] = norm(channel.find('a').get_text())
            output_dict['channel_handle'] = channel.find('a').attrs.get('href')
        ##
        description = video_card.find(attrs={'id': 'description-text'})
        if description is not None:
            output_dict['description'] = description.get_text()
        description_snippet = video_card.find(attrs={'class': 'metadata-snippet-text style-scope ytd-video-renderer'})
        if description_snippet is not None:
            output_dict['description_snippet'] = norm(description_snippet.get_text())
        all_outputs.append(output_dict)

    return all_outputs


def make_query_string(fname, with_performer, top_pianists):
    query_orig = (
        fname
        .replace('../data/midi_from_krn', '')
        .replace('../data/midi_from_mxl', '')
        .replace('Classical Piano Midis', '')
        .replace('songs', '')
        .replace('early-music', '')
        .replace('polyrhythm', '')
        .replace('/', ' ')
        .replace('-', ' ')
        .replace('_', ' ')
        .replace('.mid', '')
        .strip()
    )
    performer = ''
    if with_performer:
        performer = random.choice(top_pianists)
        query = f'Piano piece: {query_orig}. Performed by: {performer}. Solo piano.'
    else:
        query = f'Piano piece: {query_orig}. Solo piano.'
    return query, performer


async def fetch_performances(
    input_df,
    top_pianists,
    num_performances_per_piece,
    num_pieces_to_fetch=None,
    output_filename='performances.jsonl',
    records_filename='paired-performances_fetching-records.jsonl',
    records_filepattern=None,
    start_from_scratch=False,
    verbose=False,
    method='scrape', # scrape or api
):
    if not start_from_scratch:
        if records_filepattern:
            fps = glob.glob(records_filepattern)
            fetched_records = list(map(lambda x: pd.read_json(x, lines=True), fps))
            fetched_df = pd.concat(fetched_records)
            if len(fetched_df) > 0:
                input_df = input_df.loc[lambda df: ~df['file'].isin(fetched_df['fname'])]

    if method == 'scrape':
        proxies = load_proxies(include_username_password=False)
        page, context, browser, playwright = await get_playwright(
            proxy=random.choice(proxies), headless=True
        )

    records_file = open(records_filename, 'a')
    output_file = open(output_filename, 'a')
    for idx, fname in tqdm(enumerate(input_df['file'].sample(frac=1).iloc[:num_pieces_to_fetch]), total=len(input_df)):
        record = {
            'fname': fname,
            'started': True
        }
        if (idx % REFRESH_BROWSER_EVERY_N_ITER == 0) and method == 'scrape':
            page, context, browser, playwright = await get_playwright(
                proxy=random.choice(proxies),
                headless=True,
                browser=browser,
                context=context,
                page=page,
                playwright=playwright
            )

        num_retrieved = 0
        num_tries = 0
        num_zero_tries = 0
        with_performer = True
        while (num_tries < NUM_TOTAL_TRIES):
            if (num_performances_per_piece > 0) and (num_retrieved >= num_performances_per_piece):
                break

            query, performer = make_query_string(fname, with_performer, top_pianists)
            if verbose:
                logging.info(f"Searching for {query}")

            if method == 'api':
                r_items = query_api(query, fname, performer, with_performer, verbose)
            else:  # method == 'scrape'
                r_items = await query_scrape(browser, proxies, query, fname, performer, with_performer, verbose)

            # substitute a generic performer if the search returns no results
            if len(r_items) == 0:
                num_zero_tries += 1
                if (num_zero_tries >= 3) and with_performer:
                    with_performer = False
                if num_zero_tries >= 4:
                    break
                continue

            num_retrieved += 1
            for output_dict in r_items:
                output_file.write(json.dumps(output_dict) + '\n')
                if verbose:
                    logging.info(f"Found a performance for {query}")
                    logging.info(str(output_dict) + '\n\n')

            num_tries += 1
        record['num_retrieved'] = num_retrieved
        record['num_tries'] = num_tries
        record['num_zero_tries'] = num_zero_tries
        records_file.write(json.dumps(record) + '\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch performance variants")
    parser.add_argument("--input_file", type=str, help="Directory containing MusicXML files")
    parser.add_argument("--output_file", type=str, help="Directory to save MIDI files")
    parser.add_argument("--start_idx", type=int, default=0)
    parser.add_argument("--end_idx", type=int, default=-1)
    parser.add_argument(
        "--num_performances_per_piece",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--num_top_pianists",
        type=int,
        default=50,
    )
    parser.add_argument(
        "--start_from_scratch",
        action="store_true"
    )
    parser.add_argument("--verbose", action="store_true", help="enable prints")
    args = parser.parse_args()

    top_pianists = top_100_pianists[:args.num_top_pianists]
    input_df = pd.read_csv(args.input_file)

    if args.end_idx > 0:
        input_df = input_df.iloc[args.start_idx:args.end_idx]
        args.output_file = args.output_file.replace('.jsonl', f'__{args.start_idx}_{args.end_idx}.jsonl')
    records_filename = args.output_file.replace('.jsonl', '__records.jsonl')
    records_filepattern = '*__records.jsonl'

    import asyncio
    asyncio.run(
        fetch_performances(
            input_df=input_df,
            top_pianists=top_pianists,
            num_performances_per_piece=args.num_performances_per_piece,
            output_filename=args.output_file,
            records_filename=records_filename,
            records_filepattern=records_filepattern,
            start_from_scratch=args.start_from_scratch,
            verbose=args.verbose,
        )
    )

    logging.info(f"Output saved to {args.output_file}")
    # python fetch_performance_midis.py --input_file quantized-piano-to-fetch.csv --output_file scraped-youtube-performances.jsonl --verbose --num_top_pianists 10 --num_performances_per_piece 3 --start_idx 0 --end_idx 2000