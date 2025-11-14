import streamlit as st
import pickle
import pandas as pd

st.set_page_config(page_title="Transcript Data Viewer", layout="wide")

@st.cache_data
def load_data():
    with open('transcripts_first100.pkl', 'rb') as f:
        return pickle.load(f)

df = load_data()

st.title("📊 Earning Call Transcripts - First 100 Companies")

st.sidebar.header("Filters")
companies = sorted(df['companyname'].dropna().unique())
selected_company = st.sidebar.selectbox("Select Company", ["All"] + list(companies))

if selected_company != "All":
    filtered_df = df[df['companyname'] == selected_company]
else:
    filtered_df = df

st.sidebar.metric("Total Records", len(filtered_df))
st.sidebar.metric("Unique Companies", filtered_df['companyid'].nunique())
st.sidebar.metric("Unique Transcripts", filtered_df['transcriptid'].nunique())

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Words", f"{filtered_df['word_count'].sum():,}")
with col2:
    st.metric("Avg Words/Component", f"{filtered_df['word_count'].mean():.0f}")
with col3:
    st.metric("Total Components", len(filtered_df))

st.header("Company Overview")
company_stats = filtered_df.groupby('companyname').agg({
    'transcriptid': 'nunique',
    'componenttext': 'count',
    'word_count': 'sum'
}).reset_index()
company_stats.columns = ['Company', 'Transcripts', 'Components', 'Total Words']
st.dataframe(company_stats, use_container_width=True, height=300)

st.header("Transcript Details")
selected_transcript = st.selectbox(
    "Select Transcript to View",
    filtered_df.groupby(['transcriptid', 'headline'])
    .size().reset_index()[['transcriptid', 'headline']]
    .apply(lambda x: f"{x['headline']} (ID: {int(x['transcriptid'])})", axis=1)
    .tolist()
)

if selected_transcript:
    transcript_id = float(selected_transcript.split("ID: ")[1].split(")")[0])
    transcript_data = filtered_df[filtered_df['transcriptid'] == transcript_id].sort_values('componentorder')
    
    st.subheader(f"📄 {transcript_data.iloc[0]['headline']}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Company:** {transcript_data.iloc[0]['companyname']}")
        st.write(f"**Date:** {transcript_data.iloc[0]['mostimportantdateutc']}")
    with col2:
        st.write(f"**Event Type:** {transcript_data.iloc[0]['keydeveventtypename']}")
        st.write(f"**Components:** {len(transcript_data)}")
    
    st.subheader("Components")
    for idx, row in transcript_data.iterrows():
        with st.expander(f"Component {row['componentorder']} - {row['transcriptpersonname']} ({row['word_count']} words)"):
            st.write(row['componenttext'])

st.header("Raw Data View")
display_cols = ['companyname', 'headline', 'mostimportantdateutc', 'transcriptpersonname', 
                'componentorder', 'word_count', 'componenttextpreview']
st.dataframe(filtered_df[display_cols], use_container_width=True, height=400)

st.header("Check for Duplicates")
if st.button("Analyze Duplicates"):
    duplicate_texts = filtered_df[filtered_df.duplicated(subset=['componenttext'], keep=False)]
    st.metric("Duplicate Component Texts", len(duplicate_texts))
    
    if len(duplicate_texts) > 0:
        st.warning(f"Found {len(duplicate_texts)} duplicate component texts!")
        st.dataframe(
            duplicate_texts[['companyname', 'headline', 'componentorder', 'componenttextpreview']],
            use_container_width=True
        )
