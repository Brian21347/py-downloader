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


import unittest
from src.downloader import download
from src.crawler import crawl
import os
from http.server import  SimpleHTTPRequestHandler
from socketserver import TCPServer
from threading import Thread
from random import randint


class TestDownload(unittest.TestCase):
    def test_download(self):
        PORT = randint(1_000, 10_000)


        def testing_func(httpd: TCPServer):
            url = f"http://localhost:{PORT}/test/websites/testing_website.html"

            path = "test/test_downloads"
            file_name = None
            override = "Edit name"

            to_download, *args = crawl(url, depth=1, css_selector="img", max_sites=-1, allow_duplicate_to_download_links=True)


            for url in to_download:
                download(url, path, file_name, override, verbose=True)
        
            with open("test/test_downloads/wikipedia.png", mode="rb") as f:
                downloaded_file = f.read()
            with open("test/wikipedia.png", mode='rb') as f:
                correct_file = f.read()
            count = 0
            print("Removing downloaded files...")
            if os.path.isfile("test/test_downloads/wikipedia.png"):
                os.remove("test/test_downloads/wikipedia.png")
                count += 1
            for i in range(1, 6):
                if os.path.isfile(f"test/test_downloads/wikipedia ({i}).png"):
                    os.remove(f"test/test_downloads/wikipedia ({i}).png")
                    count += 1
            httpd.shutdown()

            self.assertEqual(downloaded_file, correct_file)
            self.assertEqual(count, 6)
            self.assertEqual(len(to_download), 6)
            self.assertEqual(args, [1, 6, 6])

        print("Creating directory to download files...")
        os.makedirs("test/test_downloads", exist_ok=True)
        
        addr = ("", PORT)
        with TCPServer(addr, SimpleHTTPRequestHandler) as httpd:
            server_thread = Thread(target=httpd.serve_forever)
            tests_thread = Thread(target=testing_func, args=([httpd]))

            server_thread.start()
            tests_thread.start()

            tests_thread.join()
            server_thread.join()
        print("Removing created directory...")
        os.rmdir("test/test_downloads")
        print("Finished!")


if __name__ == "__main__":
    unittest.main()
