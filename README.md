# BanglaNLP: Bangla News Corpus and Content Categorization

Data, tools and code for the paper **"Bangla Content Categorization Using Text Based Supervised Learning Methods"** (ICBSLP 2018, IEEE).

This repository contains:

- a corpus of **19,838 Bangla news articles** labelled by news section, collected from Prothom Alo in 2017,
- the TF-IDF feature matrix used in the paper's experiments,
- the C# tools used to collect the corpus (a corpus-builder web API and a desktop extraction tool).

## Quick start

```bash
git clone https://github.com/SadekAlMotakim/BanglaNLP.git
cd BanglaNLP
unzip CorpusData.zip
python load_data.py --five-class --dedup
```

```python
from load_data import load_corpus

df = load_corpus("CorpusData.Json", five_class=True, dedup=True)
print(df["category"].value_counts())
```

## Dataset

### `CorpusData.zip` → `CorpusData.Json` (raw corpus)

A JSON array of objects (UTF-8 with BOM):

```json
[
  { "article": "<full article text in Bangla>", "category": "international" }
]
```

| Property | Value |
|---|---|
| Articles | 19,838 |
| Categories | 19 news sections |
| Median length | ~1,760 characters |
| Source period | July–September 2017 |

Category counts:

| Category | Articles | Category | Articles |
|---|---:|---|---:|
| bangladesh | 9,379 | technology | 483 |
| sports | 2,000 | trust | 313 |
| international | 1,599 | roshalo | 156 |
| entertainment | 1,389 | pachmisheli | 144 |
| northamerica | 1,105 | art-and-literature | 117 |
| economy | 883 | education | 97 |
| opinion | 804 | bondhushava | 78 |
| life-style | 647 | we-are | 69 |
| durporobash | 558 | protichinta | 16 |
|  |  | kishoralo | 1 |

**The paper's 5-class subset.** The experiments in the paper use five categories: technology, economy, entertainment, international and sports. In this file those categories have 6,354 rows, of which 494 are exact duplicates. After removing them, 5,860 articles remain: sports 1,860, international 1,390, entertainment 1,287, economy 864 and technology 459. This matches the paper's 5,870 within 10 articles.

> **Note on duplicates:** about 7% of all articles (1,388) are exact duplicates. Deduplicate before splitting into train and test sets, otherwise duplicates can appear in both and inflate scores. `load_data.py --dedup` does this.

### `sample-TFIDF-Dataset-for-Bangla-Content-Categorization.zip` (features)

The pre-computed TF-IDF matrix used in the paper (about 660 MB uncompressed CSV). The columns are `articleid`, `category`, then one column per stemmed unigram. It reflects the paper's preprocessing: punctuation removal, *bivokti* (suffix) stripping and stop-word removal. For new experiments, the raw corpus is usually the better starting point.

## Tools

| Folder | What it is |
|---|---|
| `Content Repository API/` | ASP.NET Web API that fetches articles by date range and stores them in SQL Server. Includes `Sample API Input.json`. |
| `CorpusBuilder/` | Web front end for the API: pick a date, fetch that day's articles, download them as JSON. |
| `Tool for fetching content by URL/` | Windows desktop tool (`TextExtraction.exe`) that extracts article text from a news URL. |

These tools were written in 2017–2018 against the news site's layout at the time and may need updating to work today. The hosted demo and API from the paper are no longer online.

## Results from the paper

Five-fold cross-validation accuracy on the 5-class subset, using chi-square feature selection (18,644 features):

| Model | Accuracy (%) |
|---|---:|
| Logistic Regression | 97.3 |
| SVM (linear) | 95.8 |
| SVM (RBF) | 95.0 |
| Random Forest | 94.4 |
| Gaussian NB | 91.8 |
| KNN | 48.9 |

## Citation

If you use this dataset or code, please cite:

```bibtex
@inproceedings{mostakim2018bangla,
  title     = {Bangla Content Categorization Using Text Based Supervised Learning Methods},
  author    = {Mostakim, Sadek Al and Ehsan, Faiza and Hasan, Syeda Mahdiea and Islam, Sadia and Shatabda, Swakkhar},
  booktitle = {International Conference on Bangla Speech and Language Processing (ICBSLP)},
  year      = {2018},
  publisher = {IEEE}
}
```

## License

<!-- Choose before publishing: e.g. MIT for code, CC BY 4.0 for the dataset. -->
Code: TBD. Dataset: TBD. The article texts are copyright of their original publisher and are provided for non-commercial research use only.

## Contact

Sadek Al Mostakim · s.a.mostakim@gmail.com
