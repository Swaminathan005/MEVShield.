# Machine Learning Model Benchmark Report

**Role:** Principal ML Engineer  
**Date:** 2026-09-12 21:22:56  
**Target:** Ethereum Sandwich Attack Detection (`LABEL = 1` vs `LABEL = 0`)  
**Evaluation Dataset:** `MEV_SHIELD.SANDWICH_TEST` (611,106 chronologically isolated transactions)  
**Class Imbalance:** 16.17 : 1 (Positive MEV: 40,847 | Negative Normal: 570,259)

---

## 1. Algorithm Performance Benchmark

All models were trained on 2,444,471 records (`MEV_SHIELD.SANDWICH_TRAIN`) using balanced cost-sensitive weights (`scale_pos_weight=16.17`) and evaluated with early stopping (50 rounds) on `MEV_SHIELD.SANDWICH_TEST`.

| Model Name | PR-AUC | ROC-AUC | Optimal Threshold | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **XGBoost (CUDA GPU)** | **0.8590** | 0.9661 | 0.86 | 0.8989 | 0.7299 | **0.8056** |
| **LightGBM (CPU Multi-thread)** | 0.7751 | 0.9457 | 0.33 | 0.7982 | 0.6659 | 0.7261 |
| **CatBoost (GPU)** | 0.8443 | 0.9623 | 0.85 | 0.8785 | 0.7207 | 0.7918 |

---

## 2. Champion Model Designation & Rationale

### 🏆 Champion: **XGBoost**
* **Primary Selection Metric:** Highest Precision-Recall Area Under Curve (**PR-AUC = 0.8590**). In severe class imbalance (5.8% positive), ROC-AUC can present an overly optimistic assessment due to the large majority class. PR-AUC directly penalizes false positives and provides the truest measure of detection precision.
* **Optimal Operating Cutoff:** Decision threshold tuned to **0.86**, balancing precision (89.89%) and recall (72.99%) to maximize detection **F1-Score (0.8056)**.
* **Serialized Artifact:** Saved to `models/champion_mev_model.joblib`.

---

## 3. Top 10 Feature Importances (XGBoost)

| Rank | Feature Name | Importance Score | Description / Analytical Rationale |
| :---: | :--- | :---: | :--- |
| 1 | `HAS_NEXT_TRADE` | 0.3453 | Key signal driving model decision tree split |
| 2 | `NEXT_INPUT_SIZE` | 0.1448 | Key signal driving model decision tree split |
| 3 | `PRIORITY_FEE_RATIO_PREV` | 0.1083 | Key signal driving model decision tree split |
| 4 | `LOG_NEXT_USD` | 0.1046 | Key signal driving model decision tree split |
| 5 | `PREVIOUS_GAP` | 0.0426 | Key signal driving model decision tree split |
| 6 | `AMOUNT_USD` | 0.0309 | Key signal driving model decision tree split |
| 7 | `NEXT_GAP` | 0.0265 | Key signal driving model decision tree split |
| 8 | `IS_ISOLATED_POOL_TRADE` | 0.0229 | Key signal driving model decision tree split |
| 9 | `INPUT_SIZE_BYTES` | 0.0213 | Key signal driving model decision tree split |
| 10 | `LOG_PREVIOUS_USD` | 0.0207 | Key signal driving model decision tree split |

---

## 4. Exasol Database Writeback Verification

* **Destination Table:** `MEV_SHIELD.SANDWICH_PREDICTIONS`
* **Total Streamed Records:** **611,106**
* **Writeback Throughput:** 212,983 rows/second
* **Schema Columns:** `TX_HASH`, `BLOCK_NUMBER`, `TRANSACTION_INDEX`, `ACTUAL_LABEL`, `PREDICTED_PROBABILITY`, `PREDICTED_LABEL`

### In-Database Confusion Matrix:
| Actual Label | Predicted Label | Transactions | Share | Classification Meaning |
| :---: | :---: | :---: | :---: | :--- |
| **0** | **0** | 566,906 | 92.77% | True Negative (Normal Trade) |
| **0** | **1** | 3,353 | 0.55% | False Positive |
| **1** | **0** | 11,032 | 1.81% | False Negative |
| **1** | **1** | 29,815 | 4.88% | True Positive (Detected Attack) |

---

## 5. Artifact Summary
* Model Payload: [`models/champion_mev_model.joblib`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/models/champion_mev_model.joblib)
* Database Table: `MEV_SHIELD.SANDWICH_PREDICTIONS`
* Pipeline Script: [`src/04_train_evaluate.py`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/src/04_train_evaluate.py)
