import pickle
import pandas as pd
from pathlib import Path

# Try multiple locations for input file
input_paths = [
    Path('transcripts_2024.pkl'),
    Path('data/raw/transcripts_2024.pkl')
]

input_file = None
for path in input_paths:
    if path.exists():
        input_file = path
        break

if input_file is None:
    print("❌ ERROR: Raw data file 'transcripts_2024.pkl' not found")
    print("   Searched in:")
    for path in input_paths:
        print(f"     - {path}")
    raise SystemExit(1)

print(f"Loading data from: {input_file}")
with open(input_file, 'rb') as f:
    df = pickle.load(f)

print(f"Original data shape: {df.shape}")

first_100_companies = df['companyid'].unique()[:100]
print(f"First 100 company IDs selected: {len(first_100_companies)}")

filtered_df = df[df['companyid'].isin(first_100_companies)].copy()

print(f"\nFiltered to first 100 companies (ALL data): {filtered_df.shape}")
print(f"\nBreakdown by speaker type:")
print(filtered_df['speakertypename'].value_counts())
print(f"\nBreakdown by component type:")
print(filtered_df['transcriptcomponenttypename'].value_counts())
print(f"\nSample company IDs: {first_100_companies[:5]}")

output_file = 'v2_transcripts_first100.pkl'
with open(output_file, 'wb') as f:
    pickle.dump(filtered_df, f)

print(f"\n✓ Saved ALL data for first 100 companies to: {output_file}")
