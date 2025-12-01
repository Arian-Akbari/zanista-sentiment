# Zanista Earnings Call Sentiment Analysis

**Client:** Zanista.AI  
**Dataset:** 100 companies, 2024 earnings call transcripts (803 events)  
**Status:** ✅ Complete - Delivered November 2024

---

## Project Summary

Analyzed executive tone during earnings call presentations using GPT-4.1. Classified 803 events by how executives frame results, independent of actual financial performance.

---

## Sentiment Definitions

- **Positive:** Optimistic tone, good financial presentation, beating expectations
- **Negative:** Cautious tone, poor results presentation, challenges/concerns
- **Neutral:** Factual/balanced tone, mixed signals, no clear direction

---

## Data Pipeline

**Raw data:** 102,380 rows (100 companies)
**Cleaned:** 69,625 rows (removed 32% duplicates, 0% information loss)
**Filtered:** Executive presenter speeches only
**Analyzed:** 803 unique earnings call events

### Data Cleaning Process (3-Stage Deduplication)

The raw dataset had a **32.7% duplication rate** with events recorded up to 7 times with different transcript IDs. We used a 3-stage pipeline to clean this:

**Stage 1: Within-Transcript Deduplication**
- Removed duplicate texts within each individual transcript
- Used `drop_duplicates(subset=['transcriptid', 'componenttext'])`
- Kept first occurrence of each unique text
- Result: Removed 3.5% of rows

**Stage 2: Cross-Transcript Merging**
- Identified events with multiple transcript versions (same company, headline, date but different transcript IDs)
- Merged all versions into one by deduplicating on componenttext
- **Unified each event to have a SINGLE transcript ID** (eliminated 909 redundant transcript versions)
- Result: Removed 15.2% of rows, merged 1,298 transcript versions into 892

**Stage 3: Company-Level Cleanup**
- Final deduplication across all events within each company: `(companyid, componenttext)`
- Removed boilerplate/repeated corporate messaging (e.g., same disclaimers or talking points reused across multiple earnings calls)
- Ensures each company's unique content appears only once while keeping first occurrence
- Result: Removed 2,270 rows (3.2% of data)

**Cleaning Results:**

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| **Total Rows** | 102,380 | 69,625 | -32,755 (-32.0%) |
| **Word Volume** | 15.3M | 12.3M | -3.0M (-19.4%) |
| **Unique Texts** | 68,893 | 68,893 | 0 (0%) ✅ |
| **Transcript Versions** | 2,190 | 892 | -1,298 (-59.3%) |

**Key Achievement:** 32% data reduction with **0% information loss** - all unique content preserved!

---

## Results

**Model:** GPT-4.1 (validated at 85% accuracy)  
**Processing:** 803 events in 2.6 minutes (5.2 events/sec)  
**Success rate:** 100% (0 failures)

**Sentiment Distribution:**

- Positive: 469 (58.4%)
- Neutral: 267 (33.3%)
- Negative: 67 (8.3%)

**Cost:** $19.79 total ($0.025 per event)

**Deliverable:** `data/results/sentiment_results.pkl` (803 events with sentiment labels, probabilities, reasoning, and cost tracking)

---

## Complete Analysis Pipeline

### Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure Azure OpenAI (create .env file)
# AZURE_OPENAI_API_KEY=your-key
# AZURE_OPENAI_ENDPOINT=your-endpoint
# AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

### Run Full Pipeline (Automated)

```bash
# Execute entire pipeline: filter → clean → aggregate → sentiment
bash run_pipeline.sh
```

### Run Individual Steps (Manual)

**Step 1: Filter to First 100 Companies**

```bash
python data_processing/01_filter_companies.py
# Output: v2_transcripts_first100.pkl
```

**Step 2: Clean Duplicates**

```bash
python data_processing/02_clean_data.py
# Output: data/processed/v2_transcripts_cleaned.pkl
```

**Step 3: Filter & Aggregate for Sentiment**

```bash
python data_processing/03_prepare_for_sentiment.py
# Output: data/processed/v2_transcripts_aggregated_for_gpt.pkl
```

**Step 4: Run Sentiment Analysis**

```bash
python run_sentiment_analysis.py
# Output: data/results/v2_sentiment_results.pkl
# ⚠️  WARNING: This costs ~$20 via Azure OpenAI API
```

---

## Data Viewers

### Results Dashboard
```bash
streamlit run view_results_streamlit.py
```
Interactive web dashboard with 6 tabs: Overview (charts & metrics), Data Table (customizable columns), Search & Filter, Event Details, Raw Data Browser (all fields paginated), Company Reports (per-company sentiment distribution & stats). Includes CSV/JSON export.

### Raw Data Viewer
```bash
streamlit run data_processing/data_viewer.py
```
View raw and intermediate processed data at different pipeline stages (cleaned datasets, aggregated data).

### Ground Truth Labeling Tool
```bash
streamlit run labeling/label_reviewer.py
```
Interactive tool for manually labeling events to create ground truth dataset for model validation.

---

## Project Structure

```
config/             # Azure OpenAI setup
data_processing/    # Data cleaning scripts
sentiment_analysis/ # GPT analyzer & prompts
labeling/           # Ground truth review tool
data/results/       # Output files
```

---

## Output Schema

```python
{
    'companyname': str,
    'event_date': str,
    'sentiment': str,           # positive/negative/neutral
    'positive_prob': float,
    'negative_prob': float,
    'neutral_prob': float,
    'reasoning': str,
    'input_tokens': int,
    'output_tokens': int,
    'cost': float
}
```
