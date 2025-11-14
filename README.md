# 📊 Earning Call Transcript Analysis - Project Summary

**Project:** Sentiment Analysis of Executive Presentations in Earning Calls  
**Dataset:** First 100 companies from 2024 earning call transcripts  
**Last Updated:** 2024-11-14

---

## 🎯 Project Goal

Analyze sentiment in earning call presentation texts to understand company outlook and tone. The task involves:
1. Cleaning and filtering transcript data
2. Extracting relevant information from presentations
3. Sentiment labeling using GPT (positive/negative/neutral + probabilities)
4. Cost estimation for analysis

---

## ✅ Progress Summary

### Phase 1: Data Inspection & Understanding ✓
**Tool Created:** Interactive Data Viewer (Streamlit app)

**What we built:**
- `data_viewer.py` - Streamlit application to explore raw data
- `filter_data.py` - Script to extract first 100 companies

**Features:**
- Browse all 29 columns in logical order
- View complete transcripts component by component
- Filter by company, speaker type, component type
- Inspect individual rows with detailed field explanations
- Detect and visualize duplicates within transcripts
- Export filtered data to CSV

**Key Findings:**
- **102,380 total rows** (first 100 companies)
- **68,893 unique texts** but duplicated across 102K rows
- **53% duplication rate** in raw data
- Multiple transcript versions for same events (up to 7 versions!)

---

### Phase 2: Data Cleaning & Deduplication ✓
**Tool Created:** Automated Cleaning Pipeline

**What we built:**
- `clean_data.py` - 3-stage deduplication pipeline
- `transcripts_cleaned.pkl` - Clean dataset ready for analysis

**How We Removed Duplicates:**

#### **Stage 1: Within-Transcript Duplicates**
- **Problem:** Same text appeared multiple times in single transcript
- **Example:** Kura Sushi Q4 2024 had 186 components but only 73 unique texts (100% duplication!)
- **Solution:** For each transcript ID, keep only first occurrence of each unique text
- **Removed:** 3,209 rows (3.1%)

#### **Stage 2: Cross-Transcript Duplicates (MERGE)**
- **Problem:** Same event recorded 2-7 times with different transcript IDs
- **Example:** 909 events had multiple versions (655 events with 2 versions, 137 with 3 versions, etc.)
- **Solution:** 
  - Identify events by (company + headline + date)
  - Merge ALL versions together
  - Keep ALL unique texts from all versions combined
  - Remove duplicates after merging
- **Example Impact:** Amgen event had 3 versions (57+57+57 components) → merged into 99 unique components (gained 42 texts!)
- **Removed:** 28,470 rows (27.8%)

#### **Stage 3: Company-Level Final Cleanup**
- **Problem:** Remaining duplicates across different events within same company
- **Solution:** Remove duplicate texts at company level
- **Removed:** 1,076 rows (1.1%)

---

## 📈 Cleaning Results

### Data Reduction
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total Rows | 102,380 | 69,625 | -32,755 (-32.0%) |
| Unique Texts | 68,893 | 68,893 | 0 (0%) ✅ |
| Unique Events | 2,190 transcripts | 917 events | Merged duplicates |
| Companies | 100 | 100 | No change |

### Impact Summary
- ✅ **Removed 32% of data** (32,755 duplicate rows)
- ✅ **Preserved 100% of unique information** (68,893 unique texts)
- ✅ **Zero information loss** - all unique content retained
- ✅ **~32% cost savings** on future GPT API calls
- ✅ **Accurate analysis** - each text counted once

### Content Distribution (Cleaned Data)
- **Executives:** 38,599 components (55.4%)
- **Analysts:** 23,959 components (34.4%)
- **Operator:** 5,626 components (8.1%)
- **Others:** 1,441 components (2.1%)

**Component Types:**
- **Answers:** 34,205 (49.1%)
- **Questions:** 22,905 (32.9%)
- **Presenter Speech:** 6,889 (9.9%) ⭐ *Main analysis target*
- **Operator Messages:** 5,626 (8.1%)

---

## 📁 Project Files

### Data Files
- `transcripts_2024.pkl` - Original raw data (all companies)
- `transcripts_first100.pkl` - Filtered to first 100 companies
- `transcripts_cleaned.pkl` - **Clean dataset ready for analysis** ✅

### Scripts
- `filter_data.py` - Extract first 100 companies from raw data
- `data_viewer.py` - Streamlit app for data exploration
- `clean_data.py` - 3-stage deduplication pipeline

### Documentation
- `README.md` - This file
- `Task_1.pdf` - Original task requirements

---

## 🚀 How to Use

### View the Data
```bash
streamlit run data_viewer.py
```

### Run Data Cleaning
```bash
python3 clean_data.py
```

### Load Cleaned Data
```python
import pickle
import pandas as pd

with open('transcripts_cleaned.pkl', 'rb') as f:
    df = pickle.load(f)

# Now you have clean, deduplicated data ready for analysis
print(f"Total components: {len(df):,}")
print(f"Unique texts: {df['componenttext'].nunique():,}")
```

---

## 📊 Key Dataset Columns

| Column | Description |
|--------|-------------|
| `componenttext` | Full text spoken (MOST CRITICAL for analysis) |
| `word_count` | Number of words (for cost estimation) |
| `companyname` | Company name |
| `speakertypename` | Executives/Analysts/Operator |
| `transcriptcomponenttypename` | Presenter Speech/Answer/Question |
| `transcriptid` | Groups components from same earning call |
| `componentorder` | Order of speech in conversation |
| `mostimportantdateutc` | Date of earning call |

---

## 🎯 Next Steps

**Pending decisions from client:**
1. What information to filter from texts? (greetings vs financial metrics)
2. Sentiment analysis scope? (per component vs aggregated per company)
3. Token cap per API call? (suggested: 8,000-16,000)
4. Time segmentation? (past/present/future vs overall sentiment)

**Once decisions received:**
1. Filter/clean text content for GPT analysis
2. Implement GPT sentiment analysis pipeline
3. Generate sentiment labels + probabilities
4. Calculate cost estimates
5. Produce final analysis report

---

## 📝 Summary

We successfully built a data exploration tool and cleaned 100+ companies' earning call data. Through intelligent deduplication, we reduced the dataset by 32% while preserving 100% of unique information. The cleaned dataset is now ready for sentiment analysis, with significant cost savings and accuracy improvements compared to analyzing the raw duplicated data.

**Status:** ✅ Data preparation complete. Ready for analysis phase.
