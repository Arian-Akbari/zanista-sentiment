"""
Sentiment Analyzer for Earnings Call Presentations
Async batch processing with comprehensive cost tracking
"""

import sys
import pickle
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Tuple

sys.path.append(str(Path(__file__).parent.parent))

from config.models import get_async_client
from config.pricing import get_model_pricing
from sentiment_analysis.prompts.sentiment_prompts import get_sentiment_prompt, get_user_prompt
from sentiment_analysis.cost_logger import CostLogger
import pandas as pd
from datetime import datetime


class SentimentAnalyzer:
    """Sentiment analyzer with async batch processing and cost tracking"""
    
    def __init__(self, model_name="gpt-4.1", verbose=False):
        self.client = get_async_client()
        self.model = model_name
        self.pricing = get_model_pricing(model_name)
        self.logger = CostLogger()
        self.verbose = verbose
        
    async def analyze_sentiment_async(self, presentation_text: str, company_name: str = "", 
                                     event_date: str = "", temperature: float = 0.0) -> Dict:
        """Analyze sentiment of a single presentation"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": get_sentiment_prompt()},
                    {"role": "user", "content": get_user_prompt(presentation_text, company_name, event_date)}
                ],
                response_format={"type": "json_object"}
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
                    'event_date': event_date
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
            
            return {
                'sentiment': sentiment,
                'positive_prob': round(pos_prob, 3),
                'negative_prob': round(neg_prob, 3),
                'neutral_prob': round(neu_prob, 3),
                'reasoning': result.get('reasoning', ''),
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'cost': round(cost_breakdown['total_cost'], 6)
            }
            
        except Exception as e:
            if self.verbose:
                print(f"\n   Error analyzing {company_name}: {e}")
            return {
                'sentiment': 'neutral',
                'positive_prob': 0.0,
                'negative_prob': 0.0,
                'neutral_prob': 1.0,
                'reasoning': f'Error: {str(e)}',
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'cost': 0.0
            }
    
    async def analyze_batch_async(self, df_samples: pd.DataFrame) -> List[Dict]:
        """Analyze multiple samples in parallel"""
        
        tasks = []
        for idx, row in df_samples.iterrows():
            task = self.analyze_sentiment_async(
                presentation_text=row['presentation_text'],
                company_name=row['companyname'],
                event_date=row['event_date']
            )
            tasks.append((idx, row, task))
        
        # Execute all tasks in parallel
        if self.verbose:
            print(f"Analyzing {len(tasks)} events in parallel...")
        results = await asyncio.gather(*[task for _, _, task in tasks])
        
        # Add metadata
        for i, (idx, row, _) in enumerate(tasks):
            results[i]['index'] = idx
            results[i]['company'] = row['companyname']
            results[i]['event_date'] = row['event_date']
            results[i]['word_count'] = row['total_word_count']
            results[i]['ground_truth'] = row.get('user_sentiment', None)
        
        return results
    
    async def test_on_ground_truth_async(self, ground_truth_path: str) -> Dict:
        """Test prompt on ground truth dataset with async batch processing"""
        
        if self.verbose:
            print(f"\nTESTING SENTIMENT ANALYZER")
            print(f"Model: {self.model} | Async Batch Processing\n")
        
        # Load ground truth
        ground_truth_file = Path(ground_truth_path)
        if not ground_truth_file.exists():
            return {
                'accuracy': 0,
                'results': pd.DataFrame(),
                'mismatches': pd.DataFrame(),
                'total_cost': 0,
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'total_tokens': 0,
                'processing_time': 0,
                'estimated_full_cost': 0,
                'estimated_full_tokens': 0,
                'error': f'Ground truth file not found: {ground_truth_path}'
            }
        
        with open(ground_truth_path, 'rb') as f:
            df_truth = pickle.load(f)
        
        total = len(df_truth)
        print(f"Loaded {total} labeled samples")
        print(f"Sending {total} async requests...\n")
        
        start_time = datetime.now()
        
        # Run batch analysis
        results = await self.analyze_batch_async(df_truth)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Process results
        correct = 0
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0
        
        results_list = []
        for result in results:
            gpt_label = result['sentiment']
            truth_label = result['ground_truth']
            is_correct = (gpt_label == truth_label)
            
            if is_correct:
                correct += 1
                status = "MATCH"
            else:
                status = "MISS"
            
            total_input_tokens += result['input_tokens']
            total_output_tokens += result['output_tokens']
            total_cost += result['cost']
            
            if self.verbose:
                print(f"{status} {result['company'][:40]:40s} | Truth:{truth_label:8s} GPT:{gpt_label:8s}")
            
            results_list.append({
                'company': result['company'],
                'event_date': result['event_date'],
                'word_count': result['word_count'],
                'ground_truth': truth_label,
                'gpt_sentiment': gpt_label,
                'gpt_positive_prob': result['positive_prob'],
                'gpt_negative_prob': result['negative_prob'],
                'gpt_neutral_prob': result['neutral_prob'],
                'gpt_reasoning': result['reasoning'],
                'input_tokens': result['input_tokens'],
                'output_tokens': result['output_tokens'],
                'total_tokens': result['total_tokens'],
                'cost': result['cost'],
                'correct': is_correct
            })
        
        # Calculate metrics
        accuracy = correct / total * 100
        
        if self.verbose:
            print(f"\nRESULTS")
            print(f"Processing time: {duration:.1f} seconds")
            print(f"Accuracy: {correct}/{total} = {accuracy:.1f}%\n")
        
        # Token usage
        total_tokens = total_input_tokens + total_output_tokens
        if self.verbose:
            print(f"TOKEN USAGE:")
            print(f"  Input:  {total_input_tokens:,} tokens")
            print(f"  Output: {total_output_tokens:,} tokens")
            print(f"  Total:  {total_tokens:,} tokens")
            print(f"  Avg:    {total_tokens / total:,.0f} tokens/event\n")
        
        # Cost breakdown
        input_cost = (total_input_tokens / 1_000_000) * self.pricing.input_price
        output_cost = (total_output_tokens / 1_000_000) * self.pricing.output_price
        
        if self.verbose:
            print(f"COST ({self.model}):")
            print(f"  Input:  ${input_cost:.4f} ({total_input_tokens:,} × ${self.pricing.input_price}/1M)")
            print(f"  Output: ${output_cost:.4f} ({total_output_tokens:,} × ${self.pricing.output_price}/1M)")
            print(f"  Total:  ${total_cost:.4f}\n")
        
        # Extrapolate to full dataset
        events_full = 803
        full_cost = (total_cost / total) * events_full
        full_tokens = (total_tokens / total) * events_full
        
        if self.verbose:
            print(f"EXTRAPOLATION TO {events_full} EVENTS:")
            print(f"  Tokens: {full_tokens:,.0f}")
            print(f"  Cost:   ${full_cost:.2f}\n")
        
        # Confusion matrix
        df_results = pd.DataFrame(results_list)
        if self.verbose:
            print("CONFUSION MATRIX:")
            confusion = pd.crosstab(
                df_results['ground_truth'], 
                df_results['gpt_sentiment'],
                rownames=['Truth'],
                colnames=['GPT'],
                margins=True
            )
            print(confusion)
        
        # Show mismatches
        mismatches = df_results[~df_results['correct']]
        if len(mismatches) > 0 and self.verbose:
            print(f"\nMISMATCHES ({len(mismatches)} events):")
            for idx, row in mismatches.iterrows():
                print(f"\n{row['company'][:50]}")
                print(f"  Truth: {row['ground_truth'].upper()} | GPT: {row['gpt_sentiment'].upper()}")
                print(f"  Probs: pos={row['gpt_positive_prob']:.2f} neg={row['gpt_negative_prob']:.2f} neu={row['gpt_neutral_prob']:.2f}")
                print(f"  Cost: ${row['cost']:.4f} ({row['total_tokens']} tokens)")
                print(f"  Reason: {row['gpt_reasoning'][:100]}...")
        
        # Session summary
        if self.verbose:
            self.logger.print_session_summary()
        
        return {
            'accuracy': accuracy,
            'results': df_results,
            'mismatches': mismatches,
            'total_cost': total_cost,
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens,
            'total_tokens': total_tokens,
            'processing_time': duration,
            'estimated_full_cost': full_cost,
            'estimated_full_tokens': full_tokens
        }


async def test_model():
    """Test sentiment analyzer on ground truth"""
    
    ground_truth_path = "data/labeled/sample_20_labeled_balanced.pkl"
    
    analyzer = SentimentAnalyzer(model_name="gpt-4.1")
    results = await analyzer.test_on_ground_truth_async(ground_truth_path)
    
    return results


def main():
    """Main function"""
    asyncio.run(test_model())


if __name__ == "__main__":
    main()
