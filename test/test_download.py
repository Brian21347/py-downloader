"""
This module contains unit tests for the `download.py` module.
"""


import unittest
from src.download import download
import os


class TestDownload(unittest.TestCase):
    def test_download(self):
        url = "https://en.wikipedia.org/static/images/icons/wikipedia.png"
        download(url, "test", file_name="TestDownload")
        self.assertTrue(os.path.isfile("test/TestDownload.png"))

        with open("test/TestDownload.png", mode="rb") as f:
            downloaded_file = f.read()
        with open("test/wikipedia.png", mode='rb') as f:
            correct_file = f.read()
        self.assertEqual(downloaded_file, correct_file)


if __name__ == "__main__":
    unittest.main()
