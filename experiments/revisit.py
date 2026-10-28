"""Revisiting 'Bangla Content Categorization' (ICBSLP 2018) on a clean evaluation setup.

Steps:
  1. Clean data: drop empty articles, exact duplicates and near-duplicates
     (TF-IDF cosine >= NEAR_DUP_THRESHOLD), and articles whose text appears under conflicting labels.
  2. Fixed, seeded, stratified train/dev/test split (70/10/20), saved as row indices into CorpusData.Json.
  3. TF-IDF baselines, reporting accuracy, macro-F1 and per-class F1, on
     - the paper's 5-class subset
     - all sections with >= MIN_CLASS_SIZE articles after cleaning
  4. Leakage check: paper-style 5-fold CV on the raw (non-deduplicated) 5-class data vs the clean split.

Usage:  python revisit.py --corpus CorpusData.Json --out results
"""

import argparse
import json
import os

import numpy as np
import pandas as pd
from scipy.sparse.csgraph import connected_components
from scipy.sparse import coo_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC

SEED = 42
NEAR_DUP_THRESHOLD = 0.90
MIN_CLASS_SIZE = 50
FIVE_CLASSES = ["technology", "economy", "entertainment", "international", "sports"]

# Whitespace tokens with Bangla/Latin punctuation stripped (no stemmer, unlike the 2018 paper).
TOKEN_PATTERN = r"[^\s।॥.,;:!?\"'‘’“”()\[\]{}|/\\\-–—]+"


def models():
    return {
        "tfidf_word_LR": make_pipeline(
            TfidfVectorizer(token_pattern=TOKEN_PATTERN, min_df=2, sublinear_tf=True),
            LogisticRegression(C=10, max_iter=2000),
        ),
        "tfidf_word12_LinearSVC": make_pipeline(
            TfidfVectorizer(token_pattern=TOKEN_PATTERN, ngram_range=(1, 2), min_df=2, sublinear_tf=True),
            LinearSVC(C=0.5),
        ),
        "tfidf_char2-5_LinearSVC": make_pipeline(
            TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3, sublinear_tf=True, max_features=400_000),
            LinearSVC(C=0.5),
        ),
    }


def load(path):
    with open(path, encoding="utf-8-sig") as f:
        df = pd.DataFrame(json.load(f))
    df["article"] = df["article"].fillna("").str.strip()
    df["row_id"] = np.arange(len(df))  # index into the original JSON array
    return df


def near_duplicate_groups(texts, threshold, chunk=2000):
    """Connected components of the graph 'cosine(TF-IDF) >= threshold'."""
    X = TfidfVectorizer(token_pattern=TOKEN_PATTERN, ngram_range=(1, 2), min_df=1, sublinear_tf=True).fit_transform(texts)
    rows, cols = [], []
    for s in range(0, X.shape[0], chunk):
        S = (X[s:s + chunk] @ X.T).tocoo()
        m = (S.data >= threshold) & (S.row + s != S.col)
        rows.append(S.row[m] + s)
        cols.append(S.col[m])
    rows, cols = np.concatenate(rows), np.concatenate(cols)
    n = X.shape[0]
    G = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    return connected_components(G, directed=False)[1]


def clean(df, log):
    n0 = len(df)
    df = df[df["article"] != ""]
    log["empty_removed"] = n0 - len(df)

    conflicting = df.groupby("article")["category"].nunique()
    conflicting = set(conflicting[conflicting > 1].index)
    df = df[~df["article"].isin(conflicting)]
    log["conflicting_label_texts_removed"] = len(conflicting)

    n1 = len(df)
    df = df.drop_duplicates(subset="article")
    log["exact_duplicates_removed"] = n1 - len(df)

    df = df.reset_index(drop=True)
    groups = near_duplicate_groups(df["article"].tolist(), NEAR_DUP_THRESHOLD)
    df["dup_group"] = groups
    n2 = len(df)
    # Drop groups whose members disagree on the label, keep one article from each remaining group.
    mixed = df.groupby("dup_group")["category"].nunique()
    df = df[~df["dup_group"].isin(mixed[mixed > 1].index)]
    df = df.drop_duplicates(subset="dup_group")
    log["near_duplicates_removed"] = n2 - len(df)
    log["clean_articles"] = len(df)
    return df.drop(columns="dup_group").reset_index(drop=True)


def split(df):
    train, rest = train_test_split(df, test_size=0.30, stratify=df["category"], random_state=SEED)
    dev, test = train_test_split(rest, test_size=2 / 3, stratify=rest["category"], random_state=SEED)
    return train, dev, test


def evaluate(name, df, out):
    train, dev, test = split(df)
    pd.concat([
        train.assign(split="train"), dev.assign(split="dev"), test.assign(split="test")
    ])[["row_id", "category", "split"]].sort_values("row_id").to_csv(f"{out}/split_{name}.csv", index=False)

    rows, reports = [], {}
    for mname, model in models().items():
        model.fit(train["article"], train["category"])
        for sname, part in (("dev", dev), ("test", test)):
            pred = model.predict(part["article"])
            rows.append({
                "task": name, "model": mname, "split": sname,
                "accuracy": round(100 * accuracy_score(part["category"], pred), 2),
                "macro_f1": round(100 * f1_score(part["category"], pred, average="macro"), 2),
            })
            if sname == "test":
                reports[mname] = classification_report(part["category"], pred, digits=3)
        print(rows[-1])
    sizes = {"train": len(train), "dev": len(dev), "test": len(test)}
    return rows, reports, sizes


def leakage_check(raw, clean5):
    """Paper-style 5-fold CV with the paper's best model: raw data (duplicates kept) vs cleaned data."""
    raw5 = raw[raw["category"].isin(FIVE_CLASSES) & (raw["article"] != "")]
    out = {}
    for label, d in (("raw_with_duplicates", raw5), ("cleaned", clean5)):
        skf = StratifiedKFold(5, shuffle=True, random_state=SEED)
        pred = cross_val_predict(models()["tfidf_word_LR"], d["article"], d["category"], cv=skf)
        out[label] = {
            "n": len(d),
            "accuracy": round(100 * accuracy_score(d["category"], pred), 2),
            "macro_f1": round(100 * f1_score(d["category"], pred, average="macro"), 2),
        }
        print("leakage", label, out[label])
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", default="CorpusData.Json")
    p.add_argument("--out", default="results")
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)

    raw = load(a.corpus)
    log = {"raw_articles": len(raw)}
    df = clean(raw, log)
    print(log)

    counts = df["category"].value_counts()
    log["clean_category_counts"] = counts.to_dict()

    five = df[df["category"].isin(FIVE_CLASSES)]
    keep = counts[counts >= MIN_CLASS_SIZE].index
    allc = df[df["category"].isin(keep)]
    log["all_sections_task_classes"] = sorted(keep)

    results, reports = [], {}
    r, rep, sizes5 = evaluate("5class", five, a.out); results += r; reports["5class"] = rep
    r, rep, sizesA = evaluate(f"{len(keep)}class", allc, a.out); results += r; reports[f"{len(keep)}class"] = rep
    log["split_sizes"] = {"5class": sizes5, f"{len(keep)}class": sizesA}
    log["leakage_check_5fold_cv"] = leakage_check(raw, five)

    pd.DataFrame(results).to_csv(f"{a.out}/results.csv", index=False)
    with open(f"{a.out}/data_log.json", "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    with open(f"{a.out}/per_class_reports.txt", "w", encoding="utf-8") as f:
        for task, reps in reports.items():
            for m, txt in reps.items():
                f.write(f"=== {task} | {m} | test ===\n{txt}\n")


if __name__ == "__main__":
    main()
