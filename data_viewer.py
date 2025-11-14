import streamlit as st
import pickle
import pandas as pd

st.set_page_config(page_title="Transcript Data Viewer", layout="wide")

@st.cache_data
def load_data():
    with open('transcripts_first100.pkl', 'rb') as f:
        df = pickle.load(f)
    
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    
    return df

df = load_data()

st.title("📊 Earning Call Transcripts - First 100 Companies")

st.sidebar.header("🔍 Filters")
companies = sorted(df['companyname'].dropna().unique())
selected_company = st.sidebar.selectbox("Select Company", ["All"] + list(companies))

speaker_types = ['All'] + sorted(df['speakertypename'].dropna().unique().tolist())
selected_speaker = st.sidebar.selectbox("Speaker Type", speaker_types)

component_types = ['All'] + sorted(df['transcriptcomponenttypename'].dropna().unique().tolist())
selected_component = st.sidebar.selectbox("Component Type", component_types)

filtered_df = df.copy()
if selected_company != "All":
    filtered_df = filtered_df[filtered_df['companyname'] == selected_company]
if selected_speaker != "All":
    filtered_df = filtered_df[filtered_df['speakertypename'] == selected_speaker]
if selected_component != "All":
    filtered_df = filtered_df[filtered_df['transcriptcomponenttypename'] == selected_component]

st.sidebar.markdown("---")
st.sidebar.metric("Total Records", f"{len(filtered_df):,}")
st.sidebar.metric("Unique Companies", int(filtered_df['companyid'].nunique()))
st.sidebar.metric("Unique Transcripts", int(filtered_df['transcriptid'].nunique()))

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📝 Total Words", f"{int(filtered_df['word_count'].sum()):,}")
with col2:
    st.metric("📊 Avg Words/Component", f"{int(filtered_df['word_count'].mean())}")
with col3:
    st.metric("🎤 Total Components", f"{len(filtered_df):,}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Overview", "📄 Transcript Viewer", "🔎 Raw Data Explorer", "📊 Column Info", "🔁 Duplicates"])

with tab1:
    st.header("Company Overview")
    company_stats = filtered_df.groupby('companyname').agg({
        'transcriptid': 'nunique',
        'componenttext': 'count',
        'word_count': 'sum',
        'mostimportantdateutc': lambda x: f"{x.min()} to {x.max()}"
    }).reset_index()
    company_stats.columns = ['Company', 'Transcripts', 'Components', 'Total Words', 'Date Range']
    st.dataframe(company_stats, use_container_width=True, height=400)
    
    st.header("Data Breakdown by Type")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎤 Speaker Types")
        speaker_breakdown = filtered_df['speakertypename'].value_counts().reset_index()
        speaker_breakdown.columns = ['Speaker Type', 'Count']
        speaker_breakdown['Percentage'] = (speaker_breakdown['Count'] / len(filtered_df) * 100).round(2)
        st.dataframe(speaker_breakdown, use_container_width=True)
    with col2:
        st.subheader("💬 Component Types")
        component_breakdown = filtered_df['transcriptcomponenttypename'].value_counts().reset_index()
        component_breakdown.columns = ['Component Type', 'Count']
        component_breakdown['Percentage'] = (component_breakdown['Count'] / len(filtered_df) * 100).round(2)
        st.dataframe(component_breakdown, use_container_width=True)

with tab2:
    st.header("Transcript Viewer")
    
    transcript_options = filtered_df.groupby(['transcriptid', 'headline', 'companyname', 'mostimportantdateutc']).size().reset_index()
    transcript_options['display'] = transcript_options.apply(
        lambda x: f"{x['companyname']} - {x['headline']} ({x['mostimportantdateutc']})", axis=1
    )
    
    selected_transcript_display = st.selectbox(
        "Select Transcript to View",
        transcript_options['display'].tolist()
    )
    
    if selected_transcript_display:
        selected_idx = transcript_options[transcript_options['display'] == selected_transcript_display].index[0]
        transcript_id = transcript_options.iloc[selected_idx]['transcriptid']
        transcript_data = filtered_df[filtered_df['transcriptid'] == transcript_id].sort_values('componentorder')
        
        st.subheader(f"📄 {transcript_data.iloc[0]['headline']}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Company:** {transcript_data.iloc[0]['companyname']}")
            st.write(f"**Company ID:** {int(transcript_data.iloc[0]['companyid'])}")
        with col2:
            st.write(f"**Date:** {transcript_data.iloc[0]['mostimportantdateutc']}")
            st.write(f"**Time:** {transcript_data.iloc[0]['mostimportanttimeutc']}")
        with col3:
            st.write(f"**Event Type:** {transcript_data.iloc[0]['keydeveventtypename']}")
            st.write(f"**Components:** {len(transcript_data)}")
        
        st.markdown("---")
        st.subheader("📝 Full Transcript (in order)")
        
        for idx, row in transcript_data.iterrows():
            speaker_emoji = "👔" if row['speakertypename'] == "Executives" else "📊" if row['speakertypename'] == "Analysts" else "📢"
            with st.expander(
                f"{speaker_emoji} Component #{row['componentorder']} - {row['transcriptpersonname']} "
                f"({row['speakertypename']}, {row['transcriptcomponenttypename']}, {row['word_count']} words)",
                expanded=False
            ):
                st.markdown(f"**Speaker:** {row['transcriptpersonname']}")
                st.markdown(f"**Type:** {row['speakertypename']} - {row['transcriptcomponenttypename']}")
                st.markdown(f"**Word Count:** {row['word_count']}")
                st.markdown("**Full Text:**")
                st.text_area("", row['componenttext'], height=200, key=f"text_{idx}", label_visibility="collapsed")

with tab3:
    st.header("Raw Data Explorer")
    
    st.subheader("🔧 Customize Columns to Display")
    all_columns = df.columns.tolist()
    default_cols = ['companyname', 'headline', 'mostimportantdateutc', 'speakertypename', 
                    'transcriptcomponenttypename', 'transcriptpersonname', 'componentorder', 
                    'word_count', 'componenttextpreview']
    
    selected_columns = st.multiselect(
        "Select columns to display",
        all_columns,
        default=default_cols
    )
    
    if selected_columns:
        st.dataframe(filtered_df[selected_columns], use_container_width=True, height=500)
        
        st.download_button(
            label="⬇️ Download Filtered Data as CSV",
            data=filtered_df[selected_columns].to_csv(index=False),
            file_name="filtered_transcripts.csv",
            mime="text/csv"
        )
    
    st.subheader("🔍 Detailed Row Viewer")
    row_num = st.number_input("Enter row number to view details", min_value=0, max_value=len(filtered_df)-1, value=0)
    
    if row_num is not None:
        row_data = filtered_df.iloc[row_num]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏢 Company Information")
            st.write(f"**Company Name:** {row_data['companyname']}")
            st.write(f"**Company ID:** {row_data['companyid']}")
            st.write(f"**Company of Person:** {row_data['companyofperson']}")
            
            st.markdown("### 📅 Event Information")
            st.write(f"**Headline:** {row_data['headline']}")
            st.write(f"**Event Type:** {row_data['keydeveventtypename']}")
            st.write(f"**Date:** {row_data['mostimportantdateutc']}")
            st.write(f"**Time:** {row_data['mostimportanttimeutc']}")
            
            st.markdown("### 🎤 Speaker Information")
            st.write(f"**Person Name:** {row_data['transcriptpersonname']}")
            st.write(f"**Speaker Type:** {row_data['speakertypename']}")
            st.write(f"**Person ID:** {row_data['transcriptpersonid']}")
        
        with col2:
            st.markdown("### 📄 Transcript Information")
            st.write(f"**Transcript ID:** {row_data['transcriptid']}")
            st.write(f"**Collection Type:** {row_data['transcriptcollectiontypename']}")
            st.write(f"**Presentation Type:** {row_data['transcriptpresentationtypename']}")
            st.write(f"**Creation Date:** {row_data['transcriptcreationdate_utc']}")
            st.write(f"**Audio Length (sec):** {row_data['audiolengthsec']}")
            
            st.markdown("### 💬 Component Information")
            st.write(f"**Component Order:** {row_data['componentorder']}")
            st.write(f"**Component Type:** {row_data['transcriptcomponenttypename']}")
            st.write(f"**Word Count:** {row_data['word_count']}")
        
        st.markdown("### 📝 Full Component Text")
        st.text_area("", row_data['componenttext'], height=300, key="detailed_text", label_visibility="collapsed")

with tab4:
    st.header("📊 Column Definitions")
    
    column_info = {
        "companyid": "Unique identifier for the company",
        "companyname": "Name of the company",
        "keydevid": "Key development event ID",
        "keydeveventtypename": "Type of event (e.g., Earnings Call, Special Call)",
        "transcriptid": "Unique identifier for the transcript/earning call session",
        "headline": "Title/headline of the earning call",
        "mostimportantdateutc": "Date of the earning call (UTC)",
        "mostimportanttimeutc": "Time of the earning call (UTC)",
        "transcriptcreationdate_utc": "When the transcript was created",
        "transcriptcreationtime_utc": "Time when transcript was created",
        "audiolengthsec": "Total length of the call in seconds",
        "transcriptcollectiontypename": "How transcript was collected",
        "transcriptpresentationtypename": "Type of presentation format",
        "transcriptcomponentid": "Unique ID for this specific speech component",
        "componentorder": "⭐ Order of this speech in the call (1, 2, 3...) - CRITICAL for preserving conversation flow",
        "transcriptcomponenttypename": "⭐ Type of speech: Presenter Speech, Answer, Question, Operator Message",
        "transcriptpersonid": "Unique ID for the person speaking",
        "transcriptpersonname": "Name of the person speaking",
        "speakertypeid": "ID for speaker category",
        "speakertypename": "⭐ Category of speaker: Executives, Analysts, Operator, etc.",
        "companyofperson": "Company affiliation of the speaker",
        "componenttextpreview": "Short preview of the text (first ~100 chars)",
        "word_count": "Number of words in this component",
        "componenttext": "⭐ MOST IMPORTANT - The actual full text spoken by the person",
        "proid": "Professional ID (may be related to speaker)"
    }
    
    col_df = pd.DataFrame([
        {"Column Name": col, "Description": desc, "Data Type": str(df[col].dtype)}
        for col, desc in column_info.items()
    ])
    
    st.dataframe(col_df, use_container_width=True, height=600)
    
    st.info("⭐ = Critical columns for your analysis task")

with tab5:
    st.header("🔁 Duplicate Analysis")
    
    if st.button("🔍 Analyze Duplicates in Filtered Data"):
        duplicate_texts = filtered_df[filtered_df.duplicated(subset=['componenttext'], keep=False)]
        st.metric("Duplicate Component Texts Found", len(duplicate_texts))
        
        if len(duplicate_texts) > 0:
            st.warning(f"⚠️ Found {len(duplicate_texts)} duplicate component texts!")
            
            dup_groups = duplicate_texts.groupby('componenttext').size().reset_index(name='count')
            dup_groups = dup_groups.sort_values('count', ascending=False)
            
            st.subheader(f"Found {len(dup_groups)} unique texts that are duplicated")
            st.dataframe(dup_groups, use_container_width=True)
            
            st.subheader("Duplicate Records Details")
            st.dataframe(
                duplicate_texts[['companyname', 'headline', 'mostimportantdateutc', 
                                'speakertypename', 'transcriptpersonname', 'componentorder', 
                                'componenttextpreview']].sort_values('componenttext'),
                use_container_width=True,
                height=400
            )
        else:
            st.success("✅ No duplicates found in current filtered data!")
