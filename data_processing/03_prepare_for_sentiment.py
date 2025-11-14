import pickle
import pandas as pd
from datetime import datetime
from pathlib import Path

VERBOSE = False

def vprint(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)

print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

# STEP 1: Load and Filter Data
input_file = Path('data/processed/transcripts_cleaned.pkl')
if not input_file.exists():
    fallback_file = Path('transcripts_cleaned.pkl')
    if fallback_file.exists():
        print(f"Note: Reading from current directory (legacy location)")
        input_file = fallback_file
    else:
        print(f"ERROR: Input file not found: {input_file}")
        print("Please run 02_clean_data.py first")
        raise SystemExit(1)

print('Loading cleaned dataset...')
with open(input_file, 'rb') as f:
    df = pickle.load(f)

print(f'Loaded {len(df):,} rows')

vprint('Filtering for Executives + Presenter Speech...')

# Filter for target data
df_filtered = df[
    (df['speakertypename'] == 'Executives') &
    (df['transcriptcomponenttypename'] == 'Presenter Speech')
].copy()

print(f'Filtered: {len(df_filtered):,} rows | Companies: {df_filtered["companyid"].nunique()} | Events: {df_filtered["transcriptid"].nunique()}')

# STEP 2: Aggregate by Event
vprint('Aggregating speeches by event...')

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

print(f'Aggregated: {len(df_aggregated):,} events | Avg speeches={df_aggregated["num_speeches"].mean():.1f} | Avg words={df_aggregated["total_word_count"].mean():.0f}')

vprint(f'\nWord count: min={df_aggregated["total_word_count"].min():,} median={df_aggregated["total_word_count"].median():.0f} max={df_aggregated["total_word_count"].max():,}')
vprint(f'Speeches per event distribution:')
vprint(df_aggregated["num_speeches"].value_counts().sort_index().head(10))

vprint('\nSample event preview:')
sample = df_aggregated.iloc[0]
vprint(f'  {sample["companyname"]} - {sample["headline"][:60]}')
vprint(f'  {sample["num_speeches"]} speeches, {sample["total_word_count"]:,} words')

# Save aggregated dataset
output_file = Path('data/processed/transcripts_aggregated_for_gpt.pkl')
output_file.parent.mkdir(parents=True, exist_ok=True)
with open(output_file, 'wb') as f:
    pickle.dump(df_aggregated, f)

print(f'\nSaved {len(df_aggregated):,} events to: {output_file}')
print(f'Companies: {df_aggregated["companyid"].nunique()} | Events: {len(df_aggregated):,} | Avg words/event: {df_aggregated["total_word_count"].mean():.0f}')
print(f'Completed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
