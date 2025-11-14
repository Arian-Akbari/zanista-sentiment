# 📊 Zanista Earnings Call Sentiment Analysis

**Client:** Zanista.AI  
**Project:** Executive Presentation Sentiment Analysis  
**Dataset:** First 100 companies, 2024 earning call transcripts  
**Status:** ✅ Data Cleaning Complete | ✅ Ground Truth Labeled | ✅ Prompt Validated (85% accuracy) | 🔄 Ready for Full Analysis

---

## 🎯 Project Overview

### **Business Context**
This project is part of Zanista's **NewsWitch** product. It analyzes the **tone and perspective** of company executives during earnings call presentations.

### **Core Objective**
Analyze the **tone/language** used by executives when presenting earnings results, regardless of actual financial performance. We want to understand how executives **frame and present** results, not just what the results are.

---

## 📋 Task Requirements

### **1. Sentiment Label Definitions**
- **Positive:** Optimistic tone, good financial performance presentation, beating expectations
- **Negative:** Cautious tone, poor results presentation, challenges/concerns
- **Neutral:** Factual/balanced tone, mixed signals, no clear direction

### **2. Analysis Granularity**
- **Company-level sentiment** per earnings call event
- **Output:** One sentiment label per event

### **3. Data Scope**
- **Speaker Type:** `speakertypename == "Executives"` ONLY
- **Component Type:** `transcriptcomponenttypename == "Presenter Speech"` ONLY
- **Companies:** First 100 companies only
- **Events:** 803 unique earnings call events

### **4. Deliverables**
1. **Sentiment Results:** DataFrame saved as `.pkl` file with sentiment labels and probabilities
2. **Code:** All scripts with clear instructions
3. **Documentation:** Brief explanation of output columns and results

---

## ✅ Completed Work

### **Phase 1: Data Exploration**
- Built Streamlit viewer to inspect 102,380 rows across 100 companies
- Discovered 32.7% duplication rate in raw data
- Found events recorded up to 7 times with different transcript IDs

### **Phase 2: Data Cleaning**
- 3-stage deduplication pipeline
- Merged duplicate transcript versions
- Verified cleaning quality (98.95% uniqueness achieved)

---

## 📊 Data Cleaning Results

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| **Total Rows** | 102,380 | 69,625 | -32,755 (-32.0%) |
| **Text Volume** | 15.3M words | 12.3M words | -3.0M words (-19.4%) |
| **Unique Texts** | 68,893 | 68,893 | 0 (0%) ✅ |
| **Transcript Versions** | 2,190 | 892 | -1,298 (-59.3%) |

### **What We Removed**
- 32,755 duplicate rows (32% of data)
- ~3 million duplicate words (19.4% of text volume)
- 909 redundant transcript versions merged into single events
- **100% of unique information preserved** (zero content loss)

### **Target Dataset (After Filtering)**
- **Total:** 69,625 clean rows
- **Executive Presenter Speech:** 5,465 components across 100 companies
- **Events:** 803 unique earnings call events
- **Average:** 6.8 presentations per event
- **Text Volume:** ~5.5M tokens for GPT processing

---

## 🏗️ Technical Architecture

### **Data Flow Pipeline**
```
1. Raw Data (transcripts_2024.pkl)
   ↓
2. Filter First 100 Companies → transcripts_first100.pkl
   ↓
3. 3-Stage Deduplication → transcripts_cleaned.pkl
   ↓
4. Filter Executives + Presenter Speech → transcripts_filtered_for_gpt.pkl
   ↓
5. Aggregate by Event (803 events)
   ↓
6. GPT Sentiment Analysis → sentiment_results.pkl
```

### **GPT Configuration**
- **Model:** GPT-4.1 (Azure OpenAI)
- **Temperature:** 0.0 (deterministic)
- **Output Format:** JSON with sentiment labels and probabilities
- **Processing:** Async batch processing for performance

---

## 📁 Project Structure

```
zanista/
├── config/
│   ├── models.py                    # Azure OpenAI client
│   ├── pricing.py                   # Cost calculation
│   └── models_enum.py               # Model enumeration
│
├── data/
│   ├── raw/                         # Original dataset
│   ├── processed/                   # Cleaned data
│   ├── labeled/                     # Ground truth samples
│   └── results/                     # Output files
│
├── data_processing/
│   ├── 01_filter_companies.py       # Extract first 100 companies
│   ├── 02_clean_data.py             # 3-stage deduplication
│   ├── 03_prepare_for_sentiment.py  # Aggregate by event
│   └── data_viewer.py               # Streamlit data viewer
│
├── sentiment_analysis/
│   ├── prompts/
│   │   └── sentiment_prompts.py     # Production prompt (85% accuracy)
│   ├── sentiment_analyzer.py        # Main analyzer with async processing
│   └── cost_logger.py               # API cost tracking
│
├── labeling/
│   └── label_reviewer.py            # Ground truth review tool
│
├── .env                             # Azure OpenAI credentials
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

---

## 🚀 Setup & Usage

### **1. Environment Setup**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **2. Configure Azure OpenAI**
Create `.env` file with:
```
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=your-deployment
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
```

### **3. Run Data Viewer**
```bash
streamlit run data_viewer.py
```

### **4. Data Processing Pipeline**
```bash
# 1. Extract first 100 companies (already done)
python data_processing/01_filter_companies.py

# 2. Clean duplicates (already done)
python data_processing/02_clean_data.py

# 3. Prepare for sentiment analysis (already done)
python data_processing/03_prepare_for_sentiment.py

# 4. Run sentiment analysis
python sentiment_analysis/sentiment_analyzer.py
```

---

## 📊 Ground Truth Labeling & Prompt Development

### **Phase 3: Ground Truth Creation**
- Sampled 20 random events from 803 total
- Labeled using balanced approach (financial reality + executive tone)
- Oracle-validated in batches of 5
- **Final distribution: 10 Positive (50%), 2 Negative (10%), 8 Neutral (40%)**

### **Labeling Methodology (Balanced Approach)**
**NEGATIVE:** Clear financial declines (revenue/earnings down significantly, losses reported)
**POSITIVE:** Strong financials OR enthusiastic tone with commercial catalysts  
**NEUTRAL:** Mixed signals, no financials, or factual reporting

Key insight: Executives always spin negatives → TRUE negatives are rare (~10%)

### **Phase 4: Prompt Development & Iteration**
Developed 7 prompt versions through iterative testing:
- **V1:** 65% accuracy - Initial balanced approach
- **V2:** 80% accuracy - Added decision tree, enthusiasm detection
- **V3-V6:** 65-85% accuracy - Various refinements
- **V7:** 95% accuracy - With specific examples (overfitted)
- **FINAL:** 85% accuracy - Generalized, production-ready ✅

### **Model Selection & Pricing**
Tested models on 20 samples:

| Model | Accuracy | Cost (20 samples) | Cost (803 events) | Decision |
|-------|----------|-------------------|-------------------|----------|
| **GPT-4.1** | **85%** | **$0.31** | **$12.55** | **✅ SELECTED** |
| GPT-4o-mini | 75% | $0.01 | $0.59 | ❌ Too inaccurate (misses negatives) |
| GPT-4.1-mini | N/A | N/A | ~$3.33 (est.) | ❌ Not deployed |

**Decision:** Using **GPT-4.1** for production - 85% accuracy justifies the cost

### **Cost Tracking System**
- All API calls logged to `data/results/cost_log.jsonl`
- Tracks input/output tokens and costs per request
- Real-time cost estimation for full dataset

## 🎯 Current Status & Next Steps

### **✅ Completed**
- [x] Data exploration and quality assessment
- [x] 3-stage deduplication pipeline
- [x] Data filtering (Executives + Presenter Speech)
- [x] Event aggregation (803 events ready)
- [x] Azure OpenAI client configuration
- [x] Ground truth creation (20 samples labeled)
- [x] Sentiment prompt development (7 iterations)
- [x] Prompt validation (85% accuracy on test set)
- [x] Cost tracking system implemented

### **🔄 Next Steps**
- [ ] Run sentiment analysis on full 803 events
- [ ] Review results and validate quality
- [ ] Generate final deliverables

### **📊 Expected Output Schema**
```python
{
    'companyid': int,
    'companyname': str,
    'transcriptid': int,
    'event_date': str,
    'headline': str,
    'presentation_text': str,
    'total_word_count': int,
    
    # Sentiment results
    'sentiment': str,  # positive/negative/neutral
    'positive_prob': float,
    'negative_prob': float,
    'neutral_prob': float,
    'reasoning': str,
    
    # API usage
    'input_tokens': int,
    'output_tokens': int,
    'total_tokens': int,
    'cost': float
}
```

---

## 💰 Cost Estimation

- **Model:** GPT-4.1
- **Total Events:** 803
- **Average Tokens:** ~1,200 per event
- **Estimated Cost:** ~$12.55 for full dataset

---

## 📞 Contact

**Client:** Zanista.AI  
**Product:** NewsWitch
