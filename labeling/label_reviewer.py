"""
Sentiment Label Reviewer
Simple viewer to review and edit sentiment labels (positive/negative/neutral)
Shows the presentation text and allows editing the sentiment tag
"""

import streamlit as st
import pickle
import pandas as pd

# Page config
st.set_page_config(
    page_title="Label Reviewer",
    page_icon="🏷️",
    layout="wide"
)

# Load labeled dataset
@st.cache_data
def load_data():
    with open('data/labeled/sample_20_labeled.pkl', 'rb') as f:
        return pickle.load(f)

def save_data(df):
    with open('data/labeled/sample_20_labeled.pkl', 'wb') as f:
        pickle.dump(df, f)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = load_data()
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0

df = st.session_state.df

# Header with stats
st.title("🏷️ Sentiment Label Reviewer")

# Stats bar
col1, col2, col3, col4, col5 = st.columns(5)

total = len(df)
positive_count = (df['user_sentiment'] == 'positive').sum()
negative_count = (df['user_sentiment'] == 'negative').sum()
neutral_count = (df['user_sentiment'] == 'neutral').sum()
changed_count = df['label_changed'].sum()

with col1:
    st.metric("Total", total)
with col2:
    st.metric("Positive", f"{positive_count} ({positive_count/total*100:.0f}%)")
with col3:
    if negative_count == 0:
        st.metric("Negative", f"{negative_count} ({negative_count/total*100:.0f}%)", delta="⚠️ None!")
    else:
        st.metric("Negative", f"{negative_count} ({negative_count/total*100:.0f}%)")
with col4:
    st.metric("Neutral", f"{neutral_count} ({neutral_count/total*100:.0f}%)")
with col5:
    st.metric("Changed", changed_count)

st.markdown("---")

# Main layout: sidebar + content
col_nav, col_main = st.columns([1, 3])

with col_nav:
    st.subheader("📍 Navigation")
    
    # Event list with sentiment indicators
    for i in range(len(df)):
        sentiment = df.iloc[i]['user_sentiment']
        emoji = {'positive': '✅', 'negative': '❌', 'neutral': '⚪'}[sentiment]
        changed = '🔄' if df.iloc[i]['label_changed'] else ''
        
        label = f"{emoji}{changed} {i+1}. {df.iloc[i]['companyname'][:20]}"
        
        if st.button(label, key=f"nav_{i}", use_container_width=True, 
                     type="primary" if i == st.session_state.current_idx else "secondary"):
            st.session_state.current_idx = i
            st.rerun()
    
    st.markdown("---")
    
    # Quick navigation
    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ Prev", use_container_width=True):
            if st.session_state.current_idx > 0:
                st.session_state.current_idx -= 1
                st.rerun()
    with col_next:
        if st.button("Next ➡️", use_container_width=True):
            if st.session_state.current_idx < len(df) - 1:
                st.session_state.current_idx += 1
                st.rerun()

with col_main:
    idx = st.session_state.current_idx
    row = df.iloc[idx]
    
    # Event header
    st.header(f"Event {idx+1} of {total}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Company:** {row['companyname']}")
    with col2:
        st.markdown(f"**Date:** {row['event_date']}")
    with col3:
        st.markdown(f"**Words:** {row['total_word_count']:,}")
    
    st.markdown(f"**Headline:** {row['headline']}")
    
    st.markdown("---")
    
    # Show presentation text
    st.subheader("📄 Presentation Text")
    st.text_area("", row['presentation_text'], height=400, disabled=True, label_visibility="collapsed")
    
    st.markdown("---")
    
    # Sentiment labeling section
    st.subheader("🏷️ Sentiment Label")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**AI Label:**")
        ai_color = {
            'positive': 'green',
            'negative': 'red',
            'neutral': 'gray'
        }[row['ai_sentiment']]
        
        st.markdown(f":{ai_color}[**{row['ai_sentiment'].upper()}**]")
        st.caption(row['ai_reasoning'])
    
    with col2:
        st.markdown("**Your Label:**")
        
        # Sentiment selector
        sentiment_options = ['positive', 'negative', 'neutral']
        current_idx_sent = sentiment_options.index(row['user_sentiment'])
        
        user_sentiment = st.radio(
            "Select",
            sentiment_options,
            index=current_idx_sent,
            horizontal=True,
            label_visibility="collapsed",
            key=f"sentiment_{idx}"
        )
        
        # Show if changed
        if user_sentiment != row['ai_sentiment']:
            st.warning(f"⚠️ Changed from {row['ai_sentiment'].upper()}")
        else:
            st.success("✓ Matches AI")
    
    # Notes
    st.markdown("---")
    user_notes = st.text_area(
        "📝 Notes (optional)",
        value=row.get('user_notes', ''),
        height=80,
        placeholder="Why this label? Any concerns?",
        key=f"notes_{idx}"
    )
    
    # Save button
    st.markdown("")
    if st.button("💾 SAVE & NEXT", type="primary", use_container_width=True):
        # Check if changed
        label_changed = user_sentiment != row['ai_sentiment']
        
        # Update
        df.at[idx, 'user_sentiment'] = user_sentiment
        df.at[idx, 'user_notes'] = user_notes
        df.at[idx, 'label_changed'] = label_changed
        
        # Save
        save_data(df)
        st.session_state.df = df
        
        st.success("✅ Saved!")
        
        # Auto-advance
        if st.session_state.current_idx < len(df) - 1:
            st.session_state.current_idx += 1
            st.rerun()
        else:
            st.balloons()
            st.info("🎉 All events reviewed!")

# Footer note about negative definition
st.markdown("---")
st.info("⚠️ **Note:** Currently 0 NEGATIVE labels. Definition from README: 'Cautious tone, poor results presentation, challenges/concerns'. If this doesn't match what you expect, we need to clarify what NEGATIVE means for this project.")
