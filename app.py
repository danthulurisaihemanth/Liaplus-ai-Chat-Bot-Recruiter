"""
Liaplus AI Chatbot for Candidate Shortlisting
Main application file with Flask API and ML integration
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import openai
import os
import json
import logging
from datetime import datetime
import sqlite3
from werkzeug.security import generate_password_hash
import joblib
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

class LiaplusAIChatbot:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.classifier = MultinomialNB()
        self.model_pipeline = None
        self.job_requirements = self._load_job_requirements()
        self.conversation_history = []
        
    def _load_job_requirements(self):
        """Load job requirements and criteria"""
        return {
            "prompt_engineer": {
                "required_skills": [
                    "prompt engineering", "nlp", "machine learning", "python",
                    "ai models", "gpt", "bert", "transformers", "natural language processing",
                    "data analysis", "experimentation", "collaboration"
                ],
                "experience_keywords": [
                    "prompt design", "ai assistant", "llm", "language models",
                    "performance optimization", "model fine-tuning", "research"
                ],
                "minimum_score": 0.6
            }
        }
    
    def preprocess_text(self, text):
        """Clean and preprocess text input"""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def calculate_candidate_score(self, candidate_text, role="prompt_engineer"):
        """Calculate candidate compatibility score using ML"""
        try:
            requirements = self.job_requirements.get(role, {})
            required_skills = requirements.get("required_skills", [])
            experience_keywords = requirements.get("experience_keywords", [])
            
            # Preprocess candidate text
            processed_text = self.preprocess_text(candidate_text)
            
            # Calculate skill match score
            skill_matches = sum(1 for skill in required_skills if skill in processed_text)
            skill_score = skill_matches / len(required_skills)
            
            # Calculate experience score
            exp_matches = sum(1 for keyword in experience_keywords if keyword in processed_text)
            exp_score = exp_matches / len(experience_keywords) if experience_keywords else 0
            
            # Combined score with weights
            final_score = (skill_score * 0.7) + (exp_score * 0.3)
            
            return {
                "overall_score": round(final_score, 2),
                "skill_score": round(skill_score, 2),
                "experience_score": round(exp_score, 2),
                "matched_skills": skill_matches,
                "matched_experience": exp_matches,
                "recommendation": "SHORTLISTED" if final_score >= requirements.get("minimum_score", 0.6) else "NOT_SHORTLISTED"
            }
            
        except Exception as e:
            logger.error(f"Error calculating candidate score: {str(e)}")
            return {"error": "Score calculation failed"}
    
    def generate_ai_response(self, user_input, context=""):
        """Generate AI response using rule-based system with ML enhancement"""
        try:
            # Preprocess input
            processed_input = self.preprocess_text(user_input)
            
            # Intent classification
            if any(word in processed_input for word in ["hello", "hi", "hey", "start"]):
                return self._get_greeting_response()
            
            elif any(word in processed_input for word in ["apply", "application", "job", "position"]):
                return self._get_application_response()
            
            elif any(word in processed_input for word in ["experience", "skills", "background"]):
                return self._get_experience_inquiry()
            
            elif any(word in processed_input for word in ["prompt", "engineering", "nlp", "ai"]):
                return self._get_technical_response()
            
            elif any(word in processed_input for word in ["help", "support", "question"]):
                return self._get_help_response()
            
            else:
                return self._get_default_response()
                
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request. Please try again."
    
    def _get_greeting_response(self):
        return """Hello! Welcome to Liaplus AI Assistant. I'm here to help you with the Prompt Engineer position application process.

I can assist you with:
• Understanding the role requirements
• Evaluating your qualifications
• Guiding you through the application process
• Answering questions about prompt engineering

How can I help you today?"""
    
    def _get_application_response(self):
        return """Great! You're interested in applying for the Prompt Engineer position at Liaplus.

**Key Requirements:**
• Strong interest and experience in Prompt Engineering
• Projects related to Prompt Engineering
• Skills in NLP, ML, Python, and AI models
• Experience with data analysis and experimentation

**Next Steps:**
1. Share your relevant experience and projects
2. I'll evaluate your qualifications
3. If suitable, you'll receive an assignment within 1-2 days

Please tell me about your prompt engineering experience and projects."""
    
    def _get_experience_inquiry(self):
        return """I'd love to learn more about your background! Please share:

• Your experience with prompt engineering projects
• Technical skills (Python, NLP, ML frameworks)
• Experience with AI models (GPT, BERT, etc.)
• Any relevant research or innovation work
• Data analysis and experimentation experience

The more details you provide, the better I can evaluate your fit for the role."""
    
    def _get_technical_response(self):
        return """Excellent! Prompt engineering is at the core of what we do at Liaplus.

**Our Focus Areas:**
• Design & test prompt strategies for AI optimization
• Collaborate with cross-functional teams
• Analyze prompt effectiveness using metrics
• Document experiments and insights
• Stay updated with latest NLP research

What specific prompt engineering projects or techniques have you worked with?"""
    
    def _get_help_response(self):
        return """I'm here to help! You can ask me about:

• Role requirements and responsibilities
• Application process and timeline
• Technical questions about prompt engineering
• Company information and culture
• Next steps in the hiring process

What specific information would you like to know?"""
    
    def _get_default_response(self):
        return """I understand you're interested in the Prompt Engineer position. 

To better assist you, could you please:
• Tell me about your prompt engineering experience
• Share relevant projects you've worked on
• Ask specific questions about the role

I'm here to help evaluate your qualifications and guide you through the application process!"""

# Initialize chatbot
chatbot = LiaplusAIChatbot()

# Database setup
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('liaplus_chatbot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_input TEXT,
            bot_response TEXT,
            user_session TEXT,
            candidate_score REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            experience_text TEXT,
            overall_score REAL,
            recommendation TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# API Routes
@app.route('/')
def home():
    """Main chatbot interface"""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        data = request.get_json()
        user_input = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not user_input:
            return jsonify({'error': 'Message is required'}), 400
        
        # Generate AI response
        bot_response = chatbot.generate_ai_response(user_input)
        
        # Store conversation
        conn = sqlite3.connect('liaplus_chatbot.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversations (user_input, bot_response, user_session)
            VALUES (?, ?, ?)
        ''', (user_input, bot_response, session_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'response': bot_response,
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Chat API error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/evaluate', methods=['POST'])
def evaluate_candidate():
    """Evaluate candidate qualifications"""
    try:
        data = request.get_json()
        candidate_text = data.get('experience', '')
        name = data.get('name', '')
        email = data.get('email', '')
        
        if not candidate_text:
            return jsonify({'error': 'Experience text is required'}), 400
        
        # Calculate candidate score
        evaluation = chatbot.calculate_candidate_score(candidate_text)
        
        # Store candidate data
        conn = sqlite3.connect('liaplus_chatbot.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO candidates (name, email, experience_text, overall_score, recommendation)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, email, candidate_text, evaluation.get('overall_score', 0), 
              evaluation.get('recommendation', 'NOT_EVALUATED')))
        conn.commit()
        conn.close()
        
        return jsonify({
            'evaluation': evaluation,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Evaluation API error: {str(e)}")
        return jsonify({'error': 'Evaluation failed'}), 500

@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    """Get all evaluated candidates"""
    try:
        conn = sqlite3.connect('liaplus_chatbot.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, email, overall_score, recommendation, timestamp
            FROM candidates ORDER BY overall_score DESC
        ''')
        
        candidates = []
        for row in cursor.fetchall():
            candidates.append({
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'score': row[3],
                'recommendation': row[4],
                'timestamp': row[5]
            })
        
        conn.close()
        return jsonify({'candidates': candidates})
        
    except Exception as e:
        logger.error(f"Get candidates error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve candidates'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)