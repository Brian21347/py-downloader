import requests


def confirm(to_download: list[str], num_sites_visited: int, min_on_page: int, max_on_page: int) -> bool:
    download_size = 0
    for url in to_download:
        resp = requests.head(url)
        download_size += int(resp.headers.get("Content-Length"))
    
    conversion: dict[int, str] = {
        2 ** 40: "TiB",
        2 ** 30: "GiB",
        2 ** 20: "MiB",
        2 ** 10: "KiB",
    }
    size = download_size
    unit = "Bytes"
    for unit_size, unit_name in conversion.items():
        if download_size < unit_size: continue
        size = download_size / unit_size
        unit = unit_name
        break
    val = "\n\t"
    msg = f'''\
Found {len(to_download)} files to download with a total download size of {size:.3f} {unit} after visiting {num_sites_visited} pages. 
        {val.join(to_download[0:2] + ["..."] + to_download[-2:] if len(to_download) > 5 else to_download)}
The minimum number of elements matching the CSS selector on the visited pages is {min_on_page:,} and the maximum is {max_on_page:,}.
Proceed to download (yes, no, y, n)? '''
    while (resp := input(msg).lower()) not in ["yes", "no", "y", "n"]:
        print("Respond with \"yes\" or \"no\"")
        msg = "Proceed to download (yes, no, y, n)? "
    return True if resp[0] == "y" else False
