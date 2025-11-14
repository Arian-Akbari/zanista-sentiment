"""
STEP 1 & 2: Filter and Aggregate Dataset for Sentiment Analysis

This script:
1. Filters for Executives + Presenter Speech only
2. Aggregates all speeches per event (transcriptid) into single text
3. Creates clean dataset ready for GPT processing

Output: One row per event with combined presentation text
"""

import pickle
import pandas as pd
from datetime import datetime

print('=' * 100)
print('PREPARE DATASET FOR SENTIMENT ANALYSIS - Steps 1 & 2')
print('=' * 100)
print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print()

# ============================================================================
# STEP 1: Load and Filter Data
# ============================================================================
print('=' * 100)
print('STEP 1: LOAD AND FILTER DATA')
print('=' * 100)

print('Loading cleaned dataset...')
with open('transcripts_cleaned.pkl', 'rb') as f:
    df = pickle.load(f)

print(f'✓ Loaded {len(df):,} rows from transcripts_cleaned.pkl')
print()

print('Applying filters:')
print('  - speakertypename == "Executives"')
print('  - transcriptcomponenttypename == "Presenter Speech"')
print()

# Filter for target data
df_filtered = df[
    (df['speakertypename'] == 'Executives') &
    (df['transcriptcomponenttypename'] == 'Presenter Speech')
].copy()

print(f'✓ Filtered dataset:')
print(f'  Rows: {len(df_filtered):,}')
print(f'  Unique companies: {df_filtered["companyid"].nunique()}')
print(f'  Unique events: {df_filtered["transcriptid"].nunique()}')
print()

# ============================================================================
# STEP 2: Aggregate by Event
# ============================================================================
print('=' * 100)
print('STEP 2: AGGREGATE SPEECHES BY EVENT')
print('=' * 100)

print('Grouping by transcriptid (event) and combining speeches...')
print()

# Sort by componentorder to preserve speech order
df_filtered = df_filtered.sort_values(['transcriptid', 'componentorder'])

# Group by transcriptid and aggregate
aggregated_data = []

for transcript_id, group in df_filtered.groupby('transcriptid'):
    # Combine all speeches in order with separators
    combined_text = '\n\n'.join(group['componenttext'].tolist())
    
    # Create aggregated row
    row = {
        # Identifiers
        'companyid': int(group['companyid'].iloc[0]),
        'companyname': group['companyname'].iloc[0],
        'transcriptid': int(transcript_id),
        
        # Event info
        'headline': group['headline'].iloc[0],
        'event_date': group['mostimportantdateutc'].iloc[0],
        'event_time': group['mostimportanttimeutc'].iloc[0],
        'event_type': group['keydeveventtypename'].iloc[0],
        
        # Combined presentation text
        'presentation_text': combined_text,
        
        # Metadata
        'total_word_count': int(group['word_count'].sum()),
        'num_speeches': len(group),
        'speech_word_counts': group['word_count'].tolist(),
        
        # Speaker info
        'speaker_names': group['transcriptpersonname'].unique().tolist(),
        'num_speakers': group['transcriptpersonname'].nunique(),
    }
    
    aggregated_data.append(row)

# Create new DataFrame
df_aggregated = pd.DataFrame(aggregated_data)

print(f'✓ Aggregation complete:')
print(f'  Total events: {len(df_aggregated):,}')
print(f'  Avg speeches per event: {df_aggregated["num_speeches"].mean():.1f}')
print(f'  Avg speakers per event: {df_aggregated["num_speakers"].mean():.1f}')
print(f'  Avg words per event: {df_aggregated["total_word_count"].mean():.0f}')
print()

# ============================================================================
# DATA QUALITY SUMMARY
# ============================================================================
print('=' * 100)
print('DATA QUALITY SUMMARY')
print('=' * 100)

print(f'\nWord count distribution:')
print(f'  Min: {df_aggregated["total_word_count"].min():,} words')
print(f'  25th percentile: {df_aggregated["total_word_count"].quantile(0.25):.0f} words')
print(f'  Median: {df_aggregated["total_word_count"].median():.0f} words')
print(f'  75th percentile: {df_aggregated["total_word_count"].quantile(0.75):.0f} words')
print(f'  Max: {df_aggregated["total_word_count"].max():,} words')

print(f'\nSpeeches per event distribution:')
print(df_aggregated["num_speeches"].value_counts().sort_index().head(10))

print(f'\nSpeakers per event distribution:')
print(df_aggregated["num_speakers"].value_counts().sort_index())

print(f'\nTop 10 companies by number of events:')
company_counts = df_aggregated['companyname'].value_counts().head(10)
for company, count in company_counts.items():
    print(f'  {company}: {count} events')

print()

# ============================================================================
# SAMPLE PREVIEW
# ============================================================================
print('=' * 100)
print('SAMPLE EVENT PREVIEW')
print('=' * 100)

# Show one sample
sample = df_aggregated.iloc[0]

print(f'\nSample Event:')
print(f'  Company: {sample["companyname"]}')
print(f'  Headline: {sample["headline"]}')
print(f'  Date: {sample["event_date"]}')
print(f'  Event Type: {sample["event_type"]}')
print(f'  Number of speeches: {sample["num_speeches"]}')
print(f'  Number of speakers: {sample["num_speakers"]}')
print(f'  Total words: {sample["total_word_count"]:,}')
print(f'  Speakers: {", ".join(sample["speaker_names"])}')

print(f'\n  First 500 characters of combined text:')
print(f'  "{sample["presentation_text"][:500]}..."')

print()

# ============================================================================
# SAVE AGGREGATED DATASET
# ============================================================================
print('=' * 100)
print('SAVING AGGREGATED DATASET')
print('=' * 100)

output_file = 'transcripts_aggregated_for_gpt.pkl'

print(f'Saving to: {output_file}')
with open(output_file, 'wb') as f:
    pickle.dump(df_aggregated, f)

print(f'✓ Saved {len(df_aggregated):,} events')
print()

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print('=' * 100)
print('STEPS 1 & 2 COMPLETE')
print('=' * 100)

print(f'\n✅ Dataset prepared for sentiment analysis:')
print(f'   Input: transcripts_cleaned.pkl ({len(df):,} rows)')
print(f'   Filtered: {len(df_filtered):,} executive presenter speeches')
print(f'   Aggregated: {len(df_aggregated):,} events')
print(f'   Output: {output_file}')

print(f'\n📊 Dataset characteristics:')
print(f'   Companies: {df_aggregated["companyid"].nunique()}')
print(f'   Events: {len(df_aggregated):,}')
print(f'   Avg words per event: {df_aggregated["total_word_count"].mean():.0f}')
print(f'   Avg speeches per event: {df_aggregated["num_speeches"].mean():.1f}')

print(f'\n🎯 Next Steps:')
print(f'   Step 3: GPT Content Filtering ({len(df_aggregated):,} API calls)')
print(f'   Step 4: Sentiment Analysis BEFORE filtering ({len(df_aggregated):,} API calls)')
print(f'   Step 5: Sentiment Analysis AFTER filtering ({len(df_aggregated):,} API calls)')

print(f'\n✓ Completed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 100)
