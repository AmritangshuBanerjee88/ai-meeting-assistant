"""
AI Meeting Assistant - Streamlit Version
Powered by Google Gemini via API Key
"""
import streamlit as st
import google.generativeai as genai
from datetime import datetime
import time

# Page config
st.set_page_config(
    page_title="🤖 AI Meeting Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #4285f4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .transcript-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #4285f4;
        margin: 1rem 0;
    }
    .ai-response-box {
        background-color: #f3e5f5;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #9c27b0;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'meeting_context' not in st.session_state:
    st.session_state.meeting_context = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = None
if 'model' not in st.session_state:
    st.session_state.model = None

def initialize_gemini(api_key):
    """Initialize Gemini with API key"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            system_instruction="""You are an intelligent AI meeting assistant. 
            Analyze meeting transcripts and provide helpful, concise responses.
            
            Your capabilities:
            - Answer questions based on meeting context
            - Identify action items and decisions
            - Provide summaries and insights
            - Suggest next steps
            
            Be professional, concise, and helpful."""
        )
        return model
    except Exception as e:
        st.error(f"Error initializing Gemini: {str(e)}")
        return None

def add_to_context(speaker, text):
    """Add transcript to meeting context"""
    st.session_state.meeting_context.append({
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'speaker': speaker,
        'text': text
    })

def get_context_text():
    """Build context string from meeting history"""
    context_lines = []
    for item in st.session_state.meeting_context[-20:]:
        context_lines.append(f"[{item['timestamp']}] {item['speaker']}: {item['text']}")
    return "\n".join(context_lines)

def query_gemini(question):
    """Query Gemini with meeting context"""
    if not st.session_state.model:
        return "⚠️ Please configure your API key first."
    
    context = get_context_text()
    
    if not context:
        return "⚠️ No meeting transcript available yet. Add some transcript first!"
    
    prompt = f"""Meeting Context:
{context}

Question: {question}

Provide a clear, concise answer based on the meeting context above."""
    
    try:
        chat = st.session_state.model.start_chat()
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"

def generate_summary():
    """Generate meeting summary"""
    if not st.session_state.model:
        return "⚠️ Please configure your API key first."
    
    context = get_context_text()
    
    if not context:
        return "⚠️ No meeting content to summarize."
    
    prompt = f"""Analyze this meeting transcript and provide a comprehensive summary:

{context}

Provide:
1. **Key Discussion Points**: Main topics covered
2. **Decisions Made**: Concrete decisions and agreements
3. **Action Items**: Tasks and assignments
4. **Open Questions**: Unresolved issues
5. **Next Steps**: Recommended actions

Be specific and reference actual discussion points."""
    
    try:
        chat = st.session_state.model.start_chat()
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Main UI
st.markdown('<h1 class="main-header">🤖 AI Meeting Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Powered by Google Gemini 2.0 Flash</p>', unsafe_allow_html=True)

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key input
    api_key_input = st.text_input(
        "Google AI API Key",
        type="password",
        value=st.session_state.gemini_api_key or "",
        help="Enter your Google AI API key from GCP"
    )
    
    if api_key_input and api_key_input != st.session_state.gemini_api_key:
        st.session_state.gemini_api_key = api_key_input
        st.session_state.model = initialize_gemini(api_key_input)
        if st.session_state.model:
            st.success("✅ Gemini initialized!")
    
    st.divider()
    
    # Meeting Stats
    st.header("📊 Meeting Stats")
    st.metric("Transcript Items", len(st.session_state.meeting_context))
    st.metric("Q&A Exchanges", len(st.session_state.chat_history))
    
    st.divider()
    
    # Actions
    if st.button("🗑️ Clear All"):
        st.session_state.meeting_context = []
        st.session_state.chat_history = []
        st.rerun()
    
    if st.button("📥 Download Transcript"):
        transcript = "\n".join([
            f"[{item['timestamp']}] {item['speaker']}: {item['text']}"
            for item in st.session_state.meeting_context
        ])
        st.download_button(
            "Download as TXT",
            transcript,
            file_name=f"meeting_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Meeting Transcript")
    
    # Add transcript form
    with st.form("add_transcript", clear_on_submit=True):
        speaker = st.text_input("Speaker Name", placeholder="e.g., John, Sarah, etc.")
        transcript = st.text_area("What was said?", placeholder="Enter transcript text...", height=100)
        
        submitted = st.form_submit_button("➕ Add to Transcript")
        
        if submitted and speaker and transcript:
            add_to_context(speaker, transcript)
            st.success(f"✅ Added transcript from {speaker}")
            st.rerun()
    
    # Display transcript
    st.subheader("Recent Transcript")
    
    if st.session_state.meeting_context:
        for item in reversed(st.session_state.meeting_context[-10:]):
            st.markdown(f"""
            <div class="transcript-box">
                <strong>[{item['timestamp']}] {item['speaker']}:</strong><br>
                {item['text']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("👋 No transcript yet. Add some meeting content to get started!")

with col2:
    st.header("💬 Ask Questions")
    
    # Question form
    question = st.text_input("Ask a question about the meeting:", placeholder="e.g., What were the main action items?")
    
    col_ask, col_summary = st.columns(2)
    
    with col_ask:
        if st.button("🔍 Ask"):
            if question:
                with st.spinner("🤔 Thinking..."):
                    answer = query_gemini(question)
                    st.session_state.chat_history.append({
                        'question': question,
                        'answer': answer,
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    })
                    st.rerun()
    
    with col_summary:
        if st.button("📊 Generate Summary"):
            with st.spinner("📝 Generating summary..."):
                summary = generate_summary()
                st.session_state.chat_history.append({
                    'question': 'Meeting Summary',
                    'answer': summary,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                })
                st.rerun()
    
    # Display Q&A history
    st.subheader("💡 AI Responses")
    
    if st.session_state.chat_history:
        for item in reversed(st.session_state.chat_history[-5:]):
            st.markdown(f"""
            <div class="ai-response-box">
                <strong>❓ {item['question']}</strong> <small>[{item['timestamp']}]</small><br><br>
                {item['answer']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("💭 Ask questions about your meeting and AI will respond here!")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🔒 Your API key is stored locally in your browser session</p>
    <p>📊 Project: prj-genai-poc-glob-5bcc | Model: Gemini 2.0 Flash</p>
</div>
""", unsafe_allow_html=True)
