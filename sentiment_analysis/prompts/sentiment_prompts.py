def get_sentiment_prompt():
    return """Classify earnings call presentation sentiment: POSITIVE, NEUTRAL, or NEGATIVE.

CLASSIFICATION FRAMEWORK:

**NEGATIVE** - Material financial deterioration (facts override spin):
• Revenue declining ≥5% year-over-year
• Earnings/EBITDA/Operating Income declining ≥10% year-over-year
• Net losses reported OR EPS down ≥10% year-over-year
• Guidance explicitly reduced or cut
→ Label: NEGATIVE with probability 0.70-0.90 (higher for larger declines)

**POSITIVE** - Three pathways:

Path 1 - Strong Financial Performance:
• Revenue growing year-over-year (any amount) AND earnings/EBITDA growing
• Beating expectations, guidance, or targets
• Margin expansion or record results mentioned
→ Label: POSITIVE with probability 0.75-0.85

Path 2 - Positive Guidance & Milestones:
• Guidance raised, reaffirmed, or maintained with confident tone
• Profitability milestone achieved
• Strong forward momentum emphasized
→ Label: POSITIVE with probability 0.70-0.80

Path 3 - Strategic Optimism (for non-financial events):
• Highly enthusiastic language ("thrilled", "transformational", "remarkable", "breakthrough")
  AND concrete near-term catalysts (≤12 months):
  - Regulatory submissions/approvals expected
  - Product launches in progress or imminent
  - Major contracts/partnerships announced
OR
• Strategic business overview with growth/expansion/execution themes
  AND margin improvement or competitive positioning emphasized
→ Label: POSITIVE with probability 0.65-0.75

**NEUTRAL** - Mixed, unclear, or non-financial:
• Temporal mismatch: Current period strong BUT future guidance weak (or vice versa)
• Divisional mix: Some segments up, others down, no clear consolidated direction
• Non-financial content: Clinical trials, product updates WITHOUT financial metrics AND WITHOUT near-term commercial milestones
• Factual reporting with balanced tone, no strong directional signals
• Very brief content (<50 words)
→ Label: NEUTRAL with probability 0.60-0.80

DECISION RULES:
1. Check for NEGATIVE triggers first - if found, label NEGATIVE immediately
2. If no negatives, check for POSITIVE triggers (any of 3 paths)
3. If neither clear, default to NEUTRAL
4. One underperforming product/region in overall strong business → Still POSITIVE
5. Numbers always override management spin
6. Probabilities must sum to 1.0, dominant class ≥0.60

OUTPUT (JSON only):
{
    "sentiment": "positive|negative|neutral",
    "positive_prob": 0.0-1.0,
    "negative_prob": 0.0-1.0,
    "neutral_prob": 0.0-1.0,
    "reasoning": "Cite key evidence (specific metrics if available, or tone + context if not)"
}"""


def get_user_prompt(presentation_text: str, company_name: str = '', 
                    event_date: str = '') -> str:
    return f"""Analyze this presentation and return JSON with sentiment classification:

Company: {company_name}
Date: {event_date}

Presentation:
{presentation_text}"""
