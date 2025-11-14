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

## Reproducing Analysis

```bash
# Setup
source venv/bin/activate
pip install -r requirements.txt

# Configure Azure OpenAI (requires .env file)
# AZURE_OPENAI_API_KEY=your-key
# AZURE_OPENAI_ENDPOINT=your-endpoint
# AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Run full analysis (803 events)
python run_sentiment_analysis.py

# View processed data
streamlit run data_processing/data_viewer.py
```

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
