import pickle
import pandas as pd
from datetime import datetime
from pathlib import Path

VERBOSE = False

def vprint(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)

print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

# Load data
input_file = Path('transcripts_first100.pkl')
if not input_file.exists():
    print(f"ERROR: Input file not found: {input_file}")
    print("Please run 01_filter_companies.py first")
    raise SystemExit(1)

print('Loading data...')
with open('transcripts_first100.pkl', 'rb') as f:
    df = pickle.load(f)

if df.columns.duplicated().any():
    df = df.loc[:, ~df.columns.duplicated()]

print(f'Loaded {len(df):,} rows from transcripts_first100.pkl')

# Store original for comparison
original_rows = len(df)
original_companies = df['companyid'].nunique()
original_transcripts = df['transcriptid'].nunique()

vprint(f'Total rows: {original_rows:,}')
vprint(f'Unique companies: {original_companies}')
vprint(f'Unique transcripts: {original_transcripts}')
vprint(f'Unique componenttext: {df["componenttext"].nunique():,}')

# STAGE 1: Remove Within-Transcript Duplicates
vprint('STAGE 1: REMOVE WITHIN-TRANSCRIPT DUPLICATES')

stage1_before = len(df)

# Check duplicates within each transcript
within_transcript_duplicates = df[df.duplicated(subset=['transcriptid', 'componenttext'], keep=False)]
vprint(f'Found {len(within_transcript_duplicates):,} rows that are duplicates within their transcript')

# Remove within-transcript duplicates
df_stage1 = df.drop_duplicates(subset=['transcriptid', 'componenttext'], keep='first').copy()

stage1_after = len(df_stage1)
stage1_removed = stage1_before - stage1_after

print(f'Stage 1: Before={stage1_before:,} After={stage1_after:,} Removed={stage1_removed:,} ({stage1_removed/stage1_before*100:.1f}%)')

# STAGE 2: Merge Cross-Transcript Duplicates
vprint('STAGE 2: MERGE CROSS-TRANSCRIPT DUPLICATES')

stage2_before = len(df_stage1)
stage2_transcripts_before = df_stage1['transcriptid'].nunique()

# Create event identifier
df_stage1['event_id'] = (
    df_stage1['companyid'].astype(str) + '|' + 
    df_stage1['headline'].astype(str) + '|' + 
    df_stage1['mostimportantdateutc'].astype(str)
)

# Find events with multiple transcripts
event_transcript_counts = df_stage1.groupby('event_id')['transcriptid'].nunique()
multi_version_events = event_transcript_counts[event_transcript_counts > 1]

vprint(f'Found {len(multi_version_events)} events recorded multiple times')
vprint(f'Distribution of versions per event:')
version_dist = multi_version_events.value_counts().sort_index()
for num_versions, count in version_dist.items():
    vprint(f'  {num_versions} versions: {count} events')

# For each multi-version event, merge all versions and assign SINGLE transcript ID
merged_data = []
merge_count = 0

for event_id in multi_version_events.index:
    event_data = df_stage1[df_stage1['event_id'] == event_id].copy()
    
    # CRITICAL FIX: Merge all versions and deduplicate by componenttext
    merged_event = event_data.drop_duplicates(subset=['componenttext'], keep='first').copy()
    
    # CRITICAL FIX: Assign a SINGLE unified transcript ID (use the first one)
    unified_transcript_id = merged_event['transcriptid'].iloc[0]
    merged_event['transcriptid'] = unified_transcript_id
    
    merged_data.append(merged_event)
    merge_count += 1

# Get single-version events (no merging needed)
single_version_event_ids = event_transcript_counts[event_transcript_counts == 1].index
single_version_events = df_stage1[df_stage1['event_id'].isin(single_version_event_ids)]

# Combine merged events with single-version events
df_stage2 = pd.concat([single_version_events] + merged_data, ignore_index=True)

# Drop temporary event_id column
df_stage2 = df_stage2.drop(columns=['event_id'])

stage2_after = len(df_stage2)
stage2_transcripts_after = df_stage2['transcriptid'].nunique()
stage2_removed = stage2_before - stage2_after

vprint(f'Merging complete: Processed {merge_count} multi-version events')

print(f'Stage 2: Before={stage2_before:,} After={stage2_after:,} Removed={stage2_removed:,} ({stage2_removed/stage2_before*100:.1f}%) Transcripts={stage2_transcripts_after}')

# STAGE 3: Final Cleanup at Company Level
vprint('STAGE 3: FINAL CLEANUP AT COMPANY LEVEL')

stage3_before = len(df_stage2)

# Remove duplicates at company level
df_clean = df_stage2.drop_duplicates(subset=['companyid', 'componenttext'], keep='first')

stage3_after = len(df_clean)
stage3_removed = stage3_before - stage3_after

print(f'Stage 3: Before={stage3_before:,} After={stage3_after:,} Removed={stage3_removed:,} ({stage3_removed/stage3_before*100:.1f}%)')

# Verification: Check merge success
df_clean_check = df_clean.copy()
df_clean_check['event_id'] = (
    df_clean_check['companyid'].astype(str) + '|' + 
    df_clean_check['headline'].astype(str) + '|' + 
    df_clean_check['mostimportantdateutc'].astype(str)
)

final_event_transcript_counts = df_clean_check.groupby('event_id')['transcriptid'].nunique()
still_multi = final_event_transcript_counts[final_event_transcript_counts > 1]

if len(still_multi) > 0:
    print(f'WARNING: {len(still_multi)} events still have multiple transcript IDs!')
else:
    vprint('SUCCESS: All events have single transcript ID')

df_clean = df_clean.drop(columns=['event_id'] if 'event_id' in df_clean.columns else [])

# Final Summary
total_removed = original_rows - len(df_clean)
print(f'\nCleaning complete: {original_rows:,} → {len(df_clean):,} rows ({total_removed:,} removed, {total_removed/original_rows*100:.1f}%)')
print(f'Unique companies: {df_clean["companyid"].nunique()} | Unique events: {df_clean.groupby(["companyid", "headline", "mostimportantdateutc"]).ngroups}')
print(f'Total words: {df_clean["word_count"].sum():,} | Avg per component: {df_clean["word_count"].mean():.1f}')

vprint('\nSpeaker type distribution:')
vprint(df_clean['speakertypename'].value_counts())
vprint('\nComponent type distribution:')
vprint(df_clean['transcriptcomponenttypename'].value_counts())

# Save cleaned data
output_file = Path('data/processed/transcripts_cleaned.pkl')
output_file.parent.mkdir(parents=True, exist_ok=True)
with open(output_file, 'wb') as f:
    pickle.dump(df_clean, f)

print(f'\nSaved to: {output_file}')
print(f'Completed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
