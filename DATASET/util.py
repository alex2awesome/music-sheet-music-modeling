from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import os

top_100_pianists = [
    "Vladimir Horowitz",
    # "Arthur Rubinstein",
    # "Glenn Gould",
    # "Sviatoslav Richter",
    # "Alfred Cortot",
    # "Claudio Arrau",
    # "Wilhelm Kempff",
    # "Artur Schnabel",
    "Emil Gilels",
    "Alfred Brendel",
    "Martha Argerich",
    # "Maurizio Pollini",
    # "Vladimir Ashkenazy",
    # "Rudolf Serkin",
    # "Krystian Zimerman",
    # "Murray Perahia",
    "András Schiff",
    "Evgeny Kissin",
    # "Yevgeny Sudbin",
    "Lang Lang",
    "Daniil Trifonov",
    # "Grigory Sokolov",
    # "Leif Ove Andsnes",
    "Yuja Wang",
    "Mitsuko Uchida",
    "Ivo Pogorelić",
    "Alicia de Larrocha",
    # "John Ogdon",
    "Shura Cherkassky",
    # "Sergei Rachmaninoff",
    "Josef Hofmann",
    "Walter Gieseking",
    "Maria João Pires",
    "Ignaz Friedman",
    "Josef Lhévinne",
    "Van Cliburn",
    "Leon Fleisher",
    "Mikhail Pletnev",
    "John Browning",
    "Lili Kraus",
    "Samson François",
    "Wilhelm Backhaus",
    "Clara Haskil",
    # "Dinu Lipatti",
    # "Vladimir Sofronitsky",
    # "Géza Anda",
    # "Radu Lupu",
    # "Alexis Weissenberg",
    # "Jean-Yves Thibaudet",
    # "Gina Bachauer",
    "Georges Cziffra",
    "Gary Graffman",
    "David Oistrakh",
    "Friedrich Gulda",
    "Annie Fischer",
    "Gidon Kremer",
    "Richard Goode",
    "Rosalyn Tureck",
    "Solomon Cutner",
    "Victor Merzhanov",
    "Tatiana Nikolayeva",
    "Stephen Kovacevich",
    "Simon Barere",
    "Seymour Lipkin",
    "Sergio Tiempo",
    "Sequeira Costa",
    "Ruth Laredo",
    "Rosina Lhevinne",
    "Robert Casadesus",
    "Péter Frankl",
    "Paul Lewis",
    "Olli Mustonen",
    "Nikolai Lugansky",
    "Mikhail Rudy",
    "Menahem Pressler",
    "Magdalena Baczewska",
    "Lars Vogt",
    "Lazar Berman",
    "Khatia Buniatishvili",
    "Kathleen Long",
    "John Lill",
    "João Carlos Martins",
    "Jeno Jando",
    "Ivan Moravec",
    "Ingrid Fliter",
    "Helene Grimaud",
    "Hans Richter-Haaser",
    "György Cziffra",
    "Grigory Ginzburg",
    "Grigory Kogan",
    "Gregory Sokolov",
    "George Szell",
    "Gary Karr",
    "Fazil Say",
    "Eric Heidsieck",
    "Dinu Lipatti",
    "David Helfgott",
    "Daniel Barenboim",
    "Dame Myra Hess",
    "Cyprien Katsaris",
    "Conrad Tao",
    "Conrad Hansen",
    "Claude Frank",
    "Christian Zacharias",
    "Charles Rosen",
    "Catherine Collard"
]

api_keys = [
    # "AIzaSyAyQRbSJnm_5gy3_5XbJbU_jathq9YRQww" # usc-research
    "AIzaSyDRZ5IJrzhNkjlc3K8TISG8MH3whFEYsE4",  # music-project
    "AIzaSyBEgj08BBTcI7Y1bzmprFoPK9loXuPZ5tI",  # music-project-2
    "AIzaSyDD2DONt19-SkWa2Xlcq0SMdukfMPm3Hjs",  # music-project-3
    "AIzaSyDlPvzNHso3xYei6wtl5McSPDiNsEx4FFU",  # music-project-4
]

def load_proxies(proxy_file=None, proxy_type="socks5", include_username_password=True):
    if proxy_file is None:
        proxy_file = os.path.expanduser('~/proxies.txt')
    proxies = []
    with open(proxy_file, "r") as file:
        for line in file:
            if proxy_type == "socks5":
                ip, port, username, password = line.strip().split(":")
                if include_username_password:
                    proxy = f"socks5://{username}:{password}@{ip}:{port}"
                else: # do this is you're running on a server that is already authorized.
                    proxy = f"socks5://{ip}:{port}"
            else:
                proxy = line.strip()
            proxies.append(proxy)
    return proxies

async def get_playwright(
        proxy=None,
        headless=True,
        browser=None,
        context=None,
        page=None,
        playwright=None
):
    if browser is not None:
        await browser.close()
    if playwright is not None:
        await playwright.stop()

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
    if proxy is None:
        context = await browser.new_context()
    if proxy is not None:
        context = await browser.new_context(proxy={"server": proxy})
    page = await context.new_page()
    return page, context, browser, playwright


import asyncio
from playwright.async_api import async_playwright
import time

async def get_ip_address():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('https://www.whatismyip.com/')
        time.sleep(5)
        ip_element = await page.query_selector('#ipv4 > span')
        ip_address = await ip_element.text_content()
        print(f'IPv4 Address: {ip_address}')
        await browser.close()