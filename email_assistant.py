# AI-Powered Email Communication Assistant - Backend
# Requirements: pip install flask flask-cors transformers torch sqlite3 pandas numpy scikit-learn sentence-transformers

import sqlite3
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import datetime
import json
import logging
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings("ignore")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailAssistant:
    def __init__(self):
        """Initialize the Email Assistant with AI models and database"""
        self.setup_database()
        self.load_ai_models()
        self.load_knowledge_base()
        self.urgent_keywords = [
            'urgent', 'critical', 'emergency', 'asap', 'immediately', 'cannot access',
            'system down', 'not working', 'broken', 'error', 'failed', 'blocked',
            'deadline', 'production', 'outage', 'severe', 'major issue'
        ]
        self.sentiment_model = None
        self.response_templates = self.load_response_templates()
    
    def setup_database(self):
        """Setup SQLite database for storing emails and responses"""
        self.conn = sqlite3.connect('email_assistant.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Create emails table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                date_received TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                priority TEXT DEFAULT 'normal',
                sentiment TEXT DEFAULT 'neutral',
                keywords TEXT,
                contact_info TEXT,
                requirements TEXT,
                ai_response TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Create knowledge base table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                keywords TEXT NOT NULL,
                solution TEXT NOT NULL,
                escalation_info TEXT
            )
        ''')
        
        self.conn.commit()
        logger.info("Database setup completed")
    
    def load_ai_models(self):
        """Load pre-trained AI models for sentiment analysis and text processing"""
        try:
            # Load sentiment analysis model
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                return_all_scores=True
            )
            
            # Load sentence transformer for semantic similarity
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize TF-IDF for keyword extraction
            self.tfidf = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            logger.info("AI models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading AI models: {e}")
            # Fallback to rule-based approaches
            self.sentiment_analyzer = None
            self.sentence_model = None
    
    def load_knowledge_base(self):
        """Load knowledge base with predefined solutions"""
        knowledge_entries = [
            {
                'category': 'account_access',
                'keywords': 'login, password, access, account, locked, authentication, signin, credentials',
                'solution': 'For account access issues: 1) Try clearing browser cache and cookies 2) Reset password using "Forgot Password" link 3) Check if caps lock is on 4) Try different browser or incognito mode',
                'escalation_info': 'If issue persists after basic troubleshooting, escalate to security team for account unlock'
            },
            {
                'category': 'technical_issues',
                'keywords': 'error, bug, broken, not working, technical, system, crash, freeze, slow',
                'solution': 'For technical issues: 1) Check internet connection 2) Clear browser cache 3) Update browser to latest version 4) Try different device 5) Check system status page',
                'escalation_info': 'Complex technical issues should be forwarded to technical support team'
            },
            {
                'category': 'billing_payment',
                'keywords': 'billing, payment, invoice, charge, refund, subscription, price, cost, money',
                'solution': 'For billing inquiries: 1) Check your billing portal for invoice details 2) Verify payment method is valid 3) Contact billing support for refund requests',
                'escalation_info': 'Billing disputes require finance team approval'
            },
            {
                'category': 'feature_request',
                'keywords': 'feature, request, suggestion, enhancement, improvement, new, add, update',
                'solution': 'Thank you for your feature suggestion! We appreciate your feedback. Please visit our feature request portal to submit detailed requirements.',
                'escalation_info': 'Feature requests should be logged with product team for roadmap consideration'
            },
            {
                'category': 'integration_api',
                'keywords': 'api, integration, webhook, developer, code, sdk, documentation, endpoint',
                'solution': 'For API/integration support: 1) Check our developer documentation 2) Verify API key is valid 3) Ensure proper authentication headers 4) Check rate limits',
                'escalation_info': 'Complex integration issues require developer support team assistance'
            }
        ]
        
        # Insert knowledge base entries
        for entry in knowledge_entries:
            self.cursor.execute('''
                INSERT OR REPLACE INTO knowledge_base (category, keywords, solution, escalation_info)
                VALUES (?, ?, ?, ?)
            ''', (entry['category'], entry['keywords'], entry['solution'], entry['escalation_info']))
        
        self.conn.commit()
        logger.info("Knowledge base loaded successfully")
    
    def load_response_templates(self) -> Dict[str, str]:
        """Load response templates based on sentiment and priority"""
        return {
            'urgent_negative': """Dear {sender_name},

Thank you for reaching out, and I sincerely apologize for the urgent issue you're experiencing. I understand how critical this situation is for you.

I'm prioritizing your request and escalating it to our specialized team immediately. Here's what we're doing to resolve this:

{solution}

Expected resolution time: Within 2 hours
Ticket reference: #{ticket_id}

I'll personally monitor this case and update you every 30 minutes until resolved. You can also reach our emergency support line at +1-800-SUPPORT.

We truly appreciate your patience during this critical situation.

Best regards,
AI Support Assistant
Customer Success Team""",
            
            'normal_positive': """Hello {sender_name},

Thank you for your message! We're delighted to hear from you and appreciate your continued trust in our services.

{solution}

{additional_info}

If you need any further assistance or have additional questions, please don't hesitate to reach out. We're here to ensure you have the best possible experience.

Best regards,
AI Support Assistant
Customer Success Team""",
            
            'normal_neutral': """Hello {sender_name},

Thank you for contacting us. We're here to help with your inquiry.

{solution}

{additional_info}

If this doesn't resolve your issue or if you have any other questions, please let us know. We're committed to providing you with the support you need.

Best regards,
AI Support Assistant
Customer Success Team""",
            
            'urgent_neutral': """Dear {sender_name},

Thank you for your urgent request. I understand the importance of resolving this quickly.

I'm prioritizing your case and here's how we can address this:

{solution}

Expected resolution time: Within 4 hours
Priority ticket: #{ticket_id}

I'll keep you updated on our progress. For immediate assistance, please call our priority support line.

Best regards,
AI Support Assistant
Customer Success Team"""
        }
    
    def analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """Analyze sentiment of email text"""
        try:
            if self.sentiment_analyzer:
                results = self.sentiment_analyzer(text)
                # Get the highest scoring sentiment
                best_result = max(results[0], key=lambda x: x['score'])
                
                # Map model output to our categories
                label_mapping = {
                    'LABEL_0': 'negative',  # Negative
                    'LABEL_1': 'neutral',   # Neutral  
                    'LABEL_2': 'positive',  # Positive
                    'negative': 'negative',
                    'neutral': 'neutral',
                    'positive': 'positive'
                }
                
                sentiment = label_mapping.get(best_result['label'], 'neutral')
                confidence = best_result['score']
                
                return sentiment, confidence
            else:
                # Fallback rule-based sentiment analysis
                return self.rule_based_sentiment(text)
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return self.rule_based_sentiment(text)
    
    def rule_based_sentiment(self, text: str) -> Tuple[str, float]:
        """Fallback rule-based sentiment analysis"""
        positive_words = ['thank', 'great', 'excellent', 'love', 'amazing', 'perfect', 'wonderful']
        negative_words = ['problem', 'issue', 'error', 'broken', 'frustrated', 'angry', 'terrible', 'awful']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive', 0.7
        elif negative_count > positive_count:
            return 'negative', 0.7
        else:
            return 'neutral', 0.6
    
    def determine_priority(self, subject: str, body: str) -> str:
        """Determine email priority based on keywords and content"""
        text = (subject + " " + body).lower()
        
        urgent_score = sum(1 for keyword in self.urgent_keywords if keyword in text)
        
        # Check for time-sensitive language
        time_patterns = [
            r'\basap\b', r'\bimmediately\b', r'\burgent\b', r'\bcritical\b',
            r'\bemergency\b', r'\bdeadline\b', r'\btoday\b', r'\bnow\b'
        ]
        
        time_urgency = sum(1 for pattern in time_patterns if re.search(pattern, text))
        
        total_urgency = urgent_score + time_urgency
        
        return 'urgent' if total_urgency >= 2 else 'normal'
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from email text"""
        # Simple keyword extraction using common patterns
        keywords = []
        
        # Extract technical terms
        tech_patterns = [
            r'\b(api|sdk|webhook|integration|database|server|application)\b',
            r'\b(error code|bug|crash|timeout|connection)\b',
            r'\b(account|login|password|authentication|access)\b',
            r'\b(billing|payment|invoice|subscription|refund)\b'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.extend(matches)
        
        # Add urgent keywords found
        for keyword in self.urgent_keywords:
            if keyword in text.lower():
                keywords.append(keyword)
        
        return list(set(keywords))[:10]  # Return top 10 unique keywords
    
    def extract_contact_info(self, text: str) -> str:
        """Extract contact information from email"""
        contact_info = []
        
        # Phone number patterns
        phone_pattern = r'(\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        phones = re.findall(phone_pattern, text)
        if phones:
            contact_info.append(f"Phone: {phones[0]}")
        
        # Email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info.append(f"Alt Email: {emails[0]}")
        
        # Social media handles
        social_pattern = r'(@\w+|linkedin\.com/in/\w+|twitter\.com/\w+)'
        social = re.findall(social_pattern, text, re.IGNORECASE)
        if social:
            contact_info.append(f"Social: {social[0]}")
        
        return "; ".join(contact_info) if contact_info else "No additional contact info found"
    
    def extract_requirements(self, subject: str, body: str) -> str:
        """Extract customer requirements from email"""
        text = subject + " " + body
        
        requirement_patterns = [
            r'(need|want|require|request|looking for|help with) ([^.!?]*)',
            r'(can you|could you|please) ([^.!?]*)',
            r'(i would like|i want|i need) ([^.!?]*)'
        ]
        
        requirements = []
        for pattern in requirement_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:3]:  # Top 3 matches
                requirement = ' '.join(match).strip()
                if len(requirement) > 10:  # Filter out short matches
                    requirements.append(requirement)
        
        return "; ".join(requirements) if requirements else "General support inquiry"
    
    def find_best_solution(self, keywords: List[str], subject: str, body: str) -> Tuple[str, str]:
        """Find best solution from knowledge base using semantic matching"""
        text = subject + " " + body
        
        # Get all knowledge base entries
        self.cursor.execute('SELECT category, keywords, solution, escalation_info FROM knowledge_base')
        kb_entries = self.cursor.fetchall()
        
        best_match = None
        best_score = 0
        
        for category, kb_keywords, solution, escalation in kb_entries:
            # Calculate similarity score
            kb_keywords_list = [kw.strip() for kw in kb_keywords.split(',')]
            
            # Check for keyword overlap
            overlap = len(set(keywords) & set(kb_keywords_list))
            
            # Check for text similarity (simple approach)
            text_similarity = sum(1 for kw in kb_keywords_list if kw.lower() in text.lower())
            
            total_score = overlap * 2 + text_similarity
            
            if total_score > best_score:
                best_score = total_score
                best_match = (solution, escalation)
        
        if best_match:
            return best_match
        else:
            return ("I'll look into your inquiry and get back to you with a detailed response shortly.", 
                   "General inquiry - route to appropriate team based on content")
    
    def generate_ai_response(self, email_data: Dict) -> str:
        """Generate AI response using templates and context"""
        try:
            sender_name = email_data['sender'].split('@')[0].replace('.', ' ').title()
            sentiment = email_data['sentiment']
            priority = email_data['priority']
            keywords = email_data['keywords'].split(', ') if email_data['keywords'] else []
            
            # Find appropriate solution
            solution, escalation = self.find_best_solution(keywords, email_data['subject'], email_data['body'])
            
            # Select template based on priority and sentiment
            template_key = f"{priority}_{sentiment}"
            if template_key not in self.response_templates:
                template_key = 'normal_neutral'  # fallback
            
            template = self.response_templates[template_key]
            
            # Generate ticket ID
            ticket_id = f"SUP{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Additional context based on email content
            additional_info = ""
            if 'thank' in email_data['body'].lower():
                additional_info = "We truly appreciate your positive feedback!"
            elif priority == 'urgent':
                additional_info = f"This case has been escalated. {escalation}"
            
            # Format the response
            response = template.format(
                sender_name=sender_name,
                solution=solution,
                ticket_id=ticket_id,
                additional_info=additional_info
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return f"Dear {sender_name},\n\nThank you for contacting us. We've received your message and will respond within 24 hours.\n\nBest regards,\nSupport Team"
    
    def process_email(self, sender: str, subject: str, body: str) -> Dict:
        """Process incoming email with full analysis"""
        try:
            # Analyze email
            sentiment, sentiment_score = self.analyze_sentiment(body)
            priority = self.determine_priority(subject, body)
            keywords = self.extract_keywords(subject + " " + body)
            contact_info = self.extract_contact_info(body)
            requirements = self.extract_requirements(subject, body)
            
            # Create email data
            email_data = {
                'sender': sender,
                'subject': subject,
                'body': body,
                'priority': priority,
                'sentiment': sentiment,
                'keywords': ', '.join(keywords),
                'contact_info': contact_info,
                'requirements': requirements,
                'date_received': datetime.datetime.now().isoformat()
            }
            
            # Generate AI response
            ai_response = self.generate_ai_response(email_data)
            email_data['ai_response'] = ai_response
            
            # Store in database
            self.cursor.execute('''
                INSERT INTO emails (sender, subject, body, priority, sentiment, keywords, 
                                  contact_info, requirements, ai_response, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (sender, subject, body, priority, sentiment, ', '.join(keywords),
                  contact_info, requirements, ai_response, 'pending'))
            
            self.conn.commit()
            email_data['id'] = self.cursor.lastrowid
            
            logger.info(f"Processed email from {sender} - Priority: {priority}, Sentiment: {sentiment}")
            return email_data
            
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            raise
    
    def get_all_emails(self) -> List[Dict]:
        """Retrieve all emails from database"""
        self.cursor.execute('''
            SELECT id, sender, subject, body, date_received, priority, sentiment,
                   keywords, contact_info, requirements, ai_response, status
            FROM emails ORDER BY 
            CASE WHEN priority = 'urgent' THEN 1 ELSE 2 END,
            date_received DESC
        ''')
        
        emails = []
        for row in self.cursor.fetchall():
            emails.append({
                'id': row[0],
                'sender': row[1],
                'subject': row[2],
                'body': row[3],
                'date_received': row[4],
                'priority': row[5],
                'sentiment': row[6],
                'keywords': row[7],
                'contact_info': row[8],
                'requirements': row[9],
                'ai_response': row[10],
                'status': row[11]
            })
        
        return emails
    
    def get_analytics(self) -> Dict:
        """Get email analytics and statistics"""
        # Get email counts by category
        self.cursor.execute('SELECT priority, COUNT(*) FROM emails GROUP BY priority')
        priority_counts = dict(self.cursor.fetchall())
        
        self.cursor.execute('SELECT sentiment, COUNT(*) FROM emails GROUP BY sentiment')
        sentiment_counts = dict(self.cursor.fetchall())
        
        self.cursor.execute('SELECT status, COUNT(*) FROM emails GROUP BY status')
        status_counts = dict(self.cursor.fetchall())
        
        # Get total count
        self.cursor.execute('SELECT COUNT(*) FROM emails')
        total_emails = self.cursor.fetchone()[0]
        
        # Get recent emails (last 24 hours)
        self.cursor.execute('''
            SELECT COUNT(*) FROM emails 
            WHERE datetime(date_received) >= datetime('now', '-1 day')
        ''')
        recent_emails = self.cursor.fetchone()[0]
        
        return {
            'total_emails': total_emails,
            'recent_emails': recent_emails,
            'urgent_emails': priority_counts.get('urgent', 0),
            'resolved_emails': status_counts.get('resolved', 0),
            'pending_emails': status_counts.get('pending', 0),
            'priority_breakdown': priority_counts,
            'sentiment_breakdown': sentiment_counts,
            'status_breakdown': status_counts
        }

# Initialize the email assistant
email_assistant = EmailAssistant()

# API Routes
@app.route('/api/process_email', methods=['POST'])
def process_email():
    """Process a new incoming email"""
    try:
        data = request.json
        sender = data.get('sender', '')
        subject = data.get('subject', '')
        body = data.get('body', '')
        
        if not all([sender, subject, body]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        result = email_assistant.process_email(sender, subject, body)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in process_email: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/emails', methods=['GET'])
def get_emails():
    """Get all processed emails"""
    try:
        emails = email_assistant.get_all_emails()
        return jsonify(emails)
    except Exception as e:
        logger.error(f"Error in get_emails: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get email analytics"""
    try:
        analytics = email_assistant.get_analytics()
        return jsonify(analytics)
    except Exception as e:
        logger.error(f"Error in get_analytics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/send_response', methods=['POST'])
def send_response():
    """Mark email as responded/resolved"""
    try:
        data = request.json
        email_id = data.get('email_id')
        
        email_assistant.cursor.execute(
            'UPDATE emails SET status = ? WHERE id = ?',
            ('resolved', email_id)
        )
        email_assistant.conn.commit()
        
        return jsonify({'message': 'Email marked as resolved'})
    except Exception as e:
        logger.error(f"Error in send_response: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/regenerate_response', methods=['POST'])
def regenerate_response():
    """Regenerate AI response for an email"""
    try:
        data = request.json
        email_id = data.get('email_id')
        
        # Get email data
        email_assistant.cursor.execute(
            'SELECT sender, subject, body, priority, sentiment, keywords FROM emails WHERE id = ?',
            (email_id,)
        )
        row = email_assistant.cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Email not found'}), 404
        
        email_data = {
            'sender': row[0],
            'subject': row[1], 
            'body': row[2],
            'priority': row[3],
            'sentiment': row[4],
            'keywords': row[5]
        }
        
        # Generate new response
        new_response = email_assistant.generate_ai_response(email_data)
        
        # Update database
        email_assistant.cursor.execute(
            'UPDATE emails SET ai_response = ? WHERE id = ?',
            (new_response, email_id)
        )
        email_assistant.conn.commit()
        
        return jsonify({'ai_response': new_response})
    except Exception as e:
        logger.error(f"Error in regenerate_response: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/filter_emails', methods=['GET'])
def filter_emails():
    """Filter emails by priority or sentiment"""
    try:
        priority = request.args.get('priority')
        sentiment = request.args.get('sentiment')
        
        query = 'SELECT * FROM emails WHERE 1=1'
        params = []
        
        if priority:
            query += ' AND priority = ?'
            params.append(priority)
        
        if sentiment:
            query += ' AND sentiment = ?'
            params.append(sentiment)
        
        query += ' ORDER BY CASE WHEN priority = "urgent" THEN 1 ELSE 2 END, date_received DESC'
        
        email_assistant.cursor.execute(query, params)
        emails = []
        for row in email_assistant.cursor.fetchall():
            emails.append({
                'id': row[0], 'sender': row[1], 'subject': row[2], 'body': row[3],
                'date_received': row[4], 'priority': row[5], 'sentiment': row[6],
                'keywords': row[7], 'contact_info': row[8], 'requirements': row[9],
                'ai_response': row[10], 'status': row[11]
            })
        
        return jsonify(emails)
    except Exception as e:
        logger.error(f"Error in filter_emails: {e}")
        return jsonify({'error': str(e)}), 500

# Sample data insertion for testing
import csv
import os

@app.route('/api/load_sample_data', methods=['POST'])
def load_sample_data():
    """Load sample email data from CSV file"""
    try:
        # Path to your CSV file
        csv_file_path = 'data/Sample_Emails.csv'
        
        # Check if CSV file exists
        if not os.path.exists(csv_file_path):
            return jsonify({'error': 'Sample data CSV file not found'}), 404
        
        sample_emails = []
        
        # Read CSV file
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            
            # Validate required columns exist
            required_columns = ['sender', 'subject', 'body']
            if not all(col in csv_reader.fieldnames for col in required_columns):
                return jsonify({'error': 'CSV must contain columns: sender, subject, body'}), 400
            
            # Process each row
            for row in csv_reader:
                sample_emails.append({
                    'sender': row['sender'].strip(),
                    'subject': row['subject'].strip(),
                    'body': row['body'].strip()
                })
        
        # Process each email
        for email in sample_emails:
            email_assistant.process_email(email['sender'], email['subject'], email['body'])
        
        return jsonify({'message': f'Loaded {len(sample_emails)} sample emails from CSV'})
        
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file_path}")
        return jsonify({'error': 'Sample data CSV file not found'}), 404
    except csv.Error as e:
        logger.error(f"CSV parsing error: {e}")
        return jsonify({'error': f'CSV parsing error: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error loading sample data: {e}")
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    print("🚀 Starting AI Email Communication Assistant Backend...")
    print("📧 Loading AI models and initializing database...")
    print("🌐 Server will be available at http://localhost:5000")
    print("\n📋 Available API endpoints:")
    print("  POST /api/process_email - Process new email")
    print("  GET  /api/emails - Get all emails")
    print("  GET  /api/analytics - Get analytics")
    print("  POST /api/send_response - Mark email as resolved")
    print("  POST /api/regenerate_response - Regenerate AI response")
    print("  GET  /api/filter_emails - Filter emails")
    print("  POST /api/load_sample_data - Load sample data")
    app.run(debug=True, host='0.0.0.0', port=5000)