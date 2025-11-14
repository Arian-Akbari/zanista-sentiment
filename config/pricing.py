"""
Model Pricing Configuration
All prices are per 1 million tokens (as of Nov 2024)
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ModelPricing:
    """Pricing structure for a model"""
    input_price: float
    output_price: float
    cached_input_price: float = 0.0
    training_price: float = 0.0
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, 
                      cached_tokens: int = 0) -> Dict[str, float]:
        """Calculate cost breakdown"""
        
        regular_input = max(0, input_tokens - cached_tokens)
        
        input_cost = (regular_input / 1_000_000) * self.input_price
        cached_cost = (cached_tokens / 1_000_000) * self.cached_input_price
        output_cost = (output_tokens / 1_000_000) * self.output_price
        total_cost = input_cost + cached_cost + output_cost
        
        return {
            'input_cost': input_cost,
            'cached_cost': cached_cost,
            'output_cost': output_cost,
            'total_cost': total_cost
        }


MODEL_PRICING = {
    'gpt-4.1': ModelPricing(
        input_price=3.00,
        cached_input_price=0.75,
        output_price=12.00,
        training_price=25.00
    ),
    'gpt-4.1-mini': ModelPricing(
        input_price=0.80,
        cached_input_price=0.20,
        output_price=3.20,
        training_price=5.00
    ),
    'gpt-4o': ModelPricing(
        input_price=2.50,
        cached_input_price=1.25,
        output_price=10.00
    ),
    'gpt-4o-mini': ModelPricing(
        input_price=0.15,
        cached_input_price=0.075,
        output_price=0.60
    )
}


def get_model_pricing(model_name: str) -> ModelPricing:
    """Get pricing for a model"""
    model_key = model_name.lower()
    return MODEL_PRICING.get(model_key, MODEL_PRICING['gpt-4.1'])
