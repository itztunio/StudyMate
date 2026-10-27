"""
StudyMate - WhatsApp Chat Analyzer & AI Reply Generator
Streamlit Community Cloud Deployment Entry Point
"""

import os
import io
import json
import streamlit as st
from dotenv import load_dotenv

# Load local environment if present
load_dotenv()

from analyzer import parse_chat_text, analyze_chat
from ai_service import generate_chat_replies

# Set page configuration
st.set_page_config(
    page_title="StudyMate — WhatsApp Friendship & Chat Analyzer",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (WhatsApp Emerald Theme)
st.markdown("""
<style>
    .main-header {
        color: #075E54;
        font-weight: 800;
        font-size: 2.3rem;
        margin-bottom: 0px;
    }
    .sub-header {
        color: #128C7E;
        font-size: 1.15rem;
        margin-bottom: 25px;
    }
    .metric-box {
        background-color: #F0F2F5;
        border-radius: 12px;
        padding: 16px;
        border-left: 5px solid #128C7E;
        margin-bottom: 15px;
    }
    .score-banner {
        background: linear-gradient(135deg, #075E54 0%, #128C7E 100%);
        color: white;
        padding: 24px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 25px;
    }
    .stButton>button {
        background-color: #128C7E;
        color: white;
        border-radius: 20px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Helper to check or set Gemini API key from Streamlit secrets or env
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
    except Exception:
        pass

# Sidebar navigation
with st.sidebar:
    st.image("https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f4ac.png", width=60)
    st.title("StudyMate")
    st.caption("WhatsApp Friendship Analyzer & AI Studio")
    
    app_mode = st.radio(
        "Navigation",
        ["📊 Chat Analyzer & Dashboard", "🤖 AI Reply Studio", "ℹ️ About & Privacy"]
    )
    
    st.markdown("---")
    st.markdown("### ⚡ Quick Demo")
    if st.button("Load Demo Chat ✨", use_container_width=True):
        sample_path = os.path.join(os.path.dirname(__file__), 'sample_data', 'sample_chat.txt')
        if os.path.exists(sample_path):
            with open(sample_path, 'r', encoding='utf-8') as f:
                st.session_state['chat_text'] = f.read()
                st.session_state['chat_filename'] = "Sample_Demo_Chat.txt"
                st.success("Demo loaded! Head to Chat Analyzer.")
    
    st.markdown("---")
    st.caption("100% Privacy-First: Messages are analyzed ephemerally in memory and never stored permanently.")

# PAGE 1: CHAT ANALYZER
if app_mode == "📊 Chat Analyzer & Dashboard":
    st.markdown('<div class="main-header">💬 StudyMate WhatsApp Analyzer</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">"Your chats, your memories, your insights."</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload exported WhatsApp chat (.txt)", type=["txt"])
    
    if uploaded_file is not None:
        try:
            raw_text = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            raw_text = uploaded_file.read().decode('latin-1')
        st.session_state['chat_text'] = raw_text
        st.session_state['chat_filename'] = uploaded_file.name

    chat_content = st.session_state.get('chat_text', None)

    if chat_content:
        with st.spinner("Analyzing conversation metrics..."):
            messages = parse_chat_text(chat_content)
            results = analyze_chat(messages)

        if not results.get('success'):
            st.error(results.get('error', 'Could not parse chat data.'))
        else:
            summary = results['summary']
            score = results['friendship_score']
            participants = results['participants']
            charts = results['charts']

            # Top 4 Metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("💬 Total Messages", f"{summary['total_messages']:,}")
            col2.metric("👥 Participants", summary['participant_count'])
            col3.metric("🏆 Top Contributor", summary['most_active_sender'])
            col4.metric("⏰ Peak Hour", summary['busiest_hour'])

            st.markdown("---")

            # Friendship Score Card
            st.markdown(f"""
            <div class="score-banner">
                <h3 style="margin: 0; color: #D0F5E3;">✨ PLAYFUL FRIENDSHIP SCORE</h3>
                <h1 style="font-size: 3.5rem; margin: 10px 0; color: white;">{score['total_score']} / 100</h1>
                <h3 style="margin: 0; color: white;">{score['tier']}</h3>
                <p style="margin-top: 8px; opacity: 0.9; font-size: 1rem;">{score['tagline']}</p>
                <small style="opacity: 0.75;">Note: Calculated purely for entertainment based on activity balance and emoji expressiveness.</small>
            </div>
            """, unsafe_allow_html=True)

            # Score Breakdown Bars
            b_cols = st.columns(4)
            idx = 0
            for k, item in score['breakdown'].items():
                with b_cols[idx]:
                    st.write(f"**{item['label']}**")
                    st.progress(item['score'] / item['max'])
                    st.caption(f"{item['score']} / {item['max']} pts")
                idx += 1

            st.markdown("---")

            # Fun Facts
            st.subheader("💡 Conversational Highlights")
            for fact in results['fun_facts']:
                st.info(fact)

            st.markdown("---")

            # Charts
            st.subheader("📊 Visual Analytics")
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.write("**Messages per Participant**")
                st.bar_chart({p['name']: p['messages'] for p in participants})

            with chart_col2:
                st.write("**Top Emojis Used**")
                if results['top_emojis']:
                    st.bar_chart({e['emoji']: e['count'] for e in results['top_emojis'][:8]})
                else:
                    st.write("No emojis detected in this chat.")

            # Participant Summary Table
            st.subheader("👥 Participant Breakdown")
            table_data = []
            for p in participants:
                table_data.append({
                    "Participant": p['name'],
                    "Messages": f"{p['messages']:,}",
                    "Share": f"{p['percentage']}%",
                    "Media Sent": p['media'],
                    "Avg Length": f"{p['avg_length']} chars",
                    "Top Emojis": p['top_emojis']
                })
            st.table(table_data)

            # Download buttons
            st.markdown("### 📥 Download Reports")
            d_col1, d_col2 = st.columns(2)

            # CSV Report
            csv_buffer = io.StringIO()
            csv_buffer.write("Participant,Messages,Share,Media,AvgLength\n")
            for p in participants:
                csv_buffer.write(f"{p['name']},{p['messages']},{p['percentage']}%,{p['media']},{p['avg_length']}\n")
            
            d_col1.download_button(
                label="📥 Download CSV Report",
                data=csv_buffer.getvalue(),
                file_name="studymate_analysis.csv",
                mime="text/csv"
            )

            # Text summary
            summary_text = f"""StudyMate Chat Analysis Summary
Date Range: {summary['date_range']}
Total Messages: {summary['total_messages']:,}
Friendship Score: {score['total_score']}/100 ({score['tier']})
Top Contributor: {summary['most_active_sender']}
Busiest Hour: {summary['busiest_hour']}
"""
            d_col2.download_button(
                label="📄 Download Text Summary",
                data=summary_text,
                file_name="studymate_summary.txt",
                mime="text/plain"
            )

    else:
        st.info("👆 Upload your WhatsApp export `.txt` file above or click **'Load Demo Chat ✨'** in the sidebar to try it immediately!")

# PAGE 2: AI REPLY STUDIO
elif app_mode == "🤖 AI Reply Studio":
    st.markdown('<div class="main-header">🤖 AI Reply Studio</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Generate contextual WhatsApp replies powered by Google Gemini</div>', unsafe_allow_html=True)

    if not os.getenv('GEMINI_API_KEY'):
        st.warning("⚠️ **Gemini API Key missing**: Set `GEMINI_API_KEY` in Streamlit Secrets to enable live AI replies.")

    with st.form("reply_form"):
        message_input = st.text_area("Message You Received *", placeholder="e.g. 'Are we still meeting up tonight for group study?'")
        context_input = st.text_input("Context / What's on your mind? (Optional)", placeholder="e.g. 'Running 15 mins late, but still coming'")
        tone_choice = st.selectbox("Desired Tone", ["Friendly 😊", "Funny 😂", "Cute ✨", "Polite 🤝", "Professional 💼", "Casual 😎"])
        submit_btn = st.form_submit_button("✨ Generate 3 Reply Suggestions")

    if submit_btn:
        if not message_input.strip():
            st.error("Please enter a message.")
        else:
            clean_tone = tone_choice.split()[0].lower()
            with st.spinner("Gemini is crafting tailored replies..."):
                res = generate_chat_replies(message_input, context_input, clean_tone)
            
            if res.get('success') and res.get('replies'):
                st.success("Replies Generated!")
                for i, r in enumerate(res['replies'], 1):
                    with st.container():
                        st.markdown(f"**Suggestion {i}:**")
                        st.code(r, language=None)
            else:
                st.error(res.get('error', 'Failed to generate replies.'))

# PAGE 3: ABOUT & PRIVACY
else:
    st.markdown('<div class="main-header">ℹ️ About StudyMate</div>', unsafe_allow_html=True)
    st.write("""
    ### 🛡️ 100% Privacy & Security
    - **Ephemeral Processing**: Chat logs are parsed strictly in memory and are never saved to permanent disk or databases.
    - **No Direct WhatsApp Connection**: Works entirely offline with standard exported text files.
    - **Gemini AI Safety**: Only messages you deliberately submit in the AI Reply Studio are sent to Google Gemini for suggestion generation.
    - **Free Cloud Deployment**: Designed for seamless zero-cost hosting on Streamlit Community Cloud.
    """)
