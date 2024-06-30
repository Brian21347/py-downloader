"""
This module downloads files.
"""


import os
import warnings
import requests


BLOCK_SIZE = 2 ** 15


def download(url: str, path: str, file_name: str = None, override: bool = False) -> bool:
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

    if override and os.path.isfile(full_path):
        warnings.warn(f"Overriding a file at the following path: \"{path}\"")
    
    replace_num = 1
    original_full_path = full_path[:]
    i = original_full_path.rfind(".")
    while os.path.isfile(full_path) and not override:
        if i == -1: raise ValueError("No File extension")
        full_path = f"{original_full_path[:i]} ({replace_num}){original_full_path[i:]}"
        replace_num += 1
        if replace_num >= 1024: raise ValueError("Too many replacements")

    with open(full_path, 'wb') as handle:
        for block in response.iter_content(BLOCK_SIZE):
            if not block: break
            handle.write(block)
    return True
