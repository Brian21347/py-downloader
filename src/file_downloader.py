"""
This module downloads files.
"""


import os
import warnings
import requests
from typing import Literal
from tqdm import tqdm


BLOCK_SIZE = 2 ** 15  # TODO: make this a dynamic value to maximize the speed of the download



def check_override(full_path: str, override: Literal["Edit name", "Skip", "Strict", "Write over"], verbose: bool = False) -> None | str:
    """
    Checks if there will be a collision and changes where the file will be downloaded, if necessary.

    params:
        full_path: The path where the file will be downloaded.
        override: The setting that is used.

    raises: 
        FileExistsError: If there is a pre-existing file and override is set to `Strict`
        ValueError: If the path does not have an extension
    
    returns:
        The location where the file will be downloaded or None if it should not be downloaded.
    """
    file_exists = os.path.isfile(full_path)
    if not file_exists: 
        if verbose: print(f"A file does not exist at {full_path}; downloading to that location.")
        return full_path
    if override == "Skip": 
        if verbose: print(f"A file exists at {full_path}, skipping the download.")
        return None
    if override == "Strict": raise FileExistsError(f"A file exists at {full_path}.")
    if override == "Write over":
        warnings.warn(f"Overriding a file at the following path: \"{full_path}\".")
        return full_path
    replace_num = 1
    original_full_path = full_path[:]
    i = original_full_path.rfind(".")
    while os.path.isfile(full_path) and override == "Edit name":
        if i == -1: raise ValueError("No File extension")
        full_path = f"{original_full_path[:i]} ({replace_num}){original_full_path[i:]}"
        replace_num += 1
    if verbose: print(f"A file exists at {original_full_path}; writing to {full_path}.")
    return full_path


def download(
        url: str, 
        path: str, 
        file_name: str = None, 
        override: Literal["Edit name", "Skip", "Strict", "Write over"] = "Edit name",  # TODO: add "Skip if same" which will check that the file being downloaded and the pre-existing file have the same file sizes
        verbose: bool = False
    ) -> bool:
    """
    Downloads a file from a remote source to a specified location using html packets.

    params:
        url: The remote source which the file will be downloaded from.
        path: The location of the directory which is used to store the downloaded file.
        file_name: The file name of the downloaded file; if left empty, will be set to the file name in the url. A file extension will be added to the end to match the file type of the downloaded file.
        override: Settings regarding what to do if the downloaded file matches the name of a pre-existing file in the download directory.
            `Edit name`: Change the name of the downloaded file by adding a number at the end (chooses the first one that prevents an overlap) such that it will not match the name of the pre-existing file(s).
            `Skip`: Do not download the file and do not throw an error.
            `Strict`: Do not download the file and throw an error.
            `Write over`: Write over the pre-existing file.
        verbose: If set to true, the function will produce more detailed output
    
    raises:
        FileExistsError: If there is a pre-existing file and override is set to `Strict`.
        ValueError: If the file extension could not be retrieved.
            
    returns:
        True if the file is successfully downloaded or has been skipped.
    """
    if verbose: print(f"Getting response from \"{url}\"...")
    response = requests.get(url, stream=True)
    if verbose: print(f"Response headers: {response.headers}")

    if not response.ok:
        warnings.warn(f"Response was not ok: \"{response}\"")
        return False

    if file_name is not None:
        if verbose: print("No file name specified, using the filename of the file on the website's side.")
        file_type = ""
        i = url.rfind(".")
        if i == -1:
            warnings.warn(f"File type not found from url, using \"content-type\" from the html response.")
            file_type = response.headers.get("content-type")
            file_type = "." + file_type[file_type.rfind("/") + 1:]
        else:
            file_type = url[i:]
        file_name += file_type
        if verbose: print(f"Using the file name: \"{file_name}\"")
    else:
        if verbose: print("Finding the name of the file...")
        file_name = url[url.rfind("/") + 1:]
        if verbose: print(f"Found \"{file_name}\".")
    
    full_path = os.path.join(path, file_name)
    if verbose: print(f"The full path of where the file will be downloaded is {full_path}...")

    ret = check_override(full_path, override, verbose=verbose)
    if ret is None: return True  # skipped
    full_path = ret

    if verbose: print(f"Downloading...")

    with open(full_path, 'wb') as file:
        for block in response.iter_content(BLOCK_SIZE):
            if not block: break
            file.write(block)
    return True
