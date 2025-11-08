"""
Question Detection and Sentiment Analysis
"""
import re
from textblob import TextBlob

class QuestionDetector:
    def __init__(self):
        self.question_words = {
            'what', 'when', 'where', 'who', 'whom', 'whose', 'which',
            'why', 'how', 'can', 'could', 'would', 'should', 'will',
            'is', 'are', 'was', 'were', 'do', 'does', 'did'
        }
    
    def is_question(self, text):
        """Detect if text is a question"""
        if not text:
            return False, 0.0
        
        text = text.strip()
        confidence = 0.0
        
        # Ends with ?
        if text.endswith('?'):
            confidence += 0.6
        
        # Starts with question word
        first_word = text.split()[0].lower().rstrip('?,:;')
        if first_word in self.question_words:
            confidence += 0.3
        
        # Contains question word in first 3 words
        first_three = ' '.join(text.split()[:3]).lower()
        if any(qw in first_three for qw in self.question_words):
            confidence += 0.2
        
        is_q = confidence >= 0.5
        return is_q, min(confidence, 1.0)
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of text"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            if polarity > 0.1:
                sentiment = 'positive'
            elif polarity < -0.1:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            return {
                'sentiment': sentiment,
                'polarity': polarity,
                'subjectivity': subjectivity,
                'confidence': abs(polarity)
            }
        except:
            return {
                'sentiment': 'neutral',
                'polarity': 0.0,
                'subjectivity': 0.0,
                'confidence': 0.0
            }
    
    def extract_questions(self, text):
        """Extract questions from text"""
        sentences = re.split(r'[.!?]+', text)
        questions = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                is_q, confidence = self.is_question(sentence)
                if is_q:
                    sentiment = self.analyze_sentiment(sentence)
                    questions.append({
                        'text': sentence,
                        'confidence': confidence,
                        'sentiment': sentiment
                    })
        
        return questions
