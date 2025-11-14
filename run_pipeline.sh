#!/bin/bash

# Zanista Earnings Call Sentiment Analysis - Full Pipeline
# Executes all data processing steps in sequence

set -e  # Exit on error

echo "=========================================="
echo "ZANISTA SENTIMENT ANALYSIS PIPELINE"
echo "=========================================="
echo ""

# Check if raw data exists
if [ ! -f "transcripts_2024.pkl" ] && [ ! -f "data/raw/transcripts_2024.pkl" ]; then
    echo "❌ ERROR: Raw data file 'transcripts_2024.pkl' not found"
    echo "   Searched in: ./transcripts_2024.pkl and data/raw/transcripts_2024.pkl"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  WARNING: Virtual environment not activated"
    echo "   Run: source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env file not found"
    echo "   Sentiment analysis (Step 4) will fail without Azure OpenAI credentials"
    echo ""
fi

echo "=========================================="
echo "STEP 1: Filter to First 100 Companies"
echo "=========================================="
python data_processing/01_filter_companies.py
if [ $? -ne 0 ]; then
    echo "❌ Step 1 failed"
    exit 1
fi
echo "✅ Step 1 complete: v2_transcripts_first100.pkl created"
echo ""

echo "=========================================="
echo "STEP 2: Clean Duplicates"
echo "=========================================="
python data_processing/02_clean_data.py
if [ $? -ne 0 ]; then
    echo "❌ Step 2 failed"
    exit 1
fi
echo "✅ Step 2 complete: data/processed/v2_transcripts_cleaned.pkl created"
echo ""

echo "=========================================="
echo "STEP 3: Filter & Aggregate for Sentiment"
echo "=========================================="
python data_processing/03_prepare_for_sentiment.py
if [ $? -ne 0 ]; then
    echo "❌ Step 3 failed"
    exit 1
fi
echo "✅ Step 3 complete: data/processed/v2_transcripts_aggregated_for_gpt.pkl created"
echo ""

echo "=========================================="
echo "STEP 4: Sentiment Analysis"
echo "=========================================="
echo "⚠️  WARNING: This step will cost approximately $20 via Azure OpenAI API"
echo ""
read -p "Run sentiment analysis? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python run_sentiment_analysis.py
    if [ $? -ne 0 ]; then
        echo "❌ Step 4 failed"
        exit 1
    fi
    echo "✅ Step 4 complete: data/results/v2_sentiment_results.pkl created"
else
    echo "⏭️  Skipped sentiment analysis"
    echo "   Run manually later with: python run_sentiment_analysis.py"
fi

echo ""
echo "=========================================="
echo "PIPELINE COMPLETE"
echo "=========================================="
echo ""
echo "Output files:"
echo "  1. v2_transcripts_first100.pkl (filtered companies)"
echo "  2. data/processed/v2_transcripts_cleaned.pkl (deduplicated)"
echo "  3. data/processed/v2_transcripts_aggregated_for_gpt.pkl (ready for sentiment)"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  4. data/results/v2_sentiment_results.pkl (sentiment analysis results)"
fi
echo ""
echo "To view data: streamlit run data_processing/data_viewer.py"
echo ""
