"""Download the MovieLens "ml-latest-small" dataset (about 100,000 ratings) from GroupLens.

Run from the project root:  python data/download_movielens.py
"""
import io
import urllib.request
import zipfile
from pathlib import Path

URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
DEST = Path(__file__).resolve().parent

if __name__ == "__main__":
    print(f"Downloading {URL} ...")
    with urllib.request.urlopen(URL) as response:
        data = response.read()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(DEST)
    print(f"Done. Files are in {DEST / 'ml-latest-small'}")
    print("Dataset by GroupLens Research (grouplens.org). See its README for license and citation terms.")
