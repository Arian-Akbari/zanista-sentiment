"""
Run Sentiment Analysis on Full Dataset (803 Events)
With retry logic, timeouts, progress tracking, and incremental saving
"""

import sys
import pickle
import json
import asyncio
import os
from pathlib import Path
from typing import List, Dict
from asyncio import TimeoutError
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from config.models import get_async_client
from config.pricing import get_model_pricing
from sentiment_analysis.prompts.sentiment_prompts import get_sentiment_prompt, get_user_prompt
from sentiment_analysis.cost_logger import CostLogger
import pandas as pd

# Load environment variables
load_dotenv()


class ProductionSentimentAnalyzer:
    """Production sentiment analyzer with retries, timeouts, and progress tracking"""
    
    def __init__(self, model_name="gpt-4.1", timeout=45, max_retries=3):
        self.client = get_async_client()
        self.model = model_name
        self.pricing = get_model_pricing(model_name)
        self.logger = CostLogger()
        self.timeout = timeout
        self.max_retries = max_retries
        
        self.completed_count = 0
        self.failed_count = 0
        self.total_count = 0
        
    async def analyze_with_retry(self, presentation_text: str, company_name: str = "", 
                                event_date: str = "", temperature: float = 0.0) -> Dict:
        """Analyze sentiment with retry logic and timeout"""
        
        for attempt in range(1, self.max_retries + 1):
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model,
                        temperature=temperature,
                        messages=[
                            {'role': 'system', 'content': get_sentiment_prompt()},
                            {'role': 'user', 'content': get_user_prompt(presentation_text, company_name, event_date)}
                        ],
                        response_format={"type": "json_object"}
                    ),
                    timeout=self.timeout
                )
                
                # Extract token usage
                usage = response.usage
                input_tokens = usage.prompt_tokens
                output_tokens = usage.completion_tokens
                
                # Calculate cost
                cost_breakdown = self.pricing.calculate_cost(input_tokens, output_tokens)
                
                # Log the request
                self.logger.log_request(
                    model=self.model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost=cost_breakdown['total_cost'],
                    metadata={
                        'company': company_name,
                        'event_date': event_date,
                        'attempt': attempt
                    }
                )
                
                # Parse result
                try:
                    result = json.loads(response.choices[0].message.content)
                except (json.JSONDecodeError, AttributeError, TypeError):
                    result = {}
                
                # Validate sentiment
                sentiment = result.get('sentiment', 'neutral').lower()
                if sentiment not in ['positive', 'negative', 'neutral']:
                    sentiment = 'neutral'
                
                # Normalize probabilities
                pos_prob = float(result.get('positive_prob', 0.0))
                neg_prob = float(result.get('negative_prob', 0.0))
                neu_prob = float(result.get('neutral_prob', 0.0))
                
                total_prob = pos_prob + neg_prob + neu_prob
                if total_prob > 0:
                    pos_prob /= total_prob
                    neg_prob /= total_prob
                    neu_prob /= total_prob
                else:
                    neu_prob = 1.0
                
                self.completed_count += 1
                
                return {
                    'sentiment': sentiment,
                    'positive_prob': round(pos_prob, 3),
                    'negative_prob': round(neg_prob, 3),
                    'neutral_prob': round(neu_prob, 3),
                    'reasoning': result.get('reasoning', ''),
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'total_tokens': input_tokens + output_tokens,
                    'cost': round(cost_breakdown['total_cost'], 6),
                    'success': True,
                    'attempts': attempt
                }
                
            except TimeoutError:
                if attempt < self.max_retries:
                    print(f"   ⏱️  Timeout on attempt {attempt}/{self.max_retries} for {company_name[:40]} - retrying...")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    print(f"   ❌ Failed after {self.max_retries} attempts (timeout): {company_name[:40]}")
                    self.failed_count += 1
                    return self._error_result(f'Timeout after {self.max_retries} attempts', attempt)
                    
            except Exception as e:
                if attempt < self.max_retries:
                    print(f"   ⚠️  Error on attempt {attempt}/{self.max_retries} for {company_name[:40]}: {str(e)[:50]} - retrying...")
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    print(f"   ❌ Failed after {self.max_retries} attempts: {company_name[:40]} - {str(e)[:50]}")
                    self.failed_count += 1
                    return self._error_result(str(e), attempt)
        
        # Should never reach here
        self.failed_count += 1
        return self._error_result('Max retries exceeded', self.max_retries)
    
    def _error_result(self, error_msg: str, attempts: int) -> Dict:
        """Return error result structure"""
        return {
            'sentiment': 'neutral',
            'positive_prob': 0.0,
            'negative_prob': 0.0,
            'neutral_prob': 1.0,
            'reasoning': f'Error: {error_msg}',
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': 0,
            'cost': 0.0,
            'success': False,
            'attempts': attempts
        }
    
    async def analyze_full_dataset(self, data_path: str, output_path: str = None, 
                                   batch_size: int = 50, save_every: int = 100):
        """
        Analyze full dataset with progress tracking and incremental saving
        
        Args:
            data_path: Path to aggregated dataset (pkl file)
            output_path: Where to save results (default: data/results/sentiment_results.pkl)
            batch_size: Number of concurrent requests (default: 50)
            save_every: Save progress every N events (default: 100)
        """
        
        print(f"\nSENTIMENT ANALYSIS - FULL DATASET")
        print(f"Model: {self.model} | Timeout: {self.timeout}s | Max retries: {self.max_retries}")
        print(f"Batch size: {batch_size} concurrent | Auto-save every: {save_every} events\n")
        
        # Load dataset
        print(f"📂 Loading dataset from: {data_path}")
        data_file = Path(data_path)
        if not data_file.exists():
            print(f"❌ Error: File not found: {data_path}")
            return
        
        with open(data_path, 'rb') as f:
            df = pickle.load(f)
        
        self.total_count = len(df)
        print(f"✅ Loaded {self.total_count} events\n")
        
        # Setup output path
        if output_path is None:
            output_path = "data/results/sentiment_results.pkl"
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Track start time
        start_time = datetime.now()
        
        # Process in batches
        all_results = []
        
        for batch_start in range(0, self.total_count, batch_size):
            batch_end = min(batch_start + batch_size, self.total_count)
            batch_df = df.iloc[batch_start:batch_end]
            
            print(f"\n📊 Processing batch {batch_start + 1}-{batch_end} of {self.total_count}")
            print(f"   Progress: {batch_start}/{self.total_count} ({batch_start/self.total_count*100:.1f}%)")
            print(f"   Remaining: {self.total_count - batch_start} events")
            
            # Create tasks for this batch
            tasks = []
            for idx, row in batch_df.iterrows():
                task = self.analyze_with_retry(
                    presentation_text=row['presentation_text'],
                    company_name=row['companyname'],
                    event_date=row['event_date']
                )
                tasks.append((idx, row, task))
            
            # Execute batch
            batch_results = await asyncio.gather(*[task for _, _, task in tasks])
            
            # Process results and add metadata
            for i, (idx, row, _) in enumerate(tasks):
                result_dict = {
                    'companyid': row['companyid'],
                    'companyname': row['companyname'],
                    'transcriptid': row['transcriptid'],
                    'event_date': row['event_date'],
                    'headline': row.get('headline', ''),
                    'presentation_text': row['presentation_text'],
                    'total_word_count': row['total_word_count'],
                    
                    # Sentiment results
                    'sentiment': batch_results[i]['sentiment'],
                    'positive_prob': batch_results[i]['positive_prob'],
                    'negative_prob': batch_results[i]['negative_prob'],
                    'neutral_prob': batch_results[i]['neutral_prob'],
                    'reasoning': batch_results[i]['reasoning'],
                    
                    # API usage
                    'input_tokens': batch_results[i]['input_tokens'],
                    'output_tokens': batch_results[i]['output_tokens'],
                    'total_tokens': batch_results[i]['total_tokens'],
                    'cost': batch_results[i]['cost'],
                    'success': batch_results[i]['success'],
                    'attempts': batch_results[i]['attempts']
                }
                all_results.append(result_dict)
            
            # Print batch summary
            batch_success = sum(1 for r in batch_results if r['success'])
            batch_failed = len(batch_results) - batch_success
            print(f"   ✅ Completed: {batch_success}/{len(batch_results)}")
            if batch_failed > 0:
                print(f"   ❌ Failed: {batch_failed}/{len(batch_results)}")
            
            # Calculate running stats
            elapsed = (datetime.now() - start_time).total_seconds()
            events_per_sec = self.completed_count / elapsed if elapsed > 0 else 0
            remaining_events = self.total_count - (batch_end)
            eta_seconds = remaining_events / events_per_sec if events_per_sec > 0 else 0
            
            print(f"   ⏱️  Speed: {events_per_sec:.2f} events/sec")
            print(f"   ⏳ ETA: {eta_seconds/60:.1f} minutes")
            
            # Incremental save
            if (batch_end % save_every == 0) or (batch_end == self.total_count):
                print(f"   💾 Saving progress... ({len(all_results)} events)")
                df_results = pd.DataFrame(all_results)
                with open(output_file, 'wb') as f:
                    pickle.dump(df_results, f)
                print(f"   ✅ Saved to: {output_file}")
        
        # Final statistics
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        print(f"\nANALYSIS COMPLETE")
        print(f"Total: {self.total_count} | Success: {self.completed_count} ({self.completed_count/self.total_count*100:.1f}%) | Failed: {self.failed_count}")
        print(f"Time: {total_duration/60:.1f} min | Speed: {self.completed_count/total_duration:.2f} events/sec\n")
        
        # Cost summary
        self.logger.print_session_summary()
        
        # Distribution of sentiments
        df_results = pd.DataFrame(all_results)
        print(f"\nSENTIMENT DISTRIBUTION")
        sentiment_counts = df_results['sentiment'].value_counts()
        for sentiment, count in sentiment_counts.items():
            print(f"{sentiment.upper():10s}: {count:4d} ({count/len(df_results)*100:5.1f}%)")
        
        # Save final results
        print(f"💾 Final save to: {output_file}")
        with open(output_file, 'wb') as f:
            pickle.dump(df_results, f)
        print(f"✅ Results saved successfully")
        
        return df_results


async def main():
    """Main function to run full analysis"""
    
    # Configuration
    DATA_PATH = "data/processed/v2_transcripts_aggregated_for_gpt.pkl"
    OUTPUT_PATH = "data/results/v2_sentiment_results.pkl"
    MODEL = os.getenv("MODEL", "gpt-4.1")  # Read from .env, default to gpt-4.1
    TIMEOUT = 45  # seconds
    MAX_RETRIES = 3
    BATCH_SIZE = 50  # concurrent requests
    SAVE_EVERY = 100  # save progress every N events
    
    # Create analyzer
    print(f"Using model: {MODEL}")
    analyzer = ProductionSentimentAnalyzer(
        model_name=MODEL,
        timeout=TIMEOUT,
        max_retries=MAX_RETRIES
    )
    
    # Run analysis
    results = await analyzer.analyze_full_dataset(
        data_path=DATA_PATH,
        output_path=OUTPUT_PATH,
        batch_size=BATCH_SIZE,
        save_every=SAVE_EVERY
    )
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
