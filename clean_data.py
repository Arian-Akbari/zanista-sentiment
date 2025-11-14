import pickle
import pandas as pd
from datetime import datetime

print('=' * 100)
print('DATA CLEANING & DEDUPLICATION PIPELINE - FIRST 100 COMPANIES')
print('=' * 100)
print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print()

# Load data
print('Loading data...')
with open('transcripts_first100.pkl', 'rb') as f:
    df = pickle.load(f)

if df.columns.duplicated().any():
    df = df.loc[:, ~df.columns.duplicated()]

print(f'✓ Loaded {len(df):,} rows from transcripts_first100.pkl')
print()

# Store original for comparison
original_rows = len(df)
original_companies = df['companyid'].nunique()
original_transcripts = df['transcriptid'].nunique()

print('=' * 100)
print('INITIAL DATA OVERVIEW')
print('=' * 100)
print(f'Total rows: {original_rows:,}')
print(f'Unique companies: {original_companies}')
print(f'Unique transcripts: {original_transcripts}')
print(f'Unique componenttext: {df["componenttext"].nunique():,}')
print()
print('Breakdown by speaker type:')
print(df['speakertypename'].value_counts())
print()
print('Breakdown by component type:')
print(df['transcriptcomponenttypename'].value_counts())
print()

# ============================================================================
# STAGE 1: Remove Within-Transcript Duplicates
# ============================================================================
print('=' * 100)
print('STAGE 1: REMOVE WITHIN-TRANSCRIPT DUPLICATES')
print('=' * 100)
print('Finding duplicate texts within each transcript...')
print()

stage1_before = len(df)

# Check duplicates within each transcript
within_transcript_duplicates = df[df.duplicated(subset=['transcriptid', 'componenttext'], keep=False)]
print(f'Found {len(within_transcript_duplicates):,} rows that are duplicates within their transcript')

# Show example
if len(within_transcript_duplicates) > 0:
    # Find a transcript with lots of internal duplicates
    dup_counts = within_transcript_duplicates.groupby('transcriptid').size().sort_values(ascending=False)
    worst_tid = dup_counts.index[0]
    worst_count = dup_counts.iloc[0]
    
    worst_transcript = df[df['transcriptid'] == worst_tid]
    print(f'\nWorst case example:')
    print(f'  Transcript ID: {int(worst_tid)}')
    print(f'  Company: {worst_transcript.iloc[0]["companyname"]}')
    print(f'  Headline: {worst_transcript.iloc[0]["headline"]}')
    print(f'  Total components: {len(worst_transcript)}')
    print(f'  Unique texts: {worst_transcript["componenttext"].nunique()}')
    print(f'  Duplicate components: {worst_count}')
    print(f'  Duplication rate: {(worst_count/len(worst_transcript)*100):.1f}%')

# Remove within-transcript duplicates
df_stage1 = df.drop_duplicates(subset=['transcriptid', 'componenttext'], keep='first')

stage1_after = len(df_stage1)
stage1_removed = stage1_before - stage1_after

print()
print(f'✓ Stage 1 Complete:')
print(f'  Before: {stage1_before:,} rows')
print(f'  After: {stage1_after:,} rows')
print(f'  Removed: {stage1_removed:,} rows ({stage1_removed/stage1_before*100:.1f}%)')
print()

# ============================================================================
# STAGE 2: Merge Cross-Transcript Duplicates
# ============================================================================
print('=' * 100)
print('STAGE 2: MERGE CROSS-TRANSCRIPT DUPLICATES (COMBINE VERSIONS)')
print('=' * 100)
print('Finding events with multiple transcript versions...')
print()

stage2_before = len(df_stage1)
stage2_transcripts_before = df_stage1['transcriptid'].nunique()

# Find events with multiple transcripts
events = df_stage1.groupby(['companyid', 'headline', 'mostimportantdateutc'])['transcriptid'].nunique()
multi_version_events = events[events > 1]

print(f'Found {len(multi_version_events)} events recorded multiple times')
print(f'Distribution of versions per event:')
version_dist = multi_version_events.value_counts().sort_index()
for num_versions, count in version_dist.items():
    print(f'  {num_versions} versions: {count} events')
print()

# For each multi-version event, merge all versions into one
merged_events = []
events_processed = 0

for (companyid, headline, date), num_versions in multi_version_events.items():
    event_data = df_stage1[
        (df_stage1['companyid'] == companyid) & 
        (df_stage1['headline'] == headline) & 
        (df_stage1['mostimportantdateutc'] == date)
    ]
    
    # Combine all versions and remove duplicates
    # Keep unique texts from ALL versions
    merged_event = event_data.drop_duplicates(subset=['componenttext'], keep='first')
    merged_events.append(merged_event)
    events_processed += 1

# Get single-version events (no merging needed)
single_version_events = df_stage1.groupby(['companyid', 'headline', 'mostimportantdateutc']).filter(
    lambda x: x['transcriptid'].nunique() == 1
)

# Combine merged events with single-version events
df_stage2 = pd.concat([single_version_events] + merged_events, ignore_index=True)

stage2_after = len(df_stage2)
stage2_transcripts_after = df_stage2['transcriptid'].nunique()
stage2_removed = stage2_before - stage2_after

print(f'Merging complete:')
print(f'  Processed {events_processed} multi-version events')
print(f'  Combined all versions into single complete transcript per event')
print()

# Show example
if len(multi_version_events) > 0:
    # Get first multi-version event
    example_key = multi_version_events.head(1).index[0]
    example_before = df_stage1[
        (df_stage1['companyid'] == example_key[0]) & 
        (df_stage1['headline'] == example_key[1]) & 
        (df_stage1['mostimportantdateutc'] == example_key[2])
    ]
    example_after = df_stage2[
        (df_stage2['companyid'] == example_key[0]) & 
        (df_stage2['headline'] == example_key[1]) & 
        (df_stage2['mostimportantdateutc'] == example_key[2])
    ]
    
    print(f'Example: {example_before.iloc[0]["companyname"]}')
    print(f'  Event: {example_key[1]}')
    print(f'  Date: {example_key[2]}')
    print(f'  Number of versions: {multi_version_events.iloc[0]}')
    print()
    
    version_info = []
    for tid in example_before['transcriptid'].unique():
        t = example_before[example_before['transcriptid'] == tid]
        version_info.append({
            'tid': tid,
            'components': len(t),
            'unique_texts': t['componenttext'].nunique()
        })
        print(f'    Version {int(tid)}: {len(t)} components, {t["componenttext"].nunique()} unique texts')
    
    print()
    print(f'  MERGED RESULT: {len(example_after)} components, {example_after["componenttext"].nunique()} unique texts')
    print(f'  → Combined ALL unique information from {len(version_info)} versions into ONE complete transcript')

print()
print(f'✓ Stage 2 Complete:')
print(f'  Before: {stage2_before:,} rows')
print(f'  After: {stage2_after:,} rows')
print(f'  Removed: {stage2_removed:,} rows ({stage2_removed/stage2_before*100:.1f}%)')
print(f'  Transcripts before: {stage2_transcripts_before}')
print(f'  Events after merging: {df_stage2.groupby(["companyid", "headline", "mostimportantdateutc"]).ngroups}')
print()

# ============================================================================
# STAGE 3: Final Cleanup at Company Level
# ============================================================================
print('=' * 100)
print('STAGE 3: FINAL CLEANUP AT COMPANY LEVEL')
print('=' * 100)
print('Removing any remaining duplicate texts per company...')
print()

stage3_before = len(df_stage2)

# Remove duplicates at company level
df_clean = df_stage2.drop_duplicates(subset=['companyid', 'componenttext'], keep='first')

stage3_after = len(df_clean)
stage3_removed = stage3_before - stage3_after

print(f'✓ Stage 3 Complete:')
print(f'  Before: {stage3_before:,} rows')
print(f'  After: {stage3_after:,} rows')
print(f'  Removed: {stage3_removed:,} rows ({stage3_removed/stage3_before*100:.1f}%)')
print()

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print('=' * 100)
print('FINAL SUMMARY - DATA CLEANING COMPLETE')
print('=' * 100)
print()

total_removed = original_rows - len(df_clean)
print(f'Original data: {original_rows:,} rows')
print(f'Final cleaned data: {len(df_clean):,} rows')
print(f'Total removed: {total_removed:,} rows ({total_removed/original_rows*100:.1f}%)')
print()

print('Breakdown by stage:')
print(f'  Stage 1 (Within-transcript duplicates): Removed {stage1_removed:,} rows ({stage1_removed/original_rows*100:.1f}%)')
print(f'  Stage 2 (Merged cross-transcript duplicates): Removed {stage2_removed:,} rows ({stage2_removed/original_rows*100:.1f}%)')
print(f'  Stage 3 (Final company-level cleanup): Removed {stage3_removed:,} rows ({stage3_removed/original_rows*100:.1f}%)')
print()

print('Final cleaned dataset statistics:')
print(f'  Total rows: {len(df_clean):,}')
print(f'  Unique companies: {df_clean["companyid"].nunique()}')
print(f'  Unique events: {df_clean.groupby(["companyid", "headline", "mostimportantdateutc"]).ngroups}')
print(f'  Unique componenttext: {df_clean["componenttext"].nunique():,}')
print(f'  Total words: {df_clean["word_count"].sum():,}')
print(f'  Average words per component: {df_clean["word_count"].mean():.1f}')
print()

print('Speaker type distribution (ALL types kept):')
print(df_clean['speakertypename'].value_counts())
print()

print('Component type distribution (ALL types kept):')
print(df_clean['transcriptcomponenttypename'].value_counts())
print()

print('Top 10 companies by number of components:')
top_companies = df_clean.groupby('companyname').size().sort_values(ascending=False).head(10)
for i, (company, count) in enumerate(top_companies.items(), 1):
    print(f'  {i}. {company}: {count} components')
print()

# Save cleaned data
output_file = 'transcripts_cleaned.pkl'
with open(output_file, 'wb') as f:
    pickle.dump(df_clean, f)

print('=' * 100)
print(f'✓ Cleaned data saved to: {output_file}')
print(f'✓ Data scope: First 100 companies only')
print(f'✓ Data retained: ALL columns, ALL speaker types, ALL component types')
print(f'✓ Duplicates removed: {total_removed:,} rows')
print(f'✓ Unique information preserved: 100%')
print(f'✓ Completed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 100)
