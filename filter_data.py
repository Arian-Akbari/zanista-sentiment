import pickle
import pandas as pd

with open('transcripts_2024.pkl', 'rb') as f:
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

with open('transcripts_first100.pkl', 'wb') as f:
    pickle.dump(filtered_df, f)

print("\n✓ Saved ALL data for first 100 companies to: transcripts_first100.pkl")
