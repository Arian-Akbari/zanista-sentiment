#!/usr/bin/env python3
"""
Main entry point for running sentiment analysis on full dataset
Usage: python run_sentiment_analysis.py
"""

import asyncio
from sentiment_analysis.run_full_analysis import main

if __name__ == "__main__":
    asyncio.run(main())
