import streamlit as st
import pickle
import pandas as pd

st.set_page_config(page_title="Transcript Data Viewer", layout="wide")

@st.cache_data
def load_data():
    with open('transcripts_cleaned.pkl', 'rb') as f:
        df = pickle.load(f)
    
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    
    return df

df = load_data()

st.title("📊 Earning Call Transcripts - First 100 Companies (CLEANED DATA)")

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
        
        # Check for duplicates in this specific transcript
        transcript_duplicates = transcript_data[transcript_data.duplicated(subset=['componenttext'], keep=False)]
        if len(transcript_duplicates) > 0:
            st.warning(f"⚠️ {len(transcript_duplicates)} duplicate components found in this transcript!")
        else:
            st.success("✅ No duplicates in this transcript")
        
        st.markdown("---")
        st.subheader("📝 Full Transcript (in order)")
        
        for idx, row in transcript_data.iterrows():
            speaker_emoji = "👔" if row['speakertypename'] == "Executives" else "📊" if row['speakertypename'] == "Analysts" else "📢"
            
            # Check if this specific component is duplicated
            is_duplicate = len(transcript_data[transcript_data['componenttext'] == row['componenttext']]) > 1
            duplicate_badge = " 🔁 DUPLICATE" if is_duplicate else ""
            
            with st.expander(
                f"{speaker_emoji} Component #{row['componentorder']} - {row['transcriptpersonname']} "
                f"({row['speakertypename']}, {row['transcriptcomponenttypename']}, {row['word_count']} words){duplicate_badge}",
                expanded=False
            ):
                st.markdown(f"**Speaker:** {row['transcriptpersonname']}")
                st.markdown(f"**Type:** {row['speakertypename']} - {row['transcriptcomponenttypename']}")
                st.markdown(f"**Word Count:** {row['word_count']}")
                if is_duplicate:
                    st.error("⚠️ This exact text appears multiple times in this transcript!")
                st.markdown("**Full Text:**")
                st.text_area("", row['componenttext'], height=200, key=f"text_{idx}", label_visibility="collapsed")

with tab3:
    st.header("🔎 Raw Data Explorer")
    
    st.info("📌 Showing ALL columns in logical order for maximum understanding. Use sidebar filters to narrow down data.")
    
    # Define optimal column order for understanding
    ordered_columns = [
        # 🏢 Company Information
        'companyid',
        'companyname',
        
        # 📅 Event Information  
        'keydevid',
        'keydeveventtypename',
        'headline',
        'mostimportantdateutc',
        'mostimportanttimeutc',
        
        # 📄 Transcript Information
        'transcriptid',
        'transcriptcollectiontypeid',
        'transcriptcollectiontypename',
        'transcriptpresentationtypeid',
        'transcriptpresentationtypename',
        'transcriptcreationdate_utc',
        'transcriptcreationtime_utc',
        'audiolengthsec',
        
        # 💬 Component Information
        'transcriptcomponentid',
        'componentorder',
        'transcriptcomponenttypeid',
        'transcriptcomponenttypename',
        
        # 🎤 Speaker Information
        'transcriptpersonid',
        'transcriptpersonname',
        'speakertypeid',
        'speakertypename',
        'companyofperson',
        'proid',
        
        # 📝 Text Content
        'componenttextpreview',
        'word_count',
        'componenttext'
    ]
    
    st.subheader("📊 Complete Data Table")
    st.caption("All 29 columns displayed in logical order: Company → Event → Transcript → Component → Speaker → Text")
    
    st.dataframe(filtered_df[ordered_columns], use_container_width=True, height=500)
    
    st.download_button(
        label="⬇️ Download Filtered Data as CSV",
        data=filtered_df[ordered_columns].to_csv(index=False),
        file_name="filtered_transcripts.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    st.subheader("🔍 Detailed Row Inspector")
    st.caption("Select any row number to see ALL fields with explanations and duplicate detection")
    
    row_num = st.number_input("Enter row number to inspect", min_value=0, max_value=len(filtered_df)-1, value=0)
    
    if row_num is not None:
        row_data = filtered_df.iloc[row_num]
        
        # Check if this component text is duplicated
        component_duplicates = df[df['componenttext'] == row_data['componenttext']]
        is_duplicate = len(component_duplicates) > 1
        
        if is_duplicate:
            st.error(f"🔁 DUPLICATE DETECTED: This exact text appears {len(component_duplicates)} times in the dataset!")
            st.caption("See 'Duplicate Details' section below for all occurrences")
        else:
            st.success("✅ This component text is unique in the dataset")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏢 Company Information")
            st.write(f"**Company ID:** {row_data['companyid']}")
            st.write(f"**Company Name:** {row_data['companyname']}")
            st.write(f"**Company of Person:** {row_data['companyofperson']}")
            
            st.markdown("---")
            st.markdown("### 📅 Event Information")
            st.write(f"**Key Dev ID:** {row_data['keydevid']}")
            st.write(f"**Event Type:** {row_data['keydeveventtypename']}")
            st.write(f"**Headline:** {row_data['headline']}")
            st.write(f"**Date (UTC):** {row_data['mostimportantdateutc']}")
            st.write(f"**Time (UTC):** {row_data['mostimportanttimeutc']}")
            
            st.markdown("---")
            st.markdown("### 📄 Transcript Information")
            st.write(f"**Transcript ID:** {row_data['transcriptid']}")
            st.write(f"**Collection Type ID:** {row_data['transcriptcollectiontypeid']}")
            st.write(f"**Collection Type:** {row_data['transcriptcollectiontypename']}")
            st.write(f"**Presentation Type ID:** {row_data['transcriptpresentationtypeid']}")
            st.write(f"**Presentation Type:** {row_data['transcriptpresentationtypename']}")
            st.write(f"**Creation Date (UTC):** {row_data['transcriptcreationdate_utc']}")
            st.write(f"**Creation Time (UTC):** {row_data['transcriptcreationtime_utc']}")
            st.write(f"**Audio Length (seconds):** {row_data['audiolengthsec']}")
        
        with col2:
            st.markdown("### 💬 Component Information")
            st.write(f"**Component ID:** {row_data['transcriptcomponentid']}")
            st.write(f"**Component Order:** ⭐ {row_data['componentorder']} (position in conversation)")
            st.write(f"**Component Type ID:** {row_data['transcriptcomponenttypeid']}")
            st.write(f"**Component Type:** ⭐ {row_data['transcriptcomponenttypename']}")
            
            st.markdown("---")
            st.markdown("### 🎤 Speaker Information")
            st.write(f"**Person ID:** {row_data['transcriptpersonid']}")
            st.write(f"**Person Name:** {row_data['transcriptpersonname']}")
            st.write(f"**Speaker Type ID:** {row_data['speakertypeid']}")
            st.write(f"**Speaker Type:** ⭐ {row_data['speakertypename']}")
            st.write(f"**Pro ID:** {row_data['proid']}")
            
            st.markdown("---")
            st.markdown("### 📝 Text Content Metadata")
            st.write(f"**Word Count:** {row_data['word_count']} words")
            st.write(f"**Text Preview:** {row_data['componenttextpreview']}")
        
        st.markdown("---")
        st.markdown("### 📝 Full Component Text (What Was Actually Said)")
        st.text_area("", row_data['componenttext'], height=300, key="detailed_text", label_visibility="collapsed")
        
        # Show duplicate details if this is a duplicate
        if is_duplicate:
            st.markdown("---")
            st.markdown("### 🔁 Duplicate Details")
            st.warning(f"This exact text appears in {len(component_duplicates)} places:")
            
            dup_display = component_duplicates[['companyname', 'headline', 'mostimportantdateutc', 
                                                 'transcriptid', 'componentorder', 'speakertypename', 
                                                 'transcriptpersonname']].copy()
            dup_display['transcriptid'] = dup_display['transcriptid'].astype(int)
            dup_display['componentorder'] = dup_display['componentorder'].astype(int)
            
            st.dataframe(dup_display, use_container_width=True)
            
            # Analyze why it's duplicated
            same_transcript = component_duplicates['transcriptid'].nunique() == 1
            same_company = component_duplicates['companyid'].nunique() == 1
            
            if same_transcript:
                st.info("ℹ️ **Duplicate Type:** Same text appears multiple times in the SAME transcript (unusual - may indicate data error)")
            elif same_company:
                st.info("ℹ️ **Duplicate Type:** Same company, different transcripts (likely same event recorded multiple times)")
            else:
                st.info("ℹ️ **Duplicate Type:** Different companies (unusual - may be template/boilerplate text)")

with tab4:
    st.header("📊 Column Definitions")
    
    column_info = {
        "companyid": ("🏢 Company", "Unique identifier for the company"),
        "companyname": ("🏢 Company", "Name of the company"),
        "keydevid": ("📅 Event", "Key development event ID"),
        "keydeveventtypename": ("📅 Event", "Type of event (e.g., Earnings Call, Special Call)"),
        "headline": ("📅 Event", "Title/headline of the earning call"),
        "mostimportantdateutc": ("📅 Event", "Date of the earning call (UTC)"),
        "mostimportanttimeutc": ("📅 Event", "Time of the earning call (UTC)"),
        "transcriptid": ("📄 Transcript", "⭐ Unique ID for each earning call session - same ID = same call"),
        "transcriptcollectiontypeid": ("📄 Transcript", "ID for collection type"),
        "transcriptcollectiontypename": ("📄 Transcript", "How transcript was collected"),
        "transcriptpresentationtypeid": ("📄 Transcript", "ID for presentation type"),
        "transcriptpresentationtypename": ("📄 Transcript", "Type of presentation format"),
        "transcriptcreationdate_utc": ("📄 Transcript", "When the transcript was created"),
        "transcriptcreationtime_utc": ("📄 Transcript", "Time when transcript was created"),
        "audiolengthsec": ("📄 Transcript", "Total length of the call in seconds"),
        "transcriptcomponentid": ("💬 Component", "Unique ID for this specific speech component"),
        "componentorder": ("💬 Component", "⭐ Order in conversation (0,1,2...) - CRITICAL for preserving flow"),
        "transcriptcomponenttypeid": ("💬 Component", "ID for component type"),
        "transcriptcomponenttypename": ("💬 Component", "⭐ Type: Presenter Speech, Answer, Question, Operator Message"),
        "transcriptpersonid": ("🎤 Speaker", "Unique ID for the person speaking"),
        "transcriptpersonname": ("🎤 Speaker", "Name of the person speaking"),
        "speakertypeid": ("🎤 Speaker", "ID for speaker category"),
        "speakertypename": ("🎤 Speaker", "⭐ Category: Executives, Analysts, Operator, etc."),
        "companyofperson": ("🎤 Speaker", "Company affiliation of the speaker"),
        "proid": ("🎤 Speaker", "Professional ID (additional identifier)"),
        "componenttextpreview": ("📝 Text", "Short preview of the text (~100 chars)"),
        "word_count": ("📝 Text", "Number of words in this component"),
        "componenttext": ("📝 Text", "⭐⭐⭐ MOST CRITICAL - The actual full text spoken")
    }
    
    col_df = pd.DataFrame([
        {
            "Category": cat,
            "Column Name": col, 
            "Description": desc, 
            "Data Type": str(df[col].dtype)
        }
        for col, (cat, desc) in column_info.items()
    ])
    
    st.dataframe(col_df, use_container_width=True, height=700)
    
    st.info("⭐ = Important for analysis | ⭐⭐⭐ = Most critical column")

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
