import streamlit as st
import pickle
import pandas as pd
import os

st.set_page_config(page_title="Transcript Data Viewer", layout="wide")

@st.cache_data
def load_data():
    # Get the path to the data file (works from any directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, '..', 'data', 'processed', 'transcripts_cleaned.pkl')

    with open(file_path, 'rb') as f:
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

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📋 Overview", "📄 Transcript Viewer", "🔎 Raw Data Explorer", "📊 Column Info", "🔁 Duplicates", "🏷️ Labeled Data"])

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
    
    # Create unique event list (one per company+headline+date combination)
    event_options = filtered_df.groupby(['companyname', 'headline', 'mostimportantdateutc']).agg({
        'transcriptid': 'first'  # Just take the first transcript ID (they should be unified now)
    }).reset_index()
    event_options['display'] = event_options.apply(
        lambda x: f"{x['companyname']} - {x['headline']} ({x['mostimportantdateutc']})", axis=1
    )
    
    selected_event_display = st.selectbox(
        "Select Event to View",
        event_options['display'].tolist()
    )
    
    if selected_event_display:
        selected_idx = event_options[event_options['display'] == selected_event_display].index[0]
        selected_company = event_options.iloc[selected_idx]['companyname']
        selected_headline = event_options.iloc[selected_idx]['headline']
        selected_date = event_options.iloc[selected_idx]['mostimportantdateutc']
        
        # Get all data for this event (should be under single transcript ID now)
        transcript_data = filtered_df[
            (filtered_df['companyname'] == selected_company) &
            (filtered_df['headline'] == selected_headline) &
            (filtered_df['mostimportantdateutc'] == selected_date)
        ].sort_values('componentorder')
        
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

with tab6:
    st.header("🏷️ Labeled Data Viewer")
    st.caption("Browse and compare AI-generated vs Human-labeled sentiment classifications")

    # Find and load labeled data files
    labeled_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'labeled')

    # Get list of labeled files
    labeled_files = []
    if os.path.exists(labeled_dir):
        for file in os.listdir(labeled_dir):
            if file.endswith('_labeled.pkl'):
                labeled_files.append(file)

    if not labeled_files:
        st.warning("⚠️ No labeled data files found. Please run the labeling process first.")
    else:
        labeled_files.sort()

        # Select which labeled dataset to view
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_labeled_file = st.selectbox(
                "Select Labeled Dataset",
                labeled_files,
                format_func=lambda x: x.replace('sample_20_labeled_', '').replace('.pkl', '').replace('_', ' ').title()
            )

        # Load selected labeled data
        @st.cache_data
        def load_labeled_data(filename):
            file_path = os.path.join(labeled_dir, filename)
            with open(file_path, 'rb') as f:
                return pickle.load(f)

        labeled_df = load_labeled_data(selected_labeled_file)

        # Initialize session state for labeled data navigation
        if 'labeled_current_idx' not in st.session_state:
            st.session_state.labeled_current_idx = 0
        if 'labeled_filter' not in st.session_state:
            st.session_state.labeled_filter = 'All'

        # Apply filter if any
        if st.session_state.labeled_filter != 'All':
            filtered_labeled_df = labeled_df[labeled_df['user_sentiment'] == st.session_state.labeled_filter].reset_index(drop=True)
        else:
            filtered_labeled_df = labeled_df.reset_index(drop=True)

        # Calculate statistics
        total_labeled = len(labeled_df)
        positive_count = (labeled_df['user_sentiment'] == 'positive').sum()
        negative_count = (labeled_df['user_sentiment'] == 'negative').sum()
        neutral_count = (labeled_df['user_sentiment'] == 'neutral').sum()
        agreement_count = (labeled_df['user_sentiment'] == labeled_df['ai_sentiment']).sum()
        agreement_rate = (agreement_count / total_labeled * 100) if total_labeled > 0 else 0
        changed_count = labeled_df['label_changed'].sum()

        # Display statistics
        st.markdown("### 📊 Statistics")
        stat_col1, stat_col2, stat_col3, stat_col4, stat_col5, stat_col6 = st.columns(6)

        with stat_col1:
            st.metric("📌 Total", total_labeled)
        with stat_col2:
            st.metric("✅ Positive", f"{positive_count} ({positive_count/total_labeled*100:.0f}%)")
        with stat_col3:
            st.metric("❌ Negative", f"{negative_count} ({negative_count/total_labeled*100:.0f}%)")
        with stat_col4:
            st.metric("⚪ Neutral", f"{neutral_count} ({neutral_count/total_labeled*100:.0f}%)")
        with stat_col5:
            st.metric("🤝 Agreement", f"{agreement_count}/{total_labeled} ({agreement_rate:.0f}%)")
        with stat_col6:
            st.metric("🔄 Changed", changed_count)

        st.markdown("---")

        # Filter options
        st.markdown("### 🔍 Filter")
        filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 2])
        with filter_col1:
            st.session_state.labeled_filter = st.selectbox(
                "Show sentiment",
                ['All', 'positive', 'negative', 'neutral'],
                key="labeled_sentiment_filter"
            )
        with filter_col2:
            show_disagreements = st.checkbox("Show only disagreements", value=False)
            if show_disagreements:
                filtered_labeled_df = filtered_labeled_df[filtered_labeled_df['label_changed'] == True]

        st.markdown("---")

        # Navigation and display
        if len(filtered_labeled_df) > 0:
            # Reset index if needed
            if st.session_state.labeled_current_idx >= len(filtered_labeled_df):
                st.session_state.labeled_current_idx = 0

            idx = st.session_state.labeled_current_idx
            row = filtered_labeled_df.iloc[idx]

            # Header with navigation
            nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 2, 1, 1])
            with nav_col1:
                if st.button("⬅️ Previous", use_container_width=True):
                    if st.session_state.labeled_current_idx > 0:
                        st.session_state.labeled_current_idx -= 1
                        st.rerun()
            with nav_col2:
                st.markdown(f"### 📍 Event {idx + 1} of {len(filtered_labeled_df)}")
            with nav_col3:
                if st.button("Next ➡️", use_container_width=True):
                    if st.session_state.labeled_current_idx < len(filtered_labeled_df) - 1:
                        st.session_state.labeled_current_idx += 1
                        st.rerun()
            with nav_col4:
                jump_to = st.number_input(
                    "Jump to",
                    min_value=1,
                    max_value=len(filtered_labeled_df),
                    value=idx + 1,
                    key="jump_to_labeled"
                )
                if jump_to != idx + 1:
                    st.session_state.labeled_current_idx = jump_to - 1
                    st.rerun()

            st.markdown("---")

            # Event details
            st.markdown("### 📋 Event Details")
            detail_col1, detail_col2, detail_col3 = st.columns(3)
            with detail_col1:
                st.write(f"**Company:** {row['companyname']}")
                st.write(f"**Date:** {row['event_date']}")
            with detail_col2:
                st.write(f"**Word Count:** {row['total_word_count']:,}")
                st.write(f"**Headline:** {row['headline']}")
            with detail_col3:
                st.write(f"**Transcript ID:** {row['transcriptid']}")
                st.write(f"**Speakers:** {row['num_speakers']}")

            st.markdown("---")

            # Presentation text
            st.markdown("### 📝 Presentation Text")
            st.text_area(
                "Full executive presentation text:",
                value=row['presentation_text'],
                height=250,
                disabled=True,
                label_visibility="collapsed"
            )

            st.markdown("---")

            # AI vs Human comparison
            st.markdown("### 🤖 AI vs 👤 Human Comparison")

            ai_sentiment = row['ai_sentiment']
            user_sentiment = row['user_sentiment']
            is_agreement = ai_sentiment == user_sentiment

            comp_col1, comp_col2, comp_col3 = st.columns(3)

            with comp_col1:
                st.markdown("**🤖 AI Classification**")
                ai_color = {'positive': 'green', 'negative': 'red', 'neutral': 'gray'}[ai_sentiment]
                st.markdown(f":{ai_color}[**{ai_sentiment.upper()}**]")
                st.caption("AI Reasoning:")
                st.markdown(f"*{row['ai_reasoning']}*")

            with comp_col2:
                st.markdown("**Agreement Status**")
                if is_agreement:
                    st.success("✅ **MATCH**")
                    st.caption("Human agreed with AI")
                else:
                    st.error("⚠️ **DISAGREEMENT**")
                    st.caption(f"Changed from {ai_sentiment} to {user_sentiment}")

            with comp_col3:
                st.markdown("**👤 Human Label**")
                user_color = {'positive': 'green', 'negative': 'red', 'neutral': 'gray'}[user_sentiment]
                st.markdown(f":{user_color}[**{user_sentiment.upper()}**]")
                if row.get('user_notes'):
                    st.caption("Human Notes:")
                    st.markdown(f"*{row['user_notes']}*")
                else:
                    st.caption("No notes provided")

            st.markdown("---")

            # Comparison table
            st.markdown("### 📊 Summary Comparison")
            comparison_data = {
                'Aspect': ['Sentiment', 'Confidence', 'Category'],
                'AI': [ai_sentiment, row.get('ai_prob', 'N/A'), 'Automated'],
                'Human': [user_sentiment, 'Manual Review', 'Expert'],
                'Status': ['Match ✅' if is_agreement else 'Mismatch ⚠️', '', '']
            }
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)

        else:
            st.info("No events match your filter criteria.")
