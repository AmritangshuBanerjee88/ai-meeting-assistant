"""
Advanced AI Meeting Assistant - Cloud Compatible Version
Real-time question detection and multi-model routing
"""
import streamlit as st
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
    .model-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-left: 0.5rem;
    }
    .model-flash { background: #e3f2fd; color: #1976d2; }
    .model-pro { background: #f3e5f5; color: #7b1fa2; }
    .model-claude { background: #fff3e0; color: #f57c00; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'meeting_context' not in st.session_state:
    st.session_state.meeting_context = []
if 'questions_detected' not in st.session_state:
    st.session_state.questions_detected = []
if 'auto_responses' not in st.session_state:
    st.session_state.auto_responses = []
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

def get_context_text():
    """Build context from recent transcripts"""
    if not st.session_state.meeting_context:
        return ""
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
    
    if not context:
        return
    
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
st.markdown('<p style="text-align: center; color: #666;">Smart Model Routing | Real-time Q&A | Sentiment Analysis</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
        # GCP Configuration
    with st.expander("🔑 API Settings", expanded=True):
        project_id = st.text_input("GCP Project ID", value="prj-genai-poc-glob-5bcc")
        api_key = st.text_input(
            "Google AI API Key", 
            type="password",
            placeholder="Enter your API key here",
            help="🔒 Keep this private! Never share your API key."
        )
        
        if st.button("🚀 Initialize Models", type="primary"):
            if api_key and project_id:
                with st.spinner("Initializing AI models..."):
                    if initialize_models(project_id, api_key):
                        st.success("✅ Models initialized!")
                        st.balloons()
            else:
                st.error("Please provide Project ID and API Key")
    
    st.divider()
    
    # Auto-Response Settings
    st.header("🤖 Auto-Response")
    auto_response_enabled = st.checkbox("Enable Auto-Response", value=True,
                                       help="Automatically respond to detected questions")
    confidence_threshold = st.slider("Question Confidence", 0.5, 1.0, 0.75, 0.05,
                                    help="Minimum confidence to trigger auto-response")
    
    st.divider()
    
    # Model Selection
    st.header("🎯 Model Routing")
    st.caption("How questions are routed:")
    st.markdown("""
    - 🟦 **Simple** → Gemini Flash
    - 🟪 **Moderate** → Gemini Pro  
    - 🟧 **Complex** → Claude Sonnet 4.5
    """)
    
    manual_model = st.selectbox(
        "Manual Override",
        ["Auto (Smart Routing)", "Gemini Flash", "Gemini Pro", "Claude Sonnet"],
        help="Force a specific model for manual questions"
    )
    
    st.divider()
    
    # Stats
    st.header("📊 Session Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Transcripts", len(st.session_state.meeting_context))
        st.metric("Questions", len(st.session_state.questions_detected))
    with col2:
        st.metric("Auto-Responses", len(st.session_state.auto_responses))
        
        # Model usage stats
        if st.session_state.auto_responses:
            models_used = [r['model'] for r in st.session_state.auto_responses]
            most_used = max(set(models_used), key=models_used.count) if models_used else "N/A"
            st.metric("Most Used", most_used.split()[0])

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📝 Transcript", "❓ Q&A Detection", "🤖 Auto-Responses", "📊 Summary"])

with tab1:
    st.header("📝 Meeting Transcript")
    
    st.info("""
    💡 **How to use during meetings:**
    1. Listen to what participants say
    2. Quickly type: Speaker name + their statement
    3. Click "Add" - AI will auto-detect questions
    4. Get instant AI responses!
    """)
    
    # Manual transcript entry
    with st.form("manual_transcript", clear_on_submit=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            speaker = st.text_input("Speaker", placeholder="e.g., John")
        with col2:
            text = st.text_area("What they said", placeholder="Type what was said...", height=100)
        
        col_submit, col_clear = st.columns([3, 1])
        with col_submit:
            submitted = st.form_submit_button("➕ Add to Transcript", type="primary", use_container_width=True)
        with col_clear:
            if st.form_submit_button("🗑️ Clear", use_container_width=True):
                st.session_state.meeting_context = []
                st.session_state.questions_detected = []
                st.session_state.auto_responses = []
                st.rerun()
        
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
                    if st.session_state.model_router:
                        auto_respond_to_question(q)
            
            st.rerun()
    
    st.divider()
    
    # Display transcript
    st.subheader("Recent Transcript")
    
    if st.session_state.meeting_context:
        for item in reversed(st.session_state.meeting_context[-15:]):
            with st.container():
                st.markdown(f"""
                **[{item['timestamp']}] {item['speaker']}:**  
                {item['text']}
                """)
                st.divider()
    else:
        st.info("👋 No transcript yet. Add some meeting content above to get started!")

with tab2:
    st.header("❓ Question Detection & Sentiment")
    
    st.caption(f"Auto-response: {'✅ Enabled' if auto_response_enabled else '❌ Disabled'} | Threshold: {confidence_threshold:.0%}")
    
    if st.session_state.questions_detected:
        for idx, q in enumerate(reversed(st.session_state.questions_detected[-10:])):
            sentiment_class = f"sentiment-{q['sentiment']['sentiment']}"
            
            # Determine if this triggered auto-response
            triggered = q['confidence'] >= confidence_threshold and auto_response_enabled
            
            st.markdown(f"""
            <div class="question-detected">
                <strong>Question #{len(st.session_state.questions_detected) - idx}:</strong> {q['text']}<br>
                <small>
                    📊 Confidence: {q['confidence']:.0%} | 
                    Sentiment: <span class="{sentiment_class}">{q['sentiment']['sentiment'].upper()}</span>
                    (Polarity: {q['sentiment']['polarity']:.2f}) |
                    {'✅ Auto-responded' if triggered else '⏭️ Skipped (below threshold)'}
                </small>
            </div>
            """, unsafe_allow_html=True)
            st.divider()
    else:
        st.info("🔍 No questions detected yet. Add transcript with questions to see them here!")
        
        st.caption("**Examples of questions:**")
        st.markdown("""
        - "What is the deadline for this project?"
        - "Can you explain the architecture?"
        - "How do we implement this feature?"
        """)

with tab3:
    st.header("🤖 Automatic AI Responses")
    
    st.caption("AI automatically responds to detected questions based on meeting context")
    
    if st.session_state.auto_responses:
        for idx, resp in enumerate(reversed(st.session_state.auto_responses[-10:])):
            sentiment_class = f"sentiment-{resp['sentiment']['sentiment']}"
            
            # Model badge
            model_class = "model-flash"
            if "Pro" in resp['model']:
                model_class = "model-pro"
            elif "Claude" in resp['model']:
                model_class = "model-claude"
            
            st.markdown(f"""
            <div class="auto-response">
                <strong>❓ Question:</strong> {resp['question']}
                <span class="{model_class} model-badge">{resp['model']}</span>
                <br>
                <small>
                    Sentiment: <span class="{sentiment_class}">{resp['sentiment']['sentiment'].upper()}</span> | 
                    Complexity: {resp['complexity']} | 
                    Time: {resp['timestamp']}
                </small>
                <br><br>
                <strong>💡 AI Response:</strong><br>
                {resp['response']}
            </div>
            """, unsafe_allow_html=True)
            st.divider()
    else:
        st.info("💭 No auto-responses yet. Add transcripts with questions to see AI responses!")
    
    st.divider()
    
    # Manual question
    st.subheader("💬 Ask Manually")
    
    with st.form("manual_question"):
        manual_question = st.text_input("Your question:", placeholder="e.g., What were the key decisions?")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            ask_submitted = st.form_submit_button("🔍 Ask", type="primary", use_container_width=True)
        with col2:
            st.caption(f"Model: {manual_model.split()[0]}")
    
    if ask_submitted and manual_question:
        if st.session_state.model_router:
            context = get_context_text()
            
            if context:
                with st.spinner("🤔 Thinking..."):
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
                    
                    st.success(f"**Model Used:** {result['model_used']} | **Complexity:** {result['complexity']}")
                    st.markdown(f"**Response:**\n\n{result['response']}")
            else:
                st.warning("⚠️ No meeting context available. Add some transcript first!")
        else:
            st.error("⚠️ Please initialize models first (sidebar)")

with tab4:
    st.header("📊 Meeting Summary & Export")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("📝 Generate AI Summary", type="primary", use_container_width=True):
            if st.session_state.model_router and st.session_state.meeting_context:
                context = get_context_text()
                
                summary_prompt = """Analyze this meeting and provide a comprehensive summary with:

1. **Key Discussion Points** - Main topics covered
2. **Decisions Made** - Concrete decisions and agreements  
3. **Action Items** - Tasks and assignments with owners
4. **Questions Raised** - Important questions discussed
5. **Sentiment Analysis** - Overall tone of the meeting
6. **Next Steps** - Recommended follow-up actions

Be specific and reference actual discussion points."""
                
                with st.spinner("🤖 Generating comprehensive summary..."):
                    result = st.session_state.model_router.route_and_query(
                        summary_prompt, 
                        context, 
                        complexity='complex'
                    )
                
                st.success(f"**Generated by:** {result['model_used']}")
                st.markdown("---")
                st.markdown(result['response'])
            else:
                st.warning("⚠️ No meeting content to summarize or models not initialized")
    
    with col2:
        st.metric("Total Items", len(st.session_state.meeting_context))
        st.metric("Questions", len(st.session_state.questions_detected))
        st.metric("Responses", len(st.session_state.auto_responses))
    
    st.divider()
    
    # Download options
    st.subheader("📥 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.meeting_context:
            transcript = "\n".join([
                f"[{item['timestamp']}] {item['speaker']}: {item['text']}"
                for item in st.session_state.meeting_context
            ])
            st.download_button(
                "📄 Download Transcript",
                transcript,
                file_name=f"meeting_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    with col2:
        if st.session_state.questions_detected:
            questions_export = "\n\n".join([
                f"Q: {q['text']}\nConfidence: {q['confidence']:.0%}\nSentiment: {q['sentiment']['sentiment']}"
                for q in st.session_state.questions_detected
            ])
            st.download_button(
                "❓ Download Questions",
                questions_export,
                file_name=f"questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                use_container_width=True
            )
    
    with col3:
        if st.session_state.auto_responses:
            responses_export = "\n\n".join([
                f"[{r['timestamp']}]\nQ: {r['question']}\nModel: {r['model']}\nA: {r['response']}"
                for r in st.session_state.auto_responses
            ])
            st.download_button(
                "🤖 Download Responses",
                responses_export,
                file_name=f"ai_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                use_container_width=True
            )

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🎯 Smart Model Routing • 🔒 Secure Processing • ⚡ Real-time Responses</p>
    <p>Powered by Vertex AI • GCP Project: prj-genai-poc-glob-5bcc</p>
</div>
""", unsafe_allow_html=True)
