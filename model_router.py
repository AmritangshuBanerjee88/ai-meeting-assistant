"""
Smart Model Router - Routes questions to appropriate AI model
"""
import google.generativeai as genai
from anthropic import AnthropicVertex
import re

class ModelRouter:
    def __init__(self, project_id, api_key, region="us-central1"):
        self.project_id = project_id
        self.region = region
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Initialize models
        self.gemini_flash = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.gemini_pro = genai.GenerativeModel('gemini-1.5-pro')
        
        # Initialize Claude (Vertex AI)
        try:
            self.claude = AnthropicVertex(project_id=project_id, region=region)
            self.claude_available = True
        except:
            self.claude_available = False
        
        # Complexity keywords
        self.complex_keywords = {
            'analyze', 'compare', 'contrast', 'evaluate', 'explain',
            'strategic', 'architecture', 'design', 'implement',
            'calculate', 'estimate', 'predict', 'legal', 'compliance'
        }
        
    def classify_question(self, question):
        """Classify question complexity"""
        question_lower = question.lower()
        word_count = len(question.split())
        
        # Check for complex keywords
        has_complex = any(kw in question_lower for kw in self.complex_keywords)
        
        # Multiple questions
        multi_part = question.count('?') > 1 or ' and ' in question_lower
        
        if has_complex or word_count > 25:
            return 'complex'
        elif multi_part or word_count > 15:
            return 'moderate'
        else:
            return 'simple'
    
    def route_and_query(self, question, context, complexity=None):
        """Route question to appropriate model and get response"""
        
        if complexity is None:
            complexity = self.classify_question(question)
        
        prompt = f"""Meeting Context:
{context}

Question: {question}

Provide a clear, concise answer based on the meeting context."""
        
        # Route based on complexity
        if complexity == 'simple':
            model_name = "Gemini 2.0 Flash"
            response = self._query_gemini_flash(prompt)
        elif complexity == 'moderate':
            model_name = "Gemini 1.5 Pro"
            response = self._query_gemini_pro(prompt)
        else:  # complex
            if self.claude_available:
                model_name = "Claude Sonnet 4.5"
                response = self._query_claude(prompt)
            else:
                model_name = "Gemini 1.5 Pro"
                response = self._query_gemini_pro(prompt)
        
        return {
            'response': response,
            'model_used': model_name,
            'complexity': complexity
        }
    
    def _query_gemini_flash(self, prompt):
        """Query Gemini Flash (fast)"""
        try:
            chat = self.gemini_flash.start_chat()
            response = chat.send_message(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _query_gemini_pro(self, prompt):
        """Query Gemini Pro (balanced)"""
        try:
            chat = self.gemini_pro.start_chat()
            response = chat.send_message(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _query_claude(self, prompt):
        """Query Claude Sonnet (advanced)"""
        try:
            message = self.claude.messages.create(
                model="claude-3-5-sonnet-v2@20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return f"Error: {str(e)}"
