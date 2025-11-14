# 📊 Earning Call Transcript Analysis

**Project:** Sentiment Analysis of Executive Presentations  
**Dataset:** First 100 companies, 2024 earning call transcripts  
**Status:** ✅ Data Preparation Complete

---

## 🎯 Goal

Analyze sentiment in earning call presentations using GPT to label text as positive/negative/neutral with probabilities.

---

## ✅ Completed Work

### Phase 1: Data Exploration
- Built Streamlit viewer to inspect 102,380 rows across 100 companies
- Discovered 32.7% duplication rate in raw data
- Found events recorded up to 7 times with different transcript IDs

### Phase 2: Data Cleaning
- 3-stage deduplication pipeline
- Merged duplicate transcript versions
- Verified cleaning quality (98.95% uniqueness achieved)



---

## 📊 Cleaning Results

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| **Rows** | 102,380 | 69,625 | -32,755 (-32.0%) |
| **Text Volume** | 15.3M words | 12.3M words | **-3.0M words (-19.4%)** |
| **Unique Texts** | 68,893 | 68,893 | **0 (0%)** ✅ |
| **Transcript Versions** | 2,190 | 892 | -1,298 (-59.3%) |

### What We Removed
- **32,755 duplicate rows** (32% of data)
- **~3 million duplicate words** (19.4% of text volume)
- **909 redundant transcript versions** merged into single events
- **100% of unique information preserved** (zero content loss)

### Final Dataset
- 69,625 clean rows
- 68,893 unique component texts
- 98.95% uniqueness rate
- 6,889 Executive Presenter Speech components (analysis target)
- Ready for GPT sentiment analysis

---

## 📁 Files

**Data:**
- `transcripts_cleaned.pkl` - Clean dataset (69,625 rows, 12.3M words)
- `transcripts_first100.pkl` - Raw data (102,380 rows)

**Scripts:**
- `data_viewer.py` - Streamlit viewer
- `clean_data.py` - Deduplication pipeline
- `filter_data.py` - Extract first 100 companies

---

## 🚀 Usage

```bash
# View data
streamlit run data_viewer.py

# Run cleaning
python3 clean_data.py
```

```python
# Load cleaned data
import pickle
with open('transcripts_cleaned.pkl', 'rb') as f:
    df = pickle.load(f)
```

---

## 🎯 Next Steps

**Pending from client:**
1. Content filtering criteria (what to keep/remove from texts)
2. Sentiment scope (per component vs per company)
3. Token cap per API call (suggest: 8,000-16,000)
4. Time segmentation approach (past/present/future)

**Ready to implement:**
- GPT sentiment analysis pipeline
- Cost estimation
- Final analysis report

---

**Status:** ✅ Data cleaned. 32% reduction, 0% information loss. Ready for analysis.
