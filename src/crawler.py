"""
This module implements an asynchronous crawler.

TODO:
- Respect robots.txt
- Find all links in sitemap.xml
- Provide a user agent
- Normalize urls (www.example.com and www.example.com/ are the same)
- Skip filetypes (jpg, pdf, webp) or include only filetypes (html, php, NONE)
- Max concurrent connections per domain
- Rate limiting
- Rate limiting per domain
- Store connections as graph
- Store results to database
- Scale

URI schemes: https://www.iana.org/assignments/uri-schemes/uri-schemes.xhtml
IP ranges for the google bots: https://developers.google.com/static/search/apis/ipranges/googlebot.json
"""


import asyncio
import pathlib
import time
import urllib.parse
from typing import Callable, Iterable
from warnings import warn

from bs4 import BeautifulSoup
import httpx


class UrlFilterer:
    def __init__(
        self, 
        is_allowed_domain: Callable[[str], bool],
        is_allowed_scheme: Callable[[str], bool], 
        is_allowed_file_type: Callable[[str], bool],
    ) -> None:
        """Creates a UrlFilterer instance which is used by the crawler to check
        if a link should be accessed.

        Args:
            is_allowed_domain (Callable[[str], bool]): Checks if the domain of
                the url is fine to be searched.
            is_allowed_scheme (Callable[[str], bool]): Checks if the scheme of
                the url is fine to be searched.
            is_allowed_file_type (Callable[[str], bool]): Checks if the file
                type of the url is fine to be searched.
        """
        self.is_allowed_domain = is_allowed_domain
        self.is_allowed_scheme = is_allowed_scheme
        self.is_allowed_file_type = is_allowed_file_type
    
    def check_url(self, base: str, path: str) -> str | None:
        """_summary_

        Args:
            base (str): A url that is being searched
            path (str): A relative path which was referenced from on the url
                being searched

        Returns:
            str | None: The url or None if the url should not be searched
        """
        url = urllib.parse.urljoin(base, path)
        url, _frag = urllib.parse.urldefrag(url)
        parsed = urllib.parse.urlparse(url)
        ending = pathlib.Path(parsed.path).suffix
        if (self.is_allowed_domain(parsed.netloc) 
            and self.is_allowed_scheme(parsed.scheme) 
            and self.is_allowed_file_type(ending)):
            return url


class Crawler:
    """
    Resp worker: sends a get request to the server linked with the url; turns the response over to the parser
    Parser: parse the html received by the resp worker to identify urls that need to be crawled (add to parser queue)/potentially has info to be downloaded (add to downloads queue)
    Downloader: downloads info from the downloads queue 
    """

    def __init__(self, client: httpx.AsyncClient, urls: Iterable[str], filter: UrlFilterer, workers: int, max_depth: int, max_sites: int) -> None:
        self.client = client
        self.initial_urls = set(urls)
        self.crawling = asyncio.Queue()
        self.to_crawl = set()
        self.seen = set()
        self.selected = set()  # TODO: add an additional filter for URLs to select and go through further processing
        self.filter = filter
        self.workers = workers
        self.max_depth = max_depth
        self.max_sites = max_sites
        
        self.total = 0
    
    async def run(self) -> None:
        [await self.crawling.put(url) for url in self.initial_urls]
        self.total += len(self.initial_urls)
        
        for depth in range(self.max_depth):
            start_time = time.perf_counter()
            start_total = self.total
            workers = [
                asyncio.create_task(self.worker())
                for _ in range(self.workers)
            ]

            await self.crawling.join()

            [worker.cancel() for worker in workers]

            time_used = time.perf_counter() - start_time
            num_parsed = self.total - start_total

            print(f"Depth {depth + 1} finished in {time_used:.3f} sec after parsing " +
                  f"{num_parsed} website{'' if num_parsed == 1 else 's'}")

            [await self.crawling.put(url) for url in self.to_crawl]
            self.to_crawl = set()
    
    async def worker(self) -> None:
        while True:
            try:
                await self.process_one()
            except asyncio.CancelledError:
                return

    async def process_one(self) -> None:
        url = await self.crawling.get()
        try:
            await self.crawl(url)
        except Exception as e:
            print(f"There was an error in processing the request: {e}")
            # TODO: add retry handling here
        finally:
            self.crawling.task_done()

    async def crawl(self, url: str) -> None:
        await asyncio.sleep(1)
        resp = await self.client.get(url, follow_redirects=True)
    
        soup = BeautifulSoup(resp, features="html.parser")
        
        for tag in soup.select("a"):
            link = self.filter.check_url(str(resp.url), tag.attrs["href"])
            if link is None or link in self.seen: continue
            await self.add_url(link)
    
    async def add_url(self, url: str) -> None:
        self.seen.add(url)
        if self.total >= self.max_sites and self.max_sites != -1: 
            warn("Max sites reached")  # TODO: find a better solution here
            return
        self.total += 1
        self.to_crawl.add(url)


async def main():
    """Run the crawler
    useful testing website: https://crawler-test.com/
    """
    start_time = time.perf_counter()
    filterer = UrlFilterer(
        lambda x: x in ["crawler-test.com"],
        lambda x: x in ["http", "https"],
        lambda x: x in ["html", "php", ""]
    )
    async with httpx.AsyncClient() as client:
        crawler = Crawler(
            client, 
            urls=["https://crawler-test.com/"],
            filter=filterer,
            workers=10,
            max_depth=3,
            max_sites=-1
        )
        await crawler.run()
    end_time = time.perf_counter()
    
    seen = sorted(crawler.seen)
    print("Results:")
    for url in seen: 
        print(url)
    print(f"Selected: {len(crawler.selected)} URLs")
    print(f"Found: {len(seen)} URLs")
    print(f"Done in {end_time - start_time:.3f}s")


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
