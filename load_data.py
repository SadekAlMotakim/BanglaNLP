"""Load the BanglaNLP news corpus (CorpusData.Json) as a pandas DataFrame.

Usage:
    python load_data.py                     # summary of the full corpus
    python load_data.py --five-class --dedup  # the paper's 5-class subset, duplicates removed
"""

import argparse
import json

import pandas as pd

FIVE_CLASSES = ["technology", "economy", "entertainment", "international", "sports"]


def load_corpus(path="CorpusData.Json", five_class=False, dedup=True):
    """Return a DataFrame with columns `article` and `category`.

    five_class: keep only the five categories used in the ICBSLP 2018 paper.
    dedup: drop empty articles and exact-duplicate texts (keeps the first occurrence).
    """
    with open(path, encoding="utf-8-sig") as f:
        df = pd.DataFrame(json.load(f))

    df["article"] = df["article"].fillna("").str.strip()
    if five_class:
        df = df[df["category"].isin(FIVE_CLASSES)]
    if dedup:
        df = df[df["article"] != ""].drop_duplicates(subset="article")
    return df.reset_index(drop=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--path", default="CorpusData.Json")
    p.add_argument("--five-class", action="store_true")
    p.add_argument("--dedup", action="store_true")
    a = p.parse_args()

    df = load_corpus(a.path, five_class=a.five_class, dedup=a.dedup)
    print(f"{len(df)} articles")
    print(df["category"].value_counts().to_string())
