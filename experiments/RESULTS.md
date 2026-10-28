# Revisiting Bangla Content Categorization: clean-split baselines

Code: `revisit.py`. Data: `CorpusData.Json` from this repository. Seed: 42.

## 1. Data cleaning

| Step | Articles removed |
|---|---:|
| Empty articles | 1 |
| Same text under conflicting labels | 3 texts |
| Exact duplicates | 1,377 |
| Near-duplicates (TF-IDF cosine ≥ 0.90) | 126 |
| **Clean corpus** | **18,320** of 19,838 |

Splits are stratified 70/10/20 (train/dev/test). They are saved as row indices into `CorpusData.Json` in `results/split_5class.csv` and `results/split_17class.csv`.

- **5-class task** (the paper's categories): 5,842 articles; 4,089 train / 584 dev / 1,169 test.
- **17-class task**: every section with at least 50 clean articles: 18,303 articles; 12,812 / 1,830 / 3,661. Two tiny sections are excluded: protichinta (16) and kishoralo (1).

## 2. Baselines (test set)

| Model | 5-class Acc | 5-class Macro-F1 | 17-class Acc | 17-class Macro-F1 |
|---|---:|---:|---:|---:|
| TF-IDF words + Logistic Regression (paper-style) | 96.75 | 95.70 | 90.19 | 73.25 |
| TF-IDF word 1–2-grams + Linear SVM | 96.83 | 95.73 | 90.00 | 71.68 |
| TF-IDF char 2–5-grams + Linear SVM | **97.18** | **96.04** | **91.18** | **75.33** |

Dev-set scores are in `results/results.csv`, and per-class reports are in `results/per_class_reports.txt`.

## 3. Leakage check (paper-style 5-fold CV, Logistic Regression)

| Data | Articles | Accuracy | Macro-F1 |
|---|---:|---:|---:|
| Raw 5-class (duplicates kept) | 6,354 | 97.86 | 96.90 |
| Cleaned 5-class | 5,842 | 97.42 | 96.31 |

Duplicates inflated cross-validation scores by only about 0.5 points. The 2018 result of 97.3% holds up on clean data.

## Findings

1. **The original 5-class result is reproducible.** On a clean, held-out test set, the paper's approach scores 96.8% accuracy (95.7 macro-F1), close to the reported 97.3%.
2. **The 5-class task is saturated.** Simple TF-IDF models are near the ceiling, so modern models have little room to show gains there.
3. **The full 17-class task is where the research room is.** Accuracy stays around 90–91%, but macro-F1 falls to 72–75 because small and overlapping sections are hard. The best model's per-class F1:
   - pachmisheli: 0.13
   - we-are: 0.13
   - education: 0.39
   - art-and-literature: 0.56
4. **Character n-grams beat word features on both tasks**, without any stemmer. This is consistent with Bangla's rich morphology.

## Next steps

- Fine-tune a Bangla BERT-style model and test multilingual LLMs on the same 17-class split, comparing macro-F1 and the weak classes above.
- Collect a 2026 test set from the same sections to measure temporal drift.
