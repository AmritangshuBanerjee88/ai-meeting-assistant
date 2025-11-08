"""
Advanced AI Meeting Assistant with Real-time Capabilities
"""
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
import numpy as np
from google.cloud import speech_v1 as speech
import queue
import threading
from datetime import datetime
import time
from model_router import ModelRouter
from question_detector import QuestionDetector

# Page config
st.set_page_config(
    page_title="🤖 AI Meeting Assistant - Advanced",
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
    .live-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #ff4444;
        animation: pulse 2s infinite;
        margin-right: 10px;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    .question-detected {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .auto-response {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .sentiment-positive { color: #28a745; font-weight: bold; }
    .sentiment-negative { color: #dc3545; font-weight: bold; }
    .sentiment-neutral { color: #6c757d; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'meeting_context' not in st.session_state:
    st.session_state.meeting_context = []
if 'questions_detected' not in st.session_state:
    st.session_state.questions_detected = []
if 'auto_responses' not in st.session_state:
    st.session_state.auto_responses = []
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False
if 'audio_buffer' not in st.session_state:
    st.session_state.audio_buffer = queue.Queue()
if 'model_router' not in st.session_state:
    st.session_state.model_router = None
if 'question_detector' not in st.session_state:
    st.session_state.question_detector = QuestionDetector()

def initialize_models(project_id, api_key):
    """Initialize AI models"""
    try:
        st.session_state.model_router = ModelRouter(
            project_id=project_id,
            api_key=api_key
        )
        return True
    except Exception as e:
        st.error(f"Error initializing models: {str(e)}")
        return False

def process_audio_chunk(audio_chunk):
    """Process audio chunk for speech-to-text"""
    # Add to buffer for processing
    st.session_state.audio_buffer.put(audio_chunk)

def get_context_text():
    """Build context from recent transcripts"""
    context_lines = []
    for item in st.session_state.meeting_context[-20:]:
        context_lines.append(f"[{item['timestamp']}] {item['speaker']}: {item['text']}")
    return "\n".join(context_lines)

def auto_respond_to_question(question_data):
    """Automatically respond to detected question"""
    if not st.session_state.model_router:
        return
    
    question = question_data['text']
    context = get_context_text()
    
    # Get response from appropriate model
    result = st.session_state.model_router.route_and_query(question, context)
    
    # Store auto-response
    st.session_state.auto_responses.append({
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'question': question,
        'response': result['response'],
        'model': result['model_used'],
        'complexity': result['complexity'],
        'sentiment': question_data['sentiment']
    })

# Main UI
st.markdown('<h1 class="main-header">🤖 AI Meeting Assistant - Advanced</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # GCP Configuration
    project_id = st.text_input("GCP Project ID", value="prj-genai-poc-glob-5bcc")
    api_key = st.text_input("Google AI API Key", type="password")
    
    if st.button("Initialize Models"):
        if api_key and project_id:
            if initialize_models(project_id, api_key):
                st.success("✅ Models initialized!")
        else:
            st.error("Please provide Project ID and API Key")
    
    st.divider()
    
    # Auto-Response Settings
    st.header("🤖 Auto-Response")
    auto_response_enabled = st.checkbox("Enable Auto-Response", value=True)
    confidence_threshold = st.slider("Question Confidence Threshold", 0.5, 1.0, 0.75, 0.05)
    
    # Model Selection
    st.header("🎯 Model Routing")
    st.info("""
    **Simple Questions** → Gemini Flash
    **Moderate Questions** → Gemini Pro
    **Complex Questions** → Claude Sonnet 4.5
    """)
    
    manual_model = st.selectbox(
        "Manual Override",
        ["Auto (Smart Routing)", "Gemini Flash", "Gemini Pro", "Claude Sonnet"]
    )
    
    st.divider()
    
    # Stats
    st.header("📊 Session Stats")
    st.metric("Transcripts", len(st.session_state.meeting_context))
    st.metric("Questions Detected", len(st.session_state.questions_detected))
    st.metric("Auto-Responses", len(st.session_state.auto_responses))

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["🎙️ Live Recording", "📝 Transcript", "❓ Q&A", "📊 Summary"])

with tab1:
    st.header("Real-time Audio & Screen Capture")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎤 Microphone")
        
        if st.session_state.is_recording:
            st.markdown('<div class="live-indicator"></div> LIVE', unsafe_allow_html=True)
        
        # WebRTC Audio Streamer
        webrtc_ctx = webrtc_streamer(
            key="speech-to-text",
            mode=WebRtcMode.SENDONLY,
            rtc_configuration=RTCConfiguration(
                {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
            ),
            media_stream_constraints={"video": False, "audio": True},
            audio_frame_callback=process_audio_chunk,
        )
        
        st.session_state.is_recording = webrtc_ctx.state.playing
    
    with col2:
        st.subheader("🖥️ Screen Capture")
        st.info("💡 Use browser's built-in screen capture or meeting app's recording feature")
        st.markdown("""
        **How to capture:**
        1. Start your meeting (Teams/Meet/Zoom)
        2. Enable meeting recording in the app
        3. Or use browser screen capture extension
        """)

with tab2:
    st.header("📝 Live Transcript")
    
    # Manual transcript entry
    with st.expander("➕ Add Transcript Manually"):
        with st.form("manual_transcript"):
            speaker = st.text_input("Speaker")
            text = st.text_area("Text")
            submitted = st.form_submit_button("Add")
            
            if submitted and speaker and text:
                # Add to context
                st.session_state.meeting_context.append({
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'speaker': speaker,
                    'text': text
                })
                
                # Check for questions
                questions = st.session_state.question_detector.extract_questions(text)
                
                for q in questions:
                    st.session_state.questions_detected.append(q)
                    
                    # Auto-respond if enabled
                    if auto_response_enabled and q['confidence'] >= confidence_threshold:
                        auto_respond_to_question(q)
                
                st.rerun()
    
    # Display transcript
    if st.session_state.meeting_context:
        for item in reversed(st.session_state.meeting_context[-20:]):
            st.markdown(f"""
            **[{item['timestamp']}] {item['speaker']}:**  
            {item['text']}
            """)
            st.divider()
    else:
        st.info("No transcript yet. Start recording or add manually.")

with tab3:
    st.header("❓ Questions & Auto-Responses")
    
    # Detected questions
    st.subheader("🔍 Detected Questions")
    
    if st.session_state.questions_detected:
        for q in reversed(st.session_state.questions_detected[-10:]):
            sentiment_class = f"sentiment-{q['sentiment']['sentiment']}"
            st.markdown(f"""
            <div class="question-detected">
                <strong>Question:</strong> {q['text']}<br>
                <small>Confidence: {q['confidence']:.0%} | 
                Sentiment: <span class="{sentiment_class}">{q['sentiment']['sentiment'].upper()}</span>
                (Polarity: {q['sentiment']['polarity']:.2f})</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No questions detected yet")
    
    st.divider()
    
    # Auto-responses
    st.subheader("🤖 Auto-Responses")
    
    if st.session_state.auto_responses:
        for resp in reversed(st.session_state.auto_responses[-10:]):
            sentiment_class = f"sentiment-{resp['sentiment']['sentiment']}"
            st.markdown(f"""
            <div class="auto-response">
                <strong>❓ Question:</strong> {resp['question']}<br>
                <small>Sentiment: <span class="{sentiment_class}">{resp['sentiment']['sentiment'].upper()}</span> | 
                Model: {resp['model']} | Complexity: {resp['complexity']}</small><br><br>
                <strong>💡 Response:</strong><br>
                {resp['response']}
                <br><small>[{resp['timestamp']}]</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No auto-responses yet")
    
    st.divider()
    
    # Manual question
    st.subheader("💬 Ask Manually")
    manual_question = st.text_input("Your question:")
    
    if st.button("🔍 Ask"):
        if manual_question and st.session_state.model_router:
            context = get_context_text()
            
            # Determine model based on selection
            if manual_model == "Auto (Smart Routing)":
                result = st.session_state.model_router.route_and_query(manual_question, context)
            else:
                complexity_map = {
                    "Gemini Flash": "simple",
                    "Gemini Pro": "moderate",
                    "Claude Sonnet": "complex"
                }
                result = st.session_state.model_router.route_and_query(
                    manual_question, 
                    context, 
                    complexity=complexity_map.get(manual_model, "moderate")
                )
            
            st.success(f"**Model Used:** {result['model_used']}")
            st.markdown(f"**Response:**\n\n{result['response']}")

with tab4:
    st.header("📊 Meeting Summary")
    
    if st.button("Generate Summary"):
        if st.session_state.model_router and st.session_state.meeting_context:
            context = get_context_text()
            
            summary_prompt = f"""Analyze this meeting and provide a comprehensive summary:

{context}

Include:
1. Key Discussion Points
2. Decisions Made
3. Action Items
4. Questions Asked
5. Sentiment Analysis
6. Next Steps"""
            
            with st.spinner("Generating summary..."):
                result = st.session_state.model_router.route_and_query(
                    summary_prompt, 
                    context, 
                    complexity='complex'
                )
            
            st.markdown(f"**Generated by:** {result['model_used']}")
            st.markdown(result['response'])
        else:
            st.warning("No meeting content to summarize")
    
    # Download options
    st.divider()
    st.subheader("📥 Export")
    
    if st.button("Download Full Transcript"):
        transcript = "\n".join([
            f"[{item['timestamp']}] {item['speaker']}: {item['text']}"
            for item in st.session_state.meeting_context
        ])
        st.download_button(
            "Download TXT",
            transcript,
            file_name=f"meeting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>🎯 Smart Model Routing | 🔒 Secure Processing | ⚡ Real-time Responses</p>
    <p>Powered by Vertex AI | GCP Project: prj-genai-poc-glob-5bcc</p>
</div>
""", unsafe_allow_html=True)
