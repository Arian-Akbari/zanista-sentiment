"""
Cost Logger for API Usage Tracking
Logs all API calls with token usage and costs
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

sys.path.append(str(Path(__file__).parent.parent))


class CostLogger:
    def __init__(self, log_file="data/results/cost_log.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.session_costs = []
        
    def log_request(self, model: str, input_tokens: int, output_tokens: int, 
                   cost: float, metadata: Dict = None):
        """Log a single API request"""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'cost': cost,
            'metadata': metadata or {}
        }
        
        # Append to JSONL file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Track in session
        self.session_costs.append(log_entry)
    
    def get_session_summary(self) -> Dict:
        """Get summary of current session costs"""
        
        if not self.session_costs:
            return {
                'total_requests': 0,
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'total_cost': 0.0
            }
        
        return {
            'total_requests': len(self.session_costs),
            'total_input_tokens': sum(e['input_tokens'] for e in self.session_costs),
            'total_output_tokens': sum(e['output_tokens'] for e in self.session_costs),
            'total_cost': sum(e['cost'] for e in self.session_costs)
        }
    
    def print_session_summary(self):
        """Print summary of session costs"""
        summary = self.get_session_summary()
        
        print("\nSESSION COST SUMMARY")
        print(f"Total requests:    {summary['total_requests']}")
        print(f"Input tokens:      {summary['total_input_tokens']:,}")
        print(f"Output tokens:     {summary['total_output_tokens']:,}")
        print(f"Total tokens:      {summary['total_input_tokens'] + summary['total_output_tokens']:,}")
        print(f"Total cost:        ${summary['total_cost']:.4f}")
    
    @staticmethod
    def load_all_logs(log_file="data/results/cost_log.jsonl") -> List[Dict]:
        """Load all logged costs from file"""
        
        log_path = Path(log_file)
        if not log_path.exists():
            return []
        
        logs = []
        with open(log_path, 'r') as f:
            for line in f:
                logs.append(json.loads(line.strip()))
        
        return logs
    
    @staticmethod
    def get_total_project_cost(log_file="data/results/cost_log.jsonl") -> Dict:
        """Get total project cost from all logs"""
        
        logs = CostLogger.load_all_logs(log_file)
        
        if not logs:
            return {
                'total_requests': 0,
                'total_cost': 0.0,
                'by_model': {}
            }
        
        total_cost = sum(e['cost'] for e in logs)
        total_requests = len(logs)
        
        # Group by model
        by_model = {}
        for log in logs:
            model = log['model']
            if model not in by_model:
                by_model[model] = {
                    'requests': 0,
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'cost': 0.0
                }
            by_model[model]['requests'] += 1
            by_model[model]['input_tokens'] += log['input_tokens']
            by_model[model]['output_tokens'] += log['output_tokens']
            by_model[model]['cost'] += log['cost']
        
        return {
            'total_requests': total_requests,
            'total_cost': total_cost,
            'by_model': by_model
        }
