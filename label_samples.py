"""
Label 20 sample events with sentiment analysis
This script reads each event and assigns AI labels based on tone/language analysis
"""

import pickle
import pandas as pd

# Load sample dataset
with open('sample_20_for_labeling.pkl', 'rb') as f:
    df = pickle.load(f)

# AI labels for each event (after reading and analyzing)
# Format: (sentiment, pos_prob, neg_prob, neu_prob, reasoning)
ai_labels = [
    # 1. Apellis - "absolutely thrilled", "remarkable results", positive regulatory timeline
    ('positive', 0.85, 0.05, 0.10, 
     "Very positive: 'absolutely thrilled', 'remarkable results', confident regulatory timeline"),
    
    # 2. NVIDIA - Technical webinar, educational tone, neutral product overview
    ('neutral', 0.20, 0.10, 0.70,
     "Neutral educational webinar: informational tone, no performance/results discussion"),
    
    # 3. Chart Industries - Confident business overview, positive about capabilities
    ('positive', 0.70, 0.10, 0.20,
     "Confident presentation of capabilities and market position, positive framing"),
    
    # 4. Constellation - Only 2 words "Thanks, Dara" - cannot assess
    ('neutral', 0.0, 0.0, 1.0,
     "Insufficient content (2 words only)"),
    
    # 5. Biogen - Need full analysis (8130 words) - will read key sections
    None,
    
    # 6. Cellectar - Need analysis
    None,
    
    # 7. BioMarin - Need analysis
    None,
    
    # 8. Lionsgate - Need analysis
    None,
    
    # 9. Avantor - Only 18 words, insufficient
    None,
    
    # 10. AngioDynamics - Need analysis
    None,
    
    # 11. Franklin Covey - Need analysis
    None,
    
    # 12. Merck - Need analysis
    None,
    
    # 13. EOG Resources - Only 12 words, insufficient
    None,
    
    # 14. US Foods - Need analysis
    None,
    
    # 15. Penumbra - Need analysis
    None,
    
    # 16. Gilead - Only 14 words, insufficient
    None,
    
    # 17. Costco - Need analysis
    None,
    
    # 18. Expro - Only 2 words, insufficient
    None,
    
    # 19. Commercial Metals - Need analysis
    None,
    
    # 20. Medtronic - Need analysis
    None,
]

# Print events that need analysis
print("Events requiring detailed analysis:")
for idx, label in enumerate(ai_labels):
    if label is None:
        print(f"{idx+1}. {df.iloc[idx]['companyname']} ({df.iloc[idx]['total_word_count']} words)")
