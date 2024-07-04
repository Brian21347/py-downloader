"""
This module contains unit tests for the `crawler.py` and `downloader.py` modules.
Run this module by running the following command in the `py-downloader` directory:
`py -m unittest test.test_download`

This module tests downloading from a remote source without connecting to the 
internet by creating a local http server in the `py-downloader` directory.
The server starts on local host on a random port in the range [1000, 10000]. 
If this program hangs when running it in the terminal and it is not closing 
itself after ^C; kill it using task manager or through `kill -9 <PID>`.
"""


from os import makedirs, remove, rmdir
from os.path import isfile, join
from http.server import  SimpleHTTPRequestHandler
from socketserver import TCPServer
from threading import Thread
from random import randint
import unittest

from src.file_downloader import download
from src.crawler import crawl


class TestDownload(unittest.TestCase):
    def test_download(self):
        PORT = randint(1_000, 10_000)

        def testing_func(httpd: TCPServer):
            url = f"http://localhost:{PORT}/test/websites/testing_website.html"

            path = join("test", "test_downloads")
            file_name = None
            override = "Edit name"

            to_download, *args = crawl(url, depth=1, css_selector="img", max_sites=-1, allow_duplicate_to_download_links=True)


            for url in to_download:
                download(url, path, file_name, override, verbose=True)
        
            download_path = join("test", "test_downloads", "wikipedia.png")

            with open(download_path, mode="rb") as f:
                downloaded_file = f.read()
            with open(join("test", "wikipedia.png"), mode='rb') as f:
                correct_file = f.read()
            count = 0
            print("Removing downloaded files...")
            if isfile(download_path):
                remove(download_path)
                count += 1
            for i in range(1, 6):
                override_path = join("test", "test_downloads", f"wikipedia ({i}).png")
                if isfile(override_path):
                    remove(override_path)
                    count += 1
            httpd.shutdown()

            self.assertEqual(downloaded_file, correct_file)
            self.assertEqual(count, 6)
            self.assertEqual(len(to_download), 6)
            self.assertEqual(args, [1, 6, 6])

        print("Creating directory to download files...")
        makedirs(join("test", "test_downloads"), exist_ok=True)
        
        addr = ("", PORT)
        with TCPServer(addr, SimpleHTTPRequestHandler) as httpd:
            server_thread = Thread(target=httpd.serve_forever)
            tests_thread = Thread(target=testing_func, args=([httpd]))

            server_thread.start()
            tests_thread.start()

            tests_thread.join()
            server_thread.join()
        print("Removing created directory...")
        rmdir(join("test", "test_downloads"))
        print("Finished!")
        print("=" * 15)
    
    def test_crawl(self):
        PORT = randint(1_000, 10_000)

        def testing_func(httpd: TCPServer):
            url = f"http://localhost:{PORT}/test/websites/testing_website.html"

            to_download, *args = crawl(url, depth=3, css_selector="img", max_sites=-1, allow_duplicate_to_download_links=False, verbose=True)

            httpd.shutdown()

            self.assertEqual(args, [6, 0, 1])
            self.assertEqual(len(to_download), 1)
            print("Finished")
            print("=" * 15)


        addr = ("", PORT)
        with TCPServer(addr, SimpleHTTPRequestHandler) as httpd:
            server_thread = Thread(target=httpd.serve_forever)
            tests_thread = Thread(target=testing_func, args=([httpd]))

            server_thread.start()
            tests_thread.start()

            tests_thread.join()
            server_thread.join()


if __name__ == "__main__":
    unittest.main()
