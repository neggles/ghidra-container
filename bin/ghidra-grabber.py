#!/usr/bin/env python3

import argparse
import shutil
import sys
import tempfile
from os import PathLike
from pathlib import Path
from zipfile import ZipFile

import requests

TEMP_DIR = Path(tempfile.gettempdir())


def get_releases() -> list:
    res = requests.get("https://api.github.com/repos/nationalsecurityagency/ghidra/releases")
    res.raise_for_status()
    releases = sorted(res.json(), key=lambda x: x["created_at"], reverse=True)
    return releases


def list_releases() -> None:
    for release in get_releases():
        vers = release["name"].split(" ")[1]
        print(f"\t{vers}")


def download_file(url: str, outdir: PathLike = TEMP_DIR) -> Path:
    outdir = Path(outdir) if not isinstance(outdir, Path) else outdir
    outfile = outdir.joinpath(Path(url).name)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with outfile.open("wb") as f:
            for chunk in r.iter_content(chunk_size=32768):
                f.write(chunk)
    return outfile


def download_release(version: str = "latest") -> Path:
    releases = get_releases()
    for release in releases:
        if version in release["name"]:
            for release_asset in release["assets"]:
                if version in release_asset["name"]:
                    asset = release_asset
                    url = asset["browser_download_url"]
                    print(f"[+] Found Ghidra {version} on Github @ {url}, downloading...")
                    return download_file(url, TEMP_DIR)
            else:
                print(f"[!] Found Ghidra {version} on Github, but no matching asset! Found:")
                print(f"\t{[x['name'] for x in release['assets']]}")
                raise ValueError(f"Failed to find Ghidra {version} release asset")
    else:
        print(f"[!] Failed to find Ghidra {version} on GitHub! Found:")
        print(f"\t{[x['name'] for x in releases]}")
        raise ValueError(f"Failed to find Ghidra {version} release")


def install_ghidra(zip_file: PathLike, destdir: PathLike) -> None:
    destdir = Path(destdir) if not isinstance(destdir, Path) else destdir
    zip_file = Path(zip_file) if not isinstance(zip_file, Path) else zip_file

    if not zip_file.exists():
        print(f"[!] Failed to find Ghidra zip @ {zip_file}")
        raise FileNotFoundError(f"Failed to find Ghidra zip @ {zip_file}")

    print(f"[+] Unpacking {zip_file} to {TEMP_DIR}...")

    with ZipFile(zip_file, "r") as zip:
        zip.extractall(TEMP_DIR)

    # delete downloaded zip file
    zip_file.unlink()

    ghidra_dir = TEMP_DIR / zip_file.name[: zip_file.name.find("_PUBLIC") + 7]

    print(f"[+] Moving {zip_file} into destination {destdir}...")
    if destdir.exists():
        print(f"[!] Destination {destdir} already exists, removing...")
        try:
            destdir.rmdir()
        except OSError:
            print(f"[!] Failed to remove {destdir}! Is it a non-empty directory?")
            raise
    shutil.move(ghidra_dir.resolve(), destdir.resolve())
    print(f"[+] Ghidra installed to {destdir}!")


parser = argparse.ArgumentParser()
parser.add_argument("-u", "--url", help="Ghidra zip URL. Defaults to latest from Github", type=str)
parser.add_argument("-l", "--list", help="List available releases", action="store_true", default=False)
parser.add_argument("-v", "--version", help="Ghidra version to install. Defaults to latest", type=str)
parser.add_argument("path", help="Path to install in", type=Path, default=Path.cwd().joinpath("ghidra"))

if __name__ == "__main__":
    args = parser.parse_args()

    if args.list:
        list_releases()
        sys.exit(0)

    if args.version:
        print(f"[+] Downloading Ghidra {args.version}...")
        zip_file = download_release(args.version)
    else:
        print("[+] Downloading Ghidra 'latest'...")
        zip_file = download_release()

    if args.path:
        install_path = Path(args.path).resolve()
    else:
        install_path = Path.cwd().joinpath("ghidra")
    print(f"[+] Installing Ghidra to {args.path}...")
    install_ghidra(zip_file, args.path)
