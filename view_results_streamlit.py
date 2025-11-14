#!/usr/bin/env python3
"""
Streamlit Viewer for Sentiment Analysis Results
Usage: streamlit run view_results_streamlit.py
"""

import streamlit as st
import pickle
import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="Sentiment Analysis Results",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def load_data(file_path):
    """Load sentiment results from pickle file"""
    with open(file_path, 'rb') as f:
        df = pickle.load(f)
    return df

def main():
    st.title("📊 Sentiment Analysis Results Viewer")
    st.markdown("---")
    
    # File selector
    results_files = list(Path('data/results').glob('*.pkl')) if Path('data/results').exists() else []
    
    if not results_files:
        st.error("❌ No results files found in data/results/")
        return
    
    file_options = {str(f): f for f in results_files}
    selected_file = st.selectbox(
        "Select results file:",
        options=list(file_options.keys()),
        index=0
    )
    
    # Load data
    df = load_data(file_options[selected_file])
    
    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Events", f"{len(df):,}")
    with col2:
        st.metric("Companies", df['companyid'].nunique())
    with col3:
        st.metric("Total Cost", f"${df['cost'].sum():.2f}")
    with col4:
        st.metric("Avg Cost/Event", f"${df['cost'].mean():.4f}")
    with col5:
        success_rate = df['success'].sum() / len(df) * 100 if 'success' in df.columns else 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 Overview", "📋 Data Table", "🔍 Search & Filter", "📄 Details", "🗂️ Raw Data", "🏢 Company Reports"])
    
    with tab1:
        # Sentiment distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Sentiment Distribution")
            sentiment_counts = df['sentiment'].value_counts()
            fig_pie = px.pie(
                values=sentiment_counts.values,
                names=sentiment_counts.index,
                color=sentiment_counts.index,
                color_discrete_map={'positive': '#00CC96', 'negative': '#EF553B', 'neutral': '#636EFA'},
                hole=0.4
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Show counts
            for sentiment, count in sentiment_counts.items():
                pct = count / len(df) * 100
                st.write(f"**{sentiment.upper()}**: {count} ({pct:.1f}%)")
        
        with col2:
            st.subheader("Cost Distribution")
            fig_box = px.box(
                df,
                y='cost',
                points='all',
                title='Cost per Event'
            )
            st.plotly_chart(fig_box, use_container_width=True)
            
            st.subheader("Token Usage")
            total_tokens = df['total_tokens'].sum()
            avg_tokens = df['total_tokens'].mean()
            st.write(f"**Total Tokens**: {total_tokens:,}")
            st.write(f"**Avg Tokens/Event**: {avg_tokens:,.0f}")
        
        # Sentiment over time
        st.subheader("Sentiment by Date")
        df_time = df.copy()
        df_time['event_date'] = pd.to_datetime(df_time['event_date'])
        sentiment_by_date = df_time.groupby(['event_date', 'sentiment']).size().reset_index(name='count')
        
        fig_time = px.bar(
            sentiment_by_date,
            x='event_date',
            y='count',
            color='sentiment',
            color_discrete_map={'positive': '#00CC96', 'negative': '#EF553B', 'neutral': '#636EFA'},
            barmode='stack'
        )
        st.plotly_chart(fig_time, use_container_width=True)
    
    with tab2:
        st.subheader("All Events")
        
        # Column selector
        all_columns = list(df.columns)
        default_columns = ['companyname', 'event_date', 'sentiment', 'positive_prob', 
                          'negative_prob', 'neutral_prob', 'total_tokens', 'cost']
        
        selected_columns = st.multiselect(
            "Select columns to display:",
            options=all_columns,
            default=[col for col in default_columns if col in all_columns]
        )
        
        if selected_columns:
            display_df = df[selected_columns].copy()
            
            # Format specific columns
            if 'cost' in selected_columns:
                display_df['cost'] = display_df['cost'].apply(lambda x: f"${x:.4f}")
            
            st.dataframe(display_df, use_container_width=True, height=600)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Full Dataset as CSV",
                data=csv,
                file_name="sentiment_results.csv",
                mime="text/csv"
            )
    
    with tab3:
        st.subheader("Search & Filter")
        
        # Filters
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment filter
            sentiment_filter = st.multiselect(
                "Filter by Sentiment:",
                options=['positive', 'negative', 'neutral'],
                default=['positive', 'negative', 'neutral']
            )
        
        with col2:
            # Company search
            company_search = st.text_input("Search by Company Name:")
        
        # Apply filters
        filtered_df = df[df['sentiment'].isin(sentiment_filter)]
        
        if company_search:
            filtered_df = filtered_df[
                filtered_df['companyname'].str.contains(company_search, case=False, na=False)
            ]
        
        st.write(f"**Found {len(filtered_df)} events**")
        
        # Display filtered results
        if len(filtered_df) > 0:
            display_cols = ['companyname', 'event_date', 'sentiment', 'positive_prob', 
                          'negative_prob', 'neutral_prob', 'reasoning']
            display_filtered = filtered_df[display_cols].copy()
            display_filtered['reasoning'] = display_filtered['reasoning'].apply(
                lambda x: x[:100] + "..." if len(x) > 100 else x
            )
            
            st.dataframe(display_filtered, use_container_width=True, height=500)
            
            # Top expensive in filtered results
            st.subheader("Top 10 Most Expensive (from filtered results)")
            top_expensive = filtered_df.nlargest(10, 'cost')[
                ['companyname', 'event_date', 'total_word_count', 'total_tokens', 'cost']
            ]
            st.dataframe(top_expensive, use_container_width=True)
    
    with tab4:
        st.subheader("Detailed Event View")
        
        # Event selector
        event_options = [
            f"{idx}: {row['companyname']} - {row['event_date']}"
            for idx, row in df.iterrows()
        ]
        
        selected_event = st.selectbox(
            "Select an event:",
            options=range(len(df)),
            format_func=lambda x: event_options[x]
        )
        
        if selected_event is not None:
            event = df.iloc[selected_event]
            
            # Display event details
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"### {event['companyname']}")
                st.write(f"**Date**: {event['event_date']}")
                if 'headline' in event:
                    st.write(f"**Headline**: {event['headline']}")
            
            with col2:
                # Sentiment badge
                sentiment_color = {
                    'positive': 'green',
                    'negative': 'red',
                    'neutral': 'gray'
                }
                st.markdown(
                    f"<h2 style='color: {sentiment_color[event['sentiment']]}'>"
                    f"{event['sentiment'].upper()}</h2>",
                    unsafe_allow_html=True
                )
            
            # Probabilities
            st.subheader("Sentiment Probabilities")
            prob_data = pd.DataFrame({
                'Sentiment': ['Positive', 'Negative', 'Neutral'],
                'Probability': [event['positive_prob'], event['negative_prob'], event['neutral_prob']]
            })
            
            fig_prob = px.bar(
                prob_data,
                x='Sentiment',
                y='Probability',
                color='Sentiment',
                color_discrete_map={'Positive': '#00CC96', 'Negative': '#EF553B', 'Neutral': '#636EFA'}
            )
            st.plotly_chart(fig_prob, use_container_width=True)
            
            # Reasoning
            st.subheader("Reasoning")
            st.info(event['reasoning'])
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Word Count", f"{event['total_word_count']:,}")
            with col2:
                st.metric("Total Tokens", f"{event['total_tokens']:,}")
            with col3:
                st.metric("Cost", f"${event['cost']:.4f}")
            
            # Presentation text
            if 'presentation_text' in event:
                with st.expander("📄 View Full Presentation Text"):
                    st.text_area(
                        "Presentation",
                        value=event['presentation_text'],
                        height=400,
                        disabled=True
                    )
    
    with tab5:
        st.subheader("🗂️ Complete Raw Data View")
        st.write("Browse all rows with complete information including presentation texts")
        
        # Row selector with pagination
        rows_per_page = st.slider("Rows per page:", min_value=10, max_value=100, value=25, step=5)
        total_pages = (len(df) - 1) // rows_per_page + 1
        page = st.number_input("Page:", min_value=1, max_value=total_pages, value=1)
        
        start_idx = (page - 1) * rows_per_page
        end_idx = min(start_idx + rows_per_page, len(df))
        
        st.write(f"Showing rows {start_idx + 1} to {end_idx} of {len(df)}")
        
        # Display paginated data
        for idx in range(start_idx, end_idx):
            row = df.iloc[idx]
            
            with st.expander(f"**Row {idx}**: {row['companyname']} - {row['event_date']} - {row['sentiment'].upper()}"):
                # Create two columns for better layout
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("#### 📋 Event Information")
                    st.write(f"**Company ID**: {row['companyid']}")
                    st.write(f"**Company Name**: {row['companyname']}")
                    st.write(f"**Transcript ID**: {row['transcriptid']}")
                    st.write(f"**Event Date**: {row['event_date']}")
                    if 'headline' in row and pd.notna(row['headline']):
                        st.write(f"**Headline**: {row['headline']}")
                    
                    st.markdown("#### 💭 Sentiment Analysis")
                    st.write(f"**Sentiment**: {row['sentiment'].upper()}")
                    st.write(f"**Positive Prob**: {row['positive_prob']:.3f}")
                    st.write(f"**Negative Prob**: {row['negative_prob']:.3f}")
                    st.write(f"**Neutral Prob**: {row['neutral_prob']:.3f}")
                    st.write(f"**Reasoning**: {row['reasoning']}")
                
                with col2:
                    st.markdown("#### 📊 Metrics")
                    st.write(f"**Word Count**: {row['total_word_count']:,}")
                    st.write(f"**Input Tokens**: {row['input_tokens']:,}")
                    st.write(f"**Output Tokens**: {row['output_tokens']:,}")
                    st.write(f"**Total Tokens**: {row['total_tokens']:,}")
                    st.write(f"**Cost**: ${row['cost']:.6f}")
                    
                    if 'success' in row:
                        st.write(f"**Success**: {row['success']}")
                    if 'attempts' in row:
                        st.write(f"**Attempts**: {row['attempts']}")
                
                # Full presentation text
                if 'presentation_text' in row and pd.notna(row['presentation_text']):
                    st.markdown("#### 📄 Full Presentation Text")
                    st.text_area(
                        f"Presentation Text (Row {idx})",
                        value=row['presentation_text'],
                        height=300,
                        key=f"presentation_{idx}",
                        disabled=True
                    )
                
                st.markdown("---")
        
        # Download complete raw data
        st.markdown("### 📥 Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            # Full CSV export
            csv_full = df.to_csv(index=False)
            st.download_button(
                label="Download Full Dataset (CSV)",
                data=csv_full,
                file_name="sentiment_results_full.csv",
                mime="text/csv"
            )
        
        with col2:
            # JSON export with all data
            json_data = df.to_json(orient='records', indent=2)
            st.download_button(
                label="Download Full Dataset (JSON)",
                data=json_data,
                file_name="sentiment_results_full.json",
                mime="application/json"
            )
    
    with tab6:
        st.subheader("🏢 Company-Level Reports")
        st.write("Aggregated sentiment analysis by company")
        
        # Create company-level aggregation
        company_stats = df.groupby('companyname').agg({
            'transcriptid': 'count',
            'sentiment': lambda x: x.value_counts().to_dict(),
            'positive_prob': 'mean',
            'negative_prob': 'mean',
            'neutral_prob': 'mean',
            'cost': 'sum',
            'total_tokens': 'sum',
            'total_word_count': 'sum'
        }).reset_index()
        
        company_stats.columns = ['Company', 'Total Events', 'Sentiment Distribution', 
                                'Avg Positive Prob', 'Avg Negative Prob', 'Avg Neutral Prob',
                                'Total Cost', 'Total Tokens', 'Total Words']
        
        # Sort by number of events
        company_stats = company_stats.sort_values('Total Events', ascending=False)
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Companies", len(company_stats))
        with col2:
            avg_events = company_stats['Total Events'].mean()
            st.metric("Avg Events/Company", f"{avg_events:.1f}")
        with col3:
            max_events = company_stats['Total Events'].max()
            st.metric("Max Events/Company", int(max_events))
        
        st.markdown("---")
        
        # View mode selector
        view_mode = st.radio("View Mode:", ["Summary Table", "Detailed Company View"], horizontal=True)
        
        if view_mode == "Summary Table":
            st.subheader("Company Summary Table")
            
            # Prepare display dataframe
            display_company = company_stats.copy()
            
            # Extract sentiment counts
            display_company['Positive'] = display_company['Sentiment Distribution'].apply(
                lambda x: x.get('positive', 0)
            )
            display_company['Negative'] = display_company['Sentiment Distribution'].apply(
                lambda x: x.get('negative', 0)
            )
            display_company['Neutral'] = display_company['Sentiment Distribution'].apply(
                lambda x: x.get('neutral', 0)
            )
            
            # Format columns
            display_company['Total Cost'] = display_company['Total Cost'].apply(lambda x: f"${x:.2f}")
            display_company['Avg Positive Prob'] = display_company['Avg Positive Prob'].apply(lambda x: f"{x:.3f}")
            display_company['Avg Negative Prob'] = display_company['Avg Negative Prob'].apply(lambda x: f"{x:.3f}")
            display_company['Avg Neutral Prob'] = display_company['Avg Neutral Prob'].apply(lambda x: f"{x:.3f}")
            
            # Select columns for display
            final_display = display_company[[
                'Company', 'Total Events', 'Positive', 'Negative', 'Neutral',
                'Avg Positive Prob', 'Avg Negative Prob', 'Avg Neutral Prob',
                'Total Tokens', 'Total Cost'
            ]]
            
            st.dataframe(final_display, use_container_width=True, height=600)
            
            # Download button
            csv = final_display.to_csv(index=False)
            st.download_button(
                label="📥 Download Company Report (CSV)",
                data=csv,
                file_name="company_sentiment_report.csv",
                mime="text/csv"
            )
            
        else:  # Detailed Company View
            st.subheader("Detailed Company Analysis")
            
            # Company selector
            selected_company = st.selectbox(
                "Select Company:",
                options=company_stats['Company'].tolist()
            )
            
            if selected_company:
                # Get company data
                company_row = company_stats[company_stats['Company'] == selected_company].iloc[0]
                company_events = df[df['companyname'] == selected_company]
                
                # Header
                st.markdown(f"### {selected_company}")
                
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Events", int(company_row['Total Events']))
                with col2:
                    st.metric("Total Cost", f"${company_row['Total Cost']:.2f}")
                with col3:
                    st.metric("Total Tokens", f"{int(company_row['Total Tokens']):,}")
                with col4:
                    st.metric("Total Words", f"{int(company_row['Total Words']):,}")
                
                st.markdown("---")
                
                # Sentiment distribution for this company
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Sentiment Distribution")
                    sentiment_dist = company_row['Sentiment Distribution']
                    
                    fig_company_pie = px.pie(
                        values=list(sentiment_dist.values()),
                        names=list(sentiment_dist.keys()),
                        color=list(sentiment_dist.keys()),
                        color_discrete_map={'positive': '#00CC96', 'negative': '#EF553B', 'neutral': '#636EFA'},
                        hole=0.4
                    )
                    st.plotly_chart(fig_company_pie, use_container_width=True)
                    
                    # Show counts
                    for sentiment, count in sentiment_dist.items():
                        pct = count / company_row['Total Events'] * 100
                        st.write(f"**{sentiment.upper()}**: {count} ({pct:.1f}%)")
                
                with col2:
                    st.subheader("Average Sentiment Probabilities")
                    prob_data = pd.DataFrame({
                        'Sentiment': ['Positive', 'Negative', 'Neutral'],
                        'Probability': [
                            company_row['Avg Positive Prob'],
                            company_row['Avg Negative Prob'],
                            company_row['Avg Neutral Prob']
                        ]
                    })
                    
                    fig_prob = px.bar(
                        prob_data,
                        x='Sentiment',
                        y='Probability',
                        color='Sentiment',
                        color_discrete_map={'Positive': '#00CC96', 'Negative': '#EF553B', 'Neutral': '#636EFA'}
                    )
                    st.plotly_chart(fig_prob, use_container_width=True)
                
                # Timeline of events
                st.subheader("Events Timeline")
                company_events_sorted = company_events.sort_values('event_date')
                company_events_sorted['event_date_dt'] = pd.to_datetime(company_events_sorted['event_date'])
                
                fig_timeline = px.scatter(
                    company_events_sorted,
                    x='event_date_dt',
                    y='sentiment',
                    color='sentiment',
                    color_discrete_map={'positive': '#00CC96', 'negative': '#EF553B', 'neutral': '#636EFA'},
                    hover_data=['headline', 'positive_prob', 'negative_prob', 'neutral_prob'],
                    title=f"Sentiment Over Time - {selected_company}"
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
                
                # All events for this company
                st.subheader("All Events")
                event_display = company_events[[
                    'event_date', 'sentiment', 'positive_prob', 'negative_prob', 'neutral_prob',
                    'reasoning', 'total_tokens', 'cost'
                ]].copy()
                event_display['cost'] = event_display['cost'].apply(lambda x: f"${x:.4f}")
                st.dataframe(event_display, use_container_width=True)

if __name__ == "__main__":
    main()
