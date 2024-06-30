"""
This module downloads files.
"""


import os
import warnings
import requests
from typing import Literal


BLOCK_SIZE = 2 ** 15  # TODO: make this a dynamic value to maximize the speed of the download



def check_override(full_path: str, override: Literal["Edit name", "Skip", "Strict", "Write over"]) -> None | str:
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
    if not file_exists: return full_path
    if override == "Skip": return None
    if override == "Strict": raise FileExistsError
    if override == "Write over":
        warnings.warn(f"Overriding a file at the following path: \"{full_path}\"")
        return full_path
    replace_num = 1
    original_full_path = full_path[:]
    i = original_full_path.rfind(".")
    while os.path.isfile(full_path) and override == "Edit name":
        if i == -1: raise ValueError("No File extension")
        full_path = f"{original_full_path[:i]} ({replace_num}){original_full_path[i:]}"
        replace_num += 1
    return full_path


def download(
        url: str, 
        path: str, 
        file_name: str = None, 
        override: Literal["Edit name", "Skip", "Strict", "Write over"] = "Edit name"
    ) -> bool:
    """
    Downloads a file from a remote source to a specified location using html packets.

    params:
        url: The remote source which the file will be downloaded from.
        path: The location of the directory which is used to store the downloaded file.
        file_name: The file name of the downloaded file; if left empty, will be set to the file name in the url. A file extension will be added to the end to match the file type of the downloaded file.
        override: Settings regarding what to do if the downloaded file matches the name of a pre-existing file in the download directory.
            `Edit name`: Change the name of the downloaded file by adding a number at the end (chooses the first one that prevents an overlap) such that it will not match the name of the pre-existing file.
            `Skip`: Do not download the file and do not throw an error.
            `Strict`: Do not download the file and throw an error.
            `Write over`: Write over the pre-existing file.
    
    raises:
        FileExistsError: If there is a pre-existing file and override is set to `Strict`.
        ValueError: If the file extension could not be retrieved.
            
    returns:
        True if the file is successfully downloaded or has been skipped.
    """
    response = requests.get(url, stream=True)

    if not response.ok:
        warnings.warn(f"Response was not ok: \"{response}\"")
        return False

    if file_name is not None:
        file_type = ""
        i = url.rfind(".")
        if i == -1:
            warnings.warn(f"File type not found from url, using \"content-type\" from the html response.")
            file_type = response.headers.get("content-type")
            file_type = "." + file_type[file_type.rfind("/") + 1:]
        else:
            file_type = url[i:]
        file_name += file_type
    else:
        file_type = url[url.rfind("/") + 1:]
    
    full_path = os.path.join(path, file_name)

    ret = check_override(full_path, override)
    if ret is None: return True  # skipped
    full_path = ret

    with open(full_path, 'wb') as handle:
        for block in response.iter_content(BLOCK_SIZE):
            if not block: break
            handle.write(block)
    return True
