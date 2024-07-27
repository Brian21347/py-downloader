"""
This module provides a web crawler that will search a web page
"""


import requests
from bs4 import BeautifulSoup
import warnings
import os


PREFIXES = ["http://", "https://"]


def get_full_url(url: str, src: str) -> str:
    if not src: return ""
    if src[0] != "/": full = url_previous_folder(url) + "/" + src
    else: full = url_domain(url) + src
    for pre in PREFIXES:
        if pre not in full: continue
        k = pre
        full = full.removeprefix(pre)
    return k + os.path.normpath(full).replace("\\", "/")


def crawl(
        url: str, 
        depth: int, 
        css_selector: str, 
        max_sites: int =  -1,
        allow_duplicate_to_download_links: bool = False,
        verbose: bool = False,
        white_list: list[str] = None, 
        black_list: list[str] = None
    ) -> tuple[set[str], int, int, int]:
    if white_list is None: white_list = []
    if black_list is None: black_list = []
    visited = set()
    visited.add(url)
    visiting = set()
    visiting.add(url)
    to_visit = set()
    to_download = []
    min_on_page = 1e9
    max_on_page = 0

    for iter in range(depth):
        if verbose: print(f"Searching at a depth of {iter}.")
        for url in visiting:
            if verbose: print(f"\tSearching: \"{url}\"...")
            visited.add(url)
            resp = requests.get(url)
            soup = BeautifulSoup(resp.text, features="html.parser")
            
            num_a_tags = 0
            for a_tag in soup.select("a"):
                link = get_full_url(url, a_tag.attrs.get('href'))
                if not link: continue
                if white_list and url_domain(link) not in white_list or url_domain(link) in black_list: continue
                if link in visited or link in to_visit or link in visiting: continue
                to_visit.add(link)
                num_a_tags += 1
            if verbose: print(f"\t\tFound {num_a_tags} links on the page.")
            
            count = 0
            for element in soup.select(css_selector):
                down_url = get_full_url(url, element.attrs.get("src"))
                if not down_url: continue
                if down_url in to_download and not allow_duplicate_to_download_links: continue
                to_download.append(down_url)
                count += 1
            min_on_page = min(min_on_page, count)
            max_on_page = max(max_on_page, count)
            if verbose: print(f"\t\tFound {count} elements to download.")

            if len(visited) >= max_sites and max_sites != -1:
                warnings.warn(f"Crawled to the maximum allowed number of sites; skipped over at least {len(to_visit)}")
                return to_download, len(visited), min_on_page, max_on_page
        if verbose: print(f"Found {len(to_visit)} links to visit; visited a total of {len(visited)} pages.")
        if not len(to_visit): break
        visiting = to_visit.copy()
        to_visit = set()
    return to_download, len(visited), min_on_page, max_on_page


def url_domain(url: str) -> str:
    prefix = ""
    for pre in PREFIXES:
        if not url.__contains__(pre): continue
        url = url.removeprefix(pre)
        prefix = pre
        break
    i = url.find('/')
    if i == -1: return url
    return prefix + url[:i]


def url_previous_folder(url: str) -> str:
    i = url.rfind("/")
    if i == -1: raise ValueError(f"Url \"{url}\" does not have folder in the level above")
    return url[:i]
