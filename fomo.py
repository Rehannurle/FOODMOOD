from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import requests
import os
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import func, extract, and_, desc
from datetime import datetime, timezone, timedelta
from flask_migrate import Migrate
import csv
import io
import zipfile
from flask import send_file
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 🔑 Secret key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')

# 🗄️ Auto switch DB: PostgreSQL (prod) or SQLite (local)
db_url = os.environ.get("DATABASE_URL")
if db_url:
    # Heroku/Render par kabhi prefix 'postgres://' hota hai, usko SQLAlchemy ke liye fix karna padta hai
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///foodmood.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# DB + Migration setup
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from werkzeug.security import generate_password_hash

# 📌 Database init + Admin auto-create
from werkzeug.security import generate_password_hash

has_initialized = False

@app.before_request
def init_db_and_admin():
    global has_initialized
    if has_initialized:
        return
    has_initialized = True

    with app.app_context():
        # Tables create karo
        db.create_all()
        print("✅ Database tables checked/created!")

        # Admin ensure karo
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@foodmood.com')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'Rihu@2004')

            admin_user = User(
                username=admin_username,
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                is_admin=True,
                age=25,
                gender='other',
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"✅ Admin created: {admin_email} / {admin_password}")
        else:
            print(f"ℹ️ Admin already exists: {admin.username} ({admin.email})")


       

# Your Foursquare Service Key
SERVICE_KEY = os.environ.get('FOURSQUARE_API_KEY', 'fallback-key')

# Working API configuration
FOURSQUARE_CONFIG = {
    "url": "https://places-api.foursquare.com/places/search",
    "headers": {
        "Accept": "application/json",
        "Authorization": f"Bearer {SERVICE_KEY}",
        "X-Places-Api-Version": "2025-06-17"
    }
}

# Email configuration for feedback notifications
EMAIL_CONFIG = {
    'SMTP_SERVER': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
    'SMTP_PORT': int(os.environ.get('SMTP_PORT', '587')),
    'EMAIL_USER': os.environ.get('EMAIL_USER', ''),
    'EMAIL_PASS': os.environ.get('EMAIL_PASS', ''),
    'ADMIN_EMAIL': os.environ.get('ADMIN_EMAIL', 'admin@foodmood.com')
}

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)  # New admin flag
    is_active = db.Column(db.Boolean, default=True)  # Account status
    last_login = db.Column(db.DateTime, nullable=True)  # Track last login
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    searches = db.relationship('SearchHistory', backref='user', lazy=True)
    feedback = db.relationship('Feedback', backref='user', lazy=True)

class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mood = db.Column(db.String(50), nullable=True)
    place_type = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    custom_query = db.Column(db.String(200), nullable=True)
    results_count = db.Column(db.Integer, default=0)
    search_date = db.Column(db.DateTime, default=datetime.utcnow)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    device = db.Column(db.String(200), nullable=True)
    features = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='new')
    admin_notes = db.Column(db.Text, nullable=True)
    is_public = db.Column(db.Boolean, default=True)

class AdminActivity(db.Model):
    """Track admin activities"""
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # 'user_deactivated', 'feedback_reviewed', etc.
    target_type = db.Column(db.String(50), nullable=False)  # 'user', 'feedback', 'system'
    target_id = db.Column(db.Integer, nullable=True)  # ID of the affected record
    details = db.Column(db.Text, nullable=True)  # Additional details
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    admin = db.relationship('User', backref='admin_activities')

# Helper functions (keeping existing ones)
def search_places(query, location="", latitude=None, longitude=None, limit=10, place_type="restaurant"):
    """Search for restaurants/hotels/cafes/dhabas using Foursquare API with coordinates or location"""
    try:
        params = {
            "query": query,
            "limit": limit
        }
        
        # Set categories based on place type
        if place_type == "hotel":
            params["categories"] = "19014"
        elif place_type == "restaurant":
            params["categories"] = "13000"
        elif place_type == "cafe":
            params["categories"] = "13032,13033,13034"
        elif place_type == "dhaba":
            params["categories"] = "13000"
            params["query"] = "dhaba"
        
        # Priority: coordinates > location text > default
        if latitude and longitude:
            params["ll"] = f"{latitude},{longitude}"
            params["radius"] = 10000
        elif location:
            params["near"] = location
        else:
            params["near"] = "Mumbai, India"
        
        response = requests.get(
            FOURSQUARE_CONFIG["url"],
            headers=FOURSQUARE_CONFIG["headers"],
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "places": data.get("results", []),
                "count": len(data.get("results", []))
            }
        else:
            return {
                "success": False,
                "error": f"API Error: {response.status_code}",
                "message": "Failed to fetch places"
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Connection error occurred"
        }

def get_mood_suggestions(mood, place_type="restaurant"):
    """Get food/hotel/cafe suggestions based on mood - Indian context"""
    
    if place_type == "dhaba":
        return ["dhaba", "roadside dhaba", "highway dhaba", "punjabi dhaba", "indian dhaba"]
    
    if place_type == "hotel":
        mood_places = {
            "happy": ["luxury hotel", "resort", "celebration hotel", "party hotel"],
            "sad": ["quiet hotel", "peaceful hotel", "comfort hotel", "cozy hotel"],
            "stressed": ["spa hotel", "wellness hotel", "relaxation hotel", "calm hotel"],
            "excited": ["adventure hotel", "activity hotel", "vibrant hotel", "entertainment hotel"],
            "tired": ["comfortable hotel", "rest hotel", "sleep hotel", "convenient hotel"],
            "romantic": ["romantic hotel", "honeymoon hotel", "couple hotel", "intimate hotel"],
            "social": ["family hotel", "group hotel", "social hotel", "party hotel"],
            "lazy": ["resort hotel", "leisure hotel", "relaxing hotel", "easy hotel"],
            "rainy": ["indoor hotel", "cozy hotel", "warm hotel", "covered hotel"],
            "hungry": ["hotel with restaurant", "food hotel", "dining hotel", "buffet hotel"],
            "travelling": ["transit hotel", "airport hotel", "highway hotel", "quick stay hotel"],
            "nostalgic": ["heritage hotel", "traditional hotel", "classic hotel", "vintage hotel"]
        }
        return mood_places.get(mood.lower(), ["hotel"])
    
    elif place_type == "cafe":
        mood_cafes = {
            "happy": ["celebration cafe", "cheerful coffee", "bright cafe", "happy coffee shop"],
            "sad": ["comfort cafe", "quiet coffee", "peaceful tea house", "cozy corner cafe"],
            "stressed": ["calm cafe", "relaxing coffee", "herbal tea", "zen coffee shop"],
            "excited": ["energizing coffee", "strong espresso", "vibrant cafe", "buzz coffee"],
            "tired": ["strong coffee", "energy boost", "espresso bar", "wake up coffee"],
            "romantic": ["intimate cafe", "cozy coffee date", "romantic coffee shop", "couple cafe"],
            "social": ["social coffee", "group cafe", "community coffee", "hangout cafe"],
            "lazy": ["laid back cafe", "comfortable coffee", "slow coffee", "relaxed cafe"],
            "rainy": ["warm cafe", "indoor coffee", "cozy hideaway", "monsoon coffee"],
            "hungry": ["cafe with food", "coffee and snacks", "breakfast cafe", "pastry cafe"],
            "travelling": ["drive thru coffee", "quick coffee", "highway cafe", "grab and go"],
            "nostalgic": ["traditional cafe", "old school coffee", "vintage cafe", "classic coffee"]
        }
        return mood_cafes.get(mood.lower(), ["coffee shop"])
    
    else:
        mood_foods = {
            "happy": ["restaurant", "biryani", "sweet", "celebration food", "festive food"],
            "sad": ["comfort food", "chai", "soup", "warm food", "home style food"],
            "stressed": ["light food", "healthy", "fresh juice", "salad", "calm dining"],
            "excited": ["spicy food", "street food", "new cuisine", "adventure food", "fusion"],
            "tired": ["quick food", "cafe", "energy food", "light meal", "convenient"],
            "romantic": ["fine dining", "romantic", "cozy restaurant", "dinner", "ambiance"],
            "social": ["family restaurant", "group dining", "sharing", "party food", "celebration"],
            "lazy": ["delivery", "casual dining", "easy food", "nearby restaurant", "simple food"],
            "rainy": ["chai", "coffee", "bhajiya", "pakoda", "hot snacks", "warm drinks"],
            "hungry": ["buffet", "thali", "heavy meal", "full course", "filling food"],
            "travelling": ["fast food", "quick bite", "drive thru", "highway dhaba", "quick service"],
            "nostalgic": ["home food", "traditional", "authentic", "classic dishes", "comfort"]
        }
        return mood_foods.get(mood.lower(), ["restaurant"])

def send_feedback_notification(feedback_data):
    """Send email notification to admin about new feedback"""
    if not EMAIL_CONFIG['EMAIL_USER'] or not EMAIL_CONFIG['ADMIN_EMAIL']:
        print("Email configuration not set up - skipping notification")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['EMAIL_USER']
        msg['To'] = EMAIL_CONFIG['ADMIN_EMAIL']
        msg['Subject'] = f"🍽️ New Food Mood Feedback: {feedback_data['type'].title()} - {feedback_data['title']}"
        
        # Email body
        body = f"""
        New feedback received on Food Mood!
        
        📝 Feedback Details:
        - Type: {feedback_data['type'].title()}
        - Rating: {'⭐' * feedback_data['rating']} ({feedback_data['rating']}/5)
        - Title: {feedback_data['title']}
        - From: {feedback_data['name']} ({feedback_data['email']})
        - Device: {feedback_data.get('device', 'Not provided')}
        
        💬 Message:
        {feedback_data['message']}
        
        🔧 Features Used:
        {', '.join(feedback_data.get('features', [])) if feedback_data.get('features') else 'None specified'}
        
        ⏰ Submitted: {feedback_data['timestamp']}
        
        ---
        Food Mood Feedback System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['EMAIL_USER'], EMAIL_CONFIG['EMAIL_PASS'])
            server.sendmail(EMAIL_CONFIG['EMAIL_USER'], EMAIL_CONFIG['ADMIN_EMAIL'], msg.as_string())
        
        print(f"✅ Feedback notification sent successfully for: {feedback_data['title']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send feedback notification: {str(e)}")
        return False

def send_feedback_confirmation(feedback_data):
    """Send confirmation email to user who submitted feedback"""
    if not EMAIL_CONFIG['EMAIL_USER'] or not feedback_data.get('email'):
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['EMAIL_USER']
        msg['To'] = feedback_data['email']
        msg['Subject'] = "🍽️ Thank you for your Food Mood feedback!"
        
        body = f"""
        Hi {feedback_data['name']},
        
        Thank you for taking the time to share your feedback with Food Mood! 🙏
        
        We've received your {feedback_data['type']} feedback titled "{feedback_data['title']}" 
        and our team will review it shortly.
        
        Your input helps us make Food Mood better for everyone. We truly appreciate users 
        like you who help us improve our AI-powered mood-based discovery platform.
        
        📧 If you have any follow-up questions, feel free to reply to this email.
        
        Best regards,  
        The Food Mood Team
        
        ---
        🍽️ Food Mood - AI-Powered Mood-Based Discovery
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['EMAIL_USER'], EMAIL_CONFIG['EMAIL_PASS'])
            server.sendmail(EMAIL_CONFIG['EMAIL_USER'], feedback_data['email'], msg.as_string())
        
        print(f"✅ Confirmation email sent to user: {feedback_data['email']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send confirmation email: {str(e)}")
        return False

def log_admin_activity(admin_id, action, target_type, target_id=None, details=None):
    """Log admin activities"""
    try:
        activity = AdminActivity(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details
        )
        db.session.add(activity)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Failed to log admin activity: {str(e)}")
        return False

def require_admin(f):
    """Decorator to require admin privileges"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        user = db.session.get(User, session['user_id'])
        if not user or not user.is_admin:
            flash('Admin access required')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/healthz')
def healthz():
    return "OK", 200

@app.route('/')
def index():
    """Main page - redirect to login if not authenticated"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user is admin
    user = db.session.get(User, session['user_id'])
    if user and user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    return render_template('index.html')

@app.route('/login')
def login():
    """Login page"""
    return render_template('login.html')

@app.route('/register')
def register():
    """Register page"""
    return render_template('register.html')

@app.route('/features')
def features():
    """Features page"""
    return render_template('features.html')

@app.route('/howwork')
def howwork():
    """How It Works page"""
    return render_template('howwork.html')

@app.route('/helpcentre')
def helpcentre():
    """Help Centre page - corrected route"""
    return render_template('helpcentre.html')

@app.route('/help')
def help_center():
    """Alternative help route"""
    return redirect(url_for('helpcentre'))

@app.route('/contact')
def contact():
    """Contact page - corrected route"""
    return render_template('contact.html')

@app.route('/contact.html')
def contact_html():
    """Alternative contact route for .html extension"""
    return redirect(url_for('contact'))

@app.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('privacy.html')

@app.route('/privacy.html')
def privacy_html():
    """Alternative privacy route for .html extension"""
    return redirect(url_for('privacy'))

@app.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('terms.html')

@app.route('/terms.html')
def terms_html():
    """Alternative terms route for .html extension"""
    return redirect(url_for('terms'))

# API endpoint for newsletter subscription (referenced in footer)
@app.route('/api/newsletter', methods=['POST'])
def api_newsletter():
    """Newsletter subscription API endpoint"""
    data = request.get_json()
    email = data.get('email', '').strip()
    
    if not email:
        return jsonify({"success": False, "message": "Email is required"}), 400
    
    # Basic email validation
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({"success": False, "message": "Please enter a valid email address"}), 400
    
    try:
        # Here you could add the email to a newsletter database table
        # For now, we'll just log it and send a confirmation
        
        # Log the subscription (you might want to create a Newsletter model)
        print(f"Newsletter subscription: {email}")
        
        # Send confirmation email if email is configured
        if EMAIL_CONFIG['EMAIL_USER']:
            try:
                send_newsletter_confirmation(email)
            except Exception as e:
                print(f"Failed to send newsletter confirmation: {str(e)}")
        
        return jsonify({
            "success": True,
            "message": "Thank you for subscribing! You'll receive updates about new features and improvements."
        })
        
    except Exception as e:
        print(f"Newsletter subscription error: {str(e)}")
        return jsonify({"success": False, "message": "Failed to subscribe. Please try again."}), 500

# Helper function for newsletter confirmation email
def send_newsletter_confirmation(email):
    """Send confirmation email for newsletter subscription"""
    if not EMAIL_CONFIG['EMAIL_USER']:
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['EMAIL_USER']
        msg['To'] = email
        msg['Subject'] = "🍽️ Welcome to Food Mood Newsletter!"
        
        body = f"""
        Hi there!
        
        Thank you for subscribing to the Food Mood newsletter! 🎉
        
        You're now part of our community and will be the first to know about:
        
        ✨ New AI-powered features
        🏨 Enhanced location coverage  
        🍕 Better restaurant recommendations
        📱 Mobile app updates
        🎯 Personalized mood-based suggestions
        
        We promise to keep our updates relevant and not spam your inbox. 
        You can unsubscribe at any time by replying to any newsletter email.
        
        Happy exploring!
        
        Best regards,  
        The Food Mood Team
        
        ---
        🍽️ Food Mood - AI-Powered Mood-Based Discovery
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['EMAIL_USER'], EMAIL_CONFIG['EMAIL_PASS'])
            server.sendmail(EMAIL_CONFIG['EMAIL_USER'], email, msg.as_string())
        
        print(f"✅ Newsletter confirmation sent to: {email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send newsletter confirmation: {str(e)}")
        return False

# Optional: Create a Newsletter model if you want to store subscriptions
class Newsletter(db.Model):
    """Newsletter subscription model"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)

# Contact form API endpoint
@app.route('/api/contact', methods=['POST'])
def api_contact():
    """Contact form submission API endpoint"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'email', 'subject', 'message']
    for field in required_fields:
        if not data.get(field, '').strip():
            return jsonify({"success": False, "message": f"{field.title()} is required"}), 400
    
    try:
        # Create a contact message record (you might want to create a ContactMessage model)
        contact_data = {
            'name': data['name'].strip(),
            'email': data['email'].strip(),
            'subject': data['subject'].strip(),
            'message': data['message'].strip(),
            'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        # Send email notification to admin
        if EMAIL_CONFIG['EMAIL_USER'] and EMAIL_CONFIG['ADMIN_EMAIL']:
            try:
                send_contact_notification(contact_data)
            except Exception as e:
                print(f"Failed to send contact notification: {str(e)}")
        
        return jsonify({
            "success": True,
            "message": "Thank you for your message! We'll get back to you soon."
        })
        
    except Exception as e:
        print(f"Contact form error: {str(e)}")
        return jsonify({"success": False, "message": "Failed to send message. Please try again."}), 500

def send_contact_notification(contact_data):
    """Send email notification for contact form submission"""
    if not EMAIL_CONFIG['EMAIL_USER'] or not EMAIL_CONFIG['ADMIN_EMAIL']:
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['EMAIL_USER']
        msg['To'] = EMAIL_CONFIG['ADMIN_EMAIL']
        msg['Subject'] = f"🍽️ Food Mood Contact: {contact_data['subject']}"
        
        body = f"""
        New contact form submission on Food Mood!
        
        📝 Contact Details:
        - Name: {contact_data['name']}
        - Email: {contact_data['email']}
        - Subject: {contact_data['subject']}
        
        💬 Message:
        {contact_data['message']}
        
        ⏰ Submitted: {contact_data['timestamp']}
        
        ---
        Food Mood Contact System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['EMAIL_USER'], EMAIL_CONFIG['EMAIL_PASS'])
            server.sendmail(EMAIL_CONFIG['EMAIL_USER'], EMAIL_CONFIG['ADMIN_EMAIL'], msg.as_string())
        
        print(f"✅ Contact notification sent for: {contact_data['subject']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send contact notification: {str(e)}")
        return False
    
@app.route('/feedback')
def feedback():
    """Feedback page"""
    return render_template('feedback.html')

@app.route('/profile')
def profile():
    """User profile page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    # Get user statistics
    total_searches = SearchHistory.query.filter_by(user_id=user.id).count()
    recent_searches = SearchHistory.query.filter_by(user_id=user.id).order_by(SearchHistory.search_date.desc()).limit(10).all()
    
    # Get mood statistics
    mood_stats = db.session.query(SearchHistory.mood, func.count(SearchHistory.mood)).filter_by(user_id=user.id).group_by(SearchHistory.mood).all()
    place_type_stats = db.session.query(SearchHistory.place_type, func.count(SearchHistory.place_type)).filter_by(user_id=user.id).group_by(SearchHistory.place_type).all()
    
    return render_template('profile.html', user=user, total_searches=total_searches, 
                         recent_searches=recent_searches, mood_stats=mood_stats, 
                         place_type_stats=place_type_stats)

@app.route('/admin')
@require_admin
def admin_dashboard():
    """Admin dashboard"""
    return render_template('admin_dashboard.html')

# API Routes
@app.route('/api/login', methods=['POST'])
def api_login():
    """Login API endpoint"""
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required"}), 400
    
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        
        redirect_url = "/admin" if user.is_admin else "/"
        return jsonify({"success": True, "message": "Login successful", "redirect": redirect_url})
    else:
        return jsonify({"success": False, "message": "Invalid email or password"}), 401
    
    
def send_welcome_email(user_data):
    """Send welcome email to newly registered user"""
    if not EMAIL_CONFIG['EMAIL_USER'] or not user_data.get('email'):
        print("Email configuration not set up - skipping welcome email")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['EMAIL_USER']
        msg['To'] = user_data['email']
        msg['Subject'] = "🎉 Welcome to Food Mood - Your AI-Powered Discovery Journey Begins!"
        
        body = f"""
        Hi {user_data['username']},
        
        🎉 Welcome to Food Mood! 🍽️
        
        Thank you for joining our AI-powered mood-based discovery platform. We're thrilled to have you as part of our growing community!
        
        ✨ What is Food Mood?
        Food Mood is a student project created by Rehan Nurle, designed to help you discover restaurants, cafes, hotels, and dhabas based on your current mood and preferences. Whether you're feeling happy, sad, excited, or just hungry, our AI will suggest the perfect places for you!
        
        🌍 Where Can You Search?
        Food Mood currently works best in these areas:
        
        ⭐ BEST COVERAGE (Excellent Results):
        • Mumbai & Greater Mumbai Region
        • Delhi NCR (Delhi, Gurgaon, Noida, Faridabad)
        • Bangalore (Bengaluru)
        • Pune & PCMC
        • Hyderabad & Secunderabad
        • Chennai & Suburban Areas
        • Kolkata & Howrah
        
        ⚠️  LIMITED COVERAGE (Some Results):
        • Smaller cities and towns
        • Rural areas
        • Very local/traditional establishments
        • Street food vendors and small dhabas
        
        💡 PRO TIPS for Better Results:
        1. 🏙️ Try searching in major city areas first
        2. 🎯 Use specific location names (e.g., "Connaught Place Delhi" instead of just "Delhi")
        3. 🏨 Hotels and cafes have better coverage than local dhabas
        4. 📱 Enable location services for more accurate nearby results
        5. 🔍 Try different search terms if first search doesn't yield results
        
        🔐 Your Data is Safe
        We want to assure you that your privacy and data security are our top priorities. All your personal information is stored securely and will never be shared with third parties. We only use your data to enhance your experience on our platform.
        
        🚀 What's Coming Next?
        As this is an ongoing student project, I'm constantly working to improve Food Mood with exciting new features:
        • Enhanced AI mood detection
        • Better local restaurant database (Google Places integration planned!)
        • Personalized recommendations based on your preferences
        • Integration with more food delivery services
        • Social features to share discoveries with friends
        • Mobile app for iOS and Android
        • Voice-activated search
        • Nutritional information and dietary preferences
        • User-contributed restaurant suggestions
        
        🎯 Getting Started
        Here's what you can do right now:
        1. 🎭 Try our mood-based search - just select how you're feeling!
        2. 📍 Use location services for nearby recommendations
        3. 🏨 Explore different place types: restaurants, cafes, hotels, and dhabas
        4. 🌟 Start with major cities for best results
        5. 💬 Share your feedback to help us improve coverage
        
        🎓 About the Developer
        Food Mood is a passion project developed by Rehan Nurle, a student dedicated to creating innovative solutions that make everyday decisions easier and more enjoyable. Your support and feedback help drive continuous improvements and new feature development.
        
        🤝 Help Us Improve!
        Since this is a growing platform, your feedback about missing restaurants or areas is invaluable! If you can't find places in your area, let me know - I'm working on expanding our database coverage, especially for Indian locations.
        
        📧 Need Help?
        If you have any questions, suggestions, or just want to say hello, feel free to reply to this email. I personally read every message and love hearing from our users!
        
        Thank you for being part of the Food Mood family. I can't wait to see what amazing places you'll discover! 🌟
        
        Happy exploring!
        
        Best regards,  
        Rehan Nurle  
        Creator & Developer, Food Mood
        
        ---
        🍽️ Food Mood - AI-Powered Mood-Based Discovery
        📧 Support: Reply to this email for any assistance
        🌐 Platform: https://foodmood-fr4h.onrender.com
        
        P.S. Don't forget to try our "rainy day" mood search - it's perfect for monsoon season! ☔
        
        📍 Quick Start Suggestion: Try searching for restaurants in Mumbai, Delhi, or Bangalore first to see the full power of Food Mood!
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['EMAIL_USER'], EMAIL_CONFIG['EMAIL_PASS'])
            server.sendmail(EMAIL_CONFIG['EMAIL_USER'], user_data['email'], msg.as_string())
        
        print(f"✅ Welcome email sent successfully to: {user_data['email']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send welcome email: {str(e)}")
        return False

@app.route('/api/register', methods=['POST'])
def api_register():
    """Registration API endpoint with welcome email"""
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    age = data.get('age')
    gender = data.get('gender', '').strip()
    
    if not username or not email or not password:
        return jsonify({"success": False, "message": "Username, email and password are required"}), 400
    
    # Check if user exists
    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "Email already registered"}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({"success": False, "message": "Username already taken"}), 400
    
    try:
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            age=age if age else None,
            gender=gender if gender else None,
            is_admin=False  # Regular users are not admin by default
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Prepare welcome email data
        welcome_data = {
            'username': username,
            'email': email,
            'registration_date': user.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        # Send welcome email (in background, don't block registration)
        try:
            send_welcome_email(welcome_data)
        except Exception as e:
            print(f"Failed to send welcome email: {str(e)}")
            # Don't fail registration if email fails
        
        # Set session
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        
        return jsonify({
            "success": True, 
            "message": "Registration successful! Check your email for a welcome message with tips to get started.",
            "redirect": "/"
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Registration error: {str(e)}")
        return jsonify({"success": False, "message": "Registration failed. Please try again."}), 500
    
@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Logout API endpoint"""
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully", "redirect": "/login"})

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for restaurant/hotel/cafe/dhaba search with geolocation support"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Authentication required"}), 401
    
    data = request.get_json()
    
    mood = data.get('mood', '').strip()
    location = data.get('location', '').strip()
    custom_query = data.get('custom_query', '').strip()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    place_type = data.get('place_type', 'restaurant')
    
    # Determine search query
    if custom_query:
        search_query = custom_query
    elif place_type == "dhaba":
        search_query = "dhaba"
    elif mood:
        suggestions = get_mood_suggestions(mood, place_type)
        search_query = suggestions[0]
    else:
        search_query = place_type
    
    # Search for places
    result = search_places(search_query, location, latitude, longitude, limit=15, place_type=place_type)
    
    # Save search history
    search_record = SearchHistory(
        user_id=session['user_id'],
        mood=mood if place_type != "dhaba" else None,
        place_type=place_type,
        location=location,
        custom_query=custom_query,
        results_count=result.get("count", 0),
        latitude=latitude,
        longitude=longitude
    )
    db.session.add(search_record)
    db.session.commit()
    
    if result["success"]:
        # Format results for frontend
        formatted_results = []
        for place in result["places"]:
            distance_m = place.get("distance", 0)
            distance_km = round(distance_m / 1000, 1) if distance_m > 0 else 0
            
            formatted_results.append({
                "name": place.get("name", "Unknown"),
                "address": place.get("location", {}).get("formatted_address", "Address not available"),
                "category": place.get("categories", [{}])[0].get("name", "Place") if place.get("categories") else "Place",
                "rating": place.get("rating", 0),
                "price": place.get("price", 0),
                "distance": distance_km,
                "website": place.get("website", ""),
                "phone": place.get("tel", "")
            })
        
        return jsonify({
            "success": True,
            "query": search_query,
            "mood": mood if place_type != "dhaba" else "all_dhabas",
            "location": location,
            "place_type": place_type,
            "used_coordinates": bool(latitude and longitude),
            "places": formatted_results,
            "count": len(formatted_results)
        })
    else:
        return jsonify(result), 500

# Admin API Routes
@app.route('/api/admin/stats', methods=['GET'])
@require_admin
def api_admin_stats():
    """Get admin dashboard statistics"""
    try:
        # Basic stats
        total_users = User.query.filter_by(is_admin=False).count()
        total_admins = User.query.filter_by(is_admin=True).count()
        total_searches = SearchHistory.query.count()
        total_feedback = Feedback.query.count()
        
        # Recent stats (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        new_users_30d = User.query.filter(User.created_at >= thirty_days_ago, User.is_admin == False).count()
        searches_30d = SearchHistory.query.filter(SearchHistory.search_date >= thirty_days_ago).count()
        feedback_30d = Feedback.query.filter(Feedback.timestamp >= thirty_days_ago).count()
        
        # Active users (users who searched in last 30 days)
        active_users = db.session.query(SearchHistory.user_id).filter(
            SearchHistory.search_date >= thirty_days_ago
        ).distinct().count()
        
        # Average rating
        avg_rating = db.session.query(func.avg(Feedback.rating)).scalar() or 0
        
        # Most popular moods
        popular_moods = db.session.query(
            SearchHistory.mood, func.count(SearchHistory.mood)
        ).filter(SearchHistory.mood.isnot(None)).group_by(
            SearchHistory.mood
        ).order_by(desc(func.count(SearchHistory.mood))).limit(5).all()
        
        # Most popular place types
        popular_places = db.session.query(
            SearchHistory.place_type, func.count(SearchHistory.place_type)
        ).group_by(SearchHistory.place_type).order_by(
            desc(func.count(SearchHistory.place_type))
        ).limit(5).all()
        
        return jsonify({
            "success": True,
            "stats": {
                "users": {
                    "total": total_users,
                    "admins": total_admins,
                    "new_30d": new_users_30d,
                    "active_30d": active_users
                },
                "activity": {
                    "total_searches": total_searches,
                    "searches_30d": searches_30d,
                    "total_feedback": total_feedback,
                    "feedback_30d": feedback_30d
                },
                "ratings": {
                    "average": round(avg_rating, 1)
                },
                "popular_moods": [{"mood": mood, "count": count} for mood, count in popular_moods],
                "popular_places": [{"place_type": place, "count": count} for place, count in popular_places]
            }
        })
        
    except Exception as e:
        print(f"Error fetching admin stats: {str(e)}")
        return jsonify({"success": False, "message": "Failed to fetch statistics"}), 500

@app.route('/api/admin/users', methods=['GET'])
@require_admin
def api_admin_users():
    """Get users with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search', '').strip()
        
        query = User.query.filter_by(is_admin=False)
        
        if search:
            query = query.filter(
                db.or_(
                    User.username.contains(search),
                    User.email.contains(search)
                )
            )
        
        users = query.order_by(desc(User.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        user_list = []
        for user in users.items:
            # Get user stats
            search_count = SearchHistory.query.filter_by(user_id=user.id).count()
            feedback_count = Feedback.query.filter_by(user_id=user.id).count()
            last_search = SearchHistory.query.filter_by(user_id=user.id).order_by(
                desc(SearchHistory.search_date)
            ).first()
            
            user_list.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "age": user.age,
                "gender": user.gender,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "last_search": last_search.search_date.isoformat() if last_search else None,
                "stats": {
                    "searches": search_count,
                    "feedback": feedback_count
                }
            })
        
        return jsonify({
            "success": True,
            "users": user_list,
            "pagination": {
                "page": users.page,
                "pages": users.pages,
                "per_page": users.per_page,
                "total": users.total
            }
        })
        
    except Exception as e:
        print(f"Error fetching users: {str(e)}")
        return jsonify({"success": False, "message": "Failed to fetch users"}), 500

@app.route('/api/admin/user/<int:user_id>', methods=['GET'])
@require_admin
def api_admin_user_detail(user_id):
    """Get detailed user information"""
    try:
        user = User.query.get_or_404(user_id)
        
        if user.is_admin:
            return jsonify({"success": False, "message": "Cannot view admin details"}), 403
        
        # Get user searches
        searches = SearchHistory.query.filter_by(user_id=user.id).order_by(
            desc(SearchHistory.search_date)
        ).limit(50).all()
        
        # Get user feedback
        feedback = Feedback.query.filter_by(user_id=user.id).order_by(
            desc(Feedback.timestamp)
        ).limit(20).all()
        
        # Get mood statistics
        mood_stats = db.session.query(
            SearchHistory.mood, func.count(SearchHistory.mood)
        ).filter_by(user_id=user.id).filter(
            SearchHistory.mood.isnot(None)
        ).group_by(SearchHistory.mood).all()
        
        # Get place type statistics  
        place_stats = db.session.query(
            SearchHistory.place_type, func.count(SearchHistory.place_type)
        ).filter_by(user_id=user.id).group_by(SearchHistory.place_type).all()
        
        return jsonify({
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "age": user.age,
                "gender": user.gender,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "searches": [{
                    "id": s.id,
                    "mood": s.mood,
                    "place_type": s.place_type,
                    "location": s.location,
                    "custom_query": s.custom_query,
                    "results_count": s.results_count,
                    "search_date": s.search_date.isoformat()
                } for s in searches],
                "feedback": [{
                    "id": f.id,
                    "type": f.type,
                    "rating": f.rating,
                    "title": f.title,
                    "message": f.message,
                    "timestamp": f.timestamp.isoformat(),
                    "status": f.status
                } for f in feedback],
                "mood_stats": [{"mood": mood, "count": count} for mood, count in mood_stats],
                "place_stats": [{"place_type": place, "count": count} for place, count in place_stats]
            }
        })
        
    except Exception as e:
        print(f"Error fetching user details: {str(e)}")
        return jsonify({"success": False, "message": "Failed to fetch user details"}), 500

@app.route('/api/admin/user/<int:user_id>/toggle', methods=['POST'])
@require_admin
def api_admin_toggle_user(user_id):
    """Toggle user active status"""
    try:
        user = User.query.get_or_404(user_id)
        
        if user.is_admin:
            return jsonify({"success": False, "message": "Cannot modify admin users"}), 403
        
        user.is_active = not user.is_active
        db.session.commit()
        
        # Log admin activity
        action = "user_activated" if user.is_active else "user_deactivated"
        log_admin_activity(session['user_id'], action, "user", user_id, 
                          f"User {user.username} {'activated' if user.is_active else 'deactivated'}")
        
        return jsonify({
            "success": True,
            "message": f"User {'activated' if user.is_active else 'deactivated'} successfully",
            "is_active": user.is_active
        })
        
    except Exception as e:
        print(f"Error toggling user status: {str(e)}")
        return jsonify({"success": False, "message": "Failed to update user status"}), 500

@app.route('/api/admin/feedback', methods=['GET'])
@require_admin
def api_admin_feedback():
    """Get feedback with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status = request.args.get('status', 'all')
        feedback_type = request.args.get('type', 'all')
        
        query = Feedback.query
        
        if status != 'all':
            query = query.filter_by(status=status)
        
        if feedback_type != 'all':
            query = query.filter_by(type=feedback_type)
        
        feedback_list = query.order_by(desc(Feedback.timestamp)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        feedback_data = []
        for fb in feedback_list.items:
            user = User.query.get(fb.user_id) if fb.user_id else None
            feedback_data.append({
                "id": fb.id,
                "name": fb.name,
                "email": fb.email,
                "type": fb.type,
                "rating": fb.rating,
                "title": fb.title,
                "message": fb.message,
                "device": fb.device,
                "features": json.loads(fb.features) if fb.features else [],
                "timestamp": fb.timestamp.isoformat(),
                "status": fb.status,
                "admin_notes": fb.admin_notes,
                "is_public": fb.is_public,
                "user": {
                    "username": user.username if user else "Anonymous",
                    "id": user.id if user else None
                }
            })
        
        return jsonify({
            "success": True,
            "feedback": feedback_data,
            "pagination": {
                "page": feedback_list.page,
                "pages": feedback_list.pages,
                "per_page": feedback_list.per_page,
                "total": feedback_list.total
            }
        })
        
    except Exception as e:
        print(f"Error fetching feedback: {str(e)}")
        return jsonify({"success": False, "message": "Failed to fetch feedback"}), 500

@app.route('/api/admin/feedback/<int:feedback_id>/update', methods=['POST'])
@require_admin
def api_admin_update_feedback(feedback_id):
    """Update feedback status and admin notes"""
    try:
        feedback = Feedback.query.get_or_404(feedback_id)
        data = request.get_json()
        
        old_status = feedback.status
        feedback.status = data.get('status', feedback.status)
        feedback.admin_notes = data.get('admin_notes', feedback.admin_notes)
        feedback.is_public = data.get('is_public', feedback.is_public)
        
        db.session.commit()
        
        # Log admin activity
        log_admin_activity(session['user_id'], "feedback_updated", "feedback", feedback_id,
                          f"Status changed from {old_status} to {feedback.status}")
        
        return jsonify({
            "success": True,
            "message": "Feedback updated successfully"
        })
        
    except Exception as e:
        print(f"Error updating feedback: {str(e)}")
        return jsonify({"success": False, "message": "Failed to update feedback"}), 500

@app.route('/api/admin/activities', methods=['GET'])
@require_admin
def api_admin_activities():
    """Get admin activity logs"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        activities = AdminActivity.query.order_by(desc(AdminActivity.timestamp)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        activity_list = []
        for activity in activities.items:
            admin = User.query.get(activity.admin_id)
            activity_list.append({
                "id": activity.id,
                "admin": {
                    "id": admin.id,
                    "username": admin.username
                },
                "action": activity.action,
                "target_type": activity.target_type,
                "target_id": activity.target_id,
                "details": activity.details,
                "timestamp": activity.timestamp.isoformat()
            })
        
        return jsonify({
            "success": True,
            "activities": activity_list,
            "pagination": {
                "page": activities.page,
                "pages": activities.pages,
                "per_page": activities.per_page,
                "total": activities.total
            }
        })
        
    except Exception as e:
        print(f"Error fetching activities: {str(e)}")
        return jsonify({"success": False, "message": "Failed to fetch activities"}), 500

@app.route('/api/admin/make-admin', methods=['POST'])
@require_admin
def api_make_admin():
    """Make a user an admin"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        user = User.query.get_or_404(user_id)
        
        if user.is_admin:
            return jsonify({"success": False, "message": "User is already an admin"}), 400
        
        user.is_admin = True
        db.session.commit()
        
        # Log admin activity
        log_admin_activity(session['user_id'], "user_promoted", "user", user_id,
                          f"User {user.username} promoted to admin")
        
        return jsonify({
            "success": True,
            "message": f"User {user.username} is now an admin"
        })
        
    except Exception as e:
        print(f"Error making user admin: {str(e)}")
        return jsonify({"success": False, "message": "Failed to promote user"}), 500

# Continue with existing routes...
@app.route('/api/feedback', methods=['POST'])
def api_feedback():
    """Submit feedback API endpoint"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'email', 'type', 'rating', 'title', 'message']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"success": False, "message": f"{field.title()} is required"}), 400
    
    # Validate rating
    rating = data.get('rating', 0)
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"success": False, "message": "Rating must be between 1 and 5"}), 400
    
    # Validate feedback type
    valid_types = ['bug', 'feature', 'improvement', 'general', 'compliment', 'complaint']
    if data.get('type') not in valid_types:
        return jsonify({"success": False, "message": "Invalid feedback type"}), 400
    
    try:
        # Create feedback record
        feedback = Feedback(
            user_id=session.get('user_id'),  # Can be None for anonymous feedback
            name=data['name'].strip(),
            email=data['email'].strip(),
            type=data['type'],
            rating=rating,
            title=data['title'].strip(),
            message=data['message'].strip(),
            device=data.get('device', '').strip(),
            features=json.dumps(data.get('features', [])),
            ip_address=request.environ.get('REMOTE_ADDR'),
            user_agent=request.headers.get('User-Agent', ''),
            timestamp=datetime.utcnow()
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        # Prepare notification data
        notification_data = {
            'name': feedback.name,
            'email': feedback.email,
            'type': feedback.type,
            'rating': feedback.rating,
            'title': feedback.title,
            'message': feedback.message,
            'device': feedback.device,
            'features': data.get('features', []),
            'timestamp': feedback.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        # Send notifications (async in production)
        try:
            send_feedback_notification(notification_data)
            send_feedback_confirmation(notification_data)
        except Exception as e:
            print(f"Failed to send email notifications: {str(e)}")
        
        return jsonify({
            "success": True,
            "message": "Thank you for your feedback! We'll review it and get back to you if needed.",
            "feedback_id": feedback.id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error saving feedback: {str(e)}")
        return jsonify({"success": False, "message": "Failed to save feedback. Please try again."}), 500

@app.route('/api/feedback/recent', methods=['GET'])
def api_feedback_recent():
    """Get recent public feedback"""
    offset = int(request.args.get('offset', 0))
    limit = min(int(request.args.get('limit', 5)), 20)
    
    try:
        feedback_query = Feedback.query.filter(
            Feedback.is_public == True,
            Feedback.status.in_(['new', 'reviewed'])
        ).order_by(Feedback.timestamp.desc()).offset(offset).limit(limit)
        
        feedback_list = []
        for fb in feedback_query:
            feedback_list.append({
                'name': fb.name,
                'type': fb.type,
                'rating': fb.rating,
                'title': fb.title,
                'message': fb.message,
                'timestamp': fb.timestamp.isoformat(),
                'features': json.loads(fb.features) if fb.features else []
            })
        
        return jsonify({
            "success": True,
            "feedback": feedback_list,
            "count": len(feedback_list)
        })
        
    except Exception as e:
        print(f"Error fetching recent feedback: {str(e)}")
        return jsonify({"success": False, "message": "Failed to fetch feedback"}), 500

@app.route('/api/feedback/stats', methods=['GET'])
def api_feedback_stats():
    """Get feedback statistics"""
    try:
        total_feedback = Feedback.query.count()
        
        # Calculate average rating
        avg_rating_result = db.session.query(func.avg(Feedback.rating)).scalar()
        avg_rating = round(avg_rating_result, 1) if avg_rating_result else 0
        
        # Count feedback this month
        current_month = datetime.now().month
        current_year = datetime.now().year
        this_month_count = Feedback.query.filter(
            extract('month', Feedback.timestamp) == current_month,
            extract('year', Feedback.timestamp) == current_year
        ).count()
        
        return jsonify({
            "success": True,
            "stats": {
                "total": total_feedback,
                "averageRating": avg_rating,
                "thisMonth": this_month_count
            }
        })
        
    except Exception as e:
        print(f"Error fetching feedback stats: {str(e)}")
        return jsonify({"success": False, "message": "Failed to fetch stats"}), 500

@app.route('/api/mood-suggestions/<mood>')
def api_mood_suggestions(mood):
    """Get suggestions for a specific mood"""
    place_type = request.args.get('place_type', 'restaurant')
    suggestions = get_mood_suggestions(mood, place_type)
    return jsonify({
        "mood": mood,
        "place_type": place_type,
        "suggestions": suggestions
    })

@app.route('/api/update-profile', methods=['POST'])
def api_update_profile():
    """Update user profile"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Authentication required"}), 401
    
    data = request.get_json()
    user = User.query.get(session['user_id'])
    
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Update profile fields
    if 'username' in data and data['username'].strip():
        # Check if username is already taken by another user
        existing_user = User.query.filter(User.username == data['username'].strip(), User.id != user.id).first()
        if existing_user:
            return jsonify({"success": False, "message": "Username already taken"}), 400
        user.username = data['username'].strip()
        session['username'] = user.username
    
    if 'age' in data and data['age']:
        user.age = int(data['age'])
    
    if 'gender' in data and data['gender'].strip():
        user.gender = data['gender'].strip()
    
    db.session.commit()
    
    return jsonify({"success": True, "message": "Profile updated successfully"})
# Add these routes to your fomo.py file (after the existing admin routes)

@app.route('/api/admin/export/users', methods=['GET'])
@require_admin
def export_users_csv():
    """Export all users data as CSV"""
    try:
        # Get all users (excluding admins for security)
        users = User.query.filter_by(is_admin=False).all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Username', 'Email', 'Age', 'Gender', 'Is Active', 
            'Created At', 'Last Login', 'Total Searches', 'Total Feedback'
        ])
        
        # Write user data
        for user in users:
            search_count = SearchHistory.query.filter_by(user_id=user.id).count()
            feedback_count = Feedback.query.filter_by(user_id=user.id).count()
            
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.age or '',
                user.gender or '',
                'Yes' if user.is_active else 'No',
                user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
                search_count,
                feedback_count
            ])
        
        # Create file-like object
        output.seek(0)
        csv_data = io.BytesIO(output.getvalue().encode('utf-8'))
        
        filename = f"foodmood_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Log admin activity
        log_admin_activity(session['user_id'], "data_exported", "users", None, 
                          f"Exported {len(users)} users to CSV")
        
        return send_file(
            csv_data,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Error exporting users: {str(e)}")
        return jsonify({"success": False, "message": "Failed to export users"}), 500

@app.route('/api/admin/export/searches', methods=['GET'])
@require_admin
def export_searches_csv():
    """Export all search history as CSV"""
    try:
        # Get all searches with user info
        searches = db.session.query(SearchHistory, User).join(
            User, SearchHistory.user_id == User.id
        ).filter(User.is_admin == False).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Search ID', 'Username', 'User Email', 'Mood', 'Place Type', 
            'Location', 'Custom Query', 'Results Count', 'Search Date', 
            'Latitude', 'Longitude'
        ])
        
        # Write search data
        for search, user in searches:
            writer.writerow([
                search.id,
                user.username,
                user.email,
                search.mood or '',
                search.place_type,
                search.location or '',
                search.custom_query or '',
                search.results_count,
                search.search_date.strftime('%Y-%m-%d %H:%M:%S'),
                search.latitude or '',
                search.longitude or ''
            ])
        
        output.seek(0)
        csv_data = io.BytesIO(output.getvalue().encode('utf-8'))
        
        filename = f"foodmood_searches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Log admin activity
        log_admin_activity(session['user_id'], "data_exported", "searches", None, 
                          f"Exported {len(searches)} searches to CSV")
        
        return send_file(
            csv_data,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Error exporting searches: {str(e)}")
        return jsonify({"success": False, "message": "Failed to export searches"}), 500

@app.route('/api/admin/export/feedback', methods=['GET'])
@require_admin
def export_feedback_csv():
    """Export all feedback as CSV"""
    try:
        # Get all feedback with user info
        feedback_query = db.session.query(Feedback, User).outerjoin(
            User, Feedback.user_id == User.id
        ).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Feedback ID', 'Username', 'Name', 'Email', 'Type', 'Rating', 
            'Title', 'Message', 'Device', 'Features', 'Status', 'Admin Notes',
            'Is Public', 'Timestamp', 'IP Address', 'User Agent'
        ])
        
        # Write feedback data
        for feedback, user in feedback_query:
            writer.writerow([
                feedback.id,
                user.username if user else 'Anonymous',
                feedback.name,
                feedback.email,
                feedback.type,
                feedback.rating,
                feedback.title,
                feedback.message.replace('\n', ' ').replace('\r', ' '),  # Clean newlines
                feedback.device or '',
                feedback.features or '',
                feedback.status,
                feedback.admin_notes or '',
                'Yes' if feedback.is_public else 'No',
                feedback.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                feedback.ip_address or '',
                (feedback.user_agent or '').replace('\n', ' ').replace('\r', ' ')
            ])
        
        output.seek(0)
        csv_data = io.BytesIO(output.getvalue().encode('utf-8'))
        
        filename = f"foodmood_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Log admin activity
        log_admin_activity(session['user_id'], "data_exported", "feedback", None, 
                          f"Exported {len(feedback_query)} feedback records to CSV")
        
        return send_file(
            csv_data,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Error exporting feedback: {str(e)}")
        return jsonify({"success": False, "message": "Failed to export feedback"}), 500

@app.route('/api/admin/export/admin-activities', methods=['GET'])
@require_admin
def export_admin_activities_csv():
    """Export all admin activities as CSV"""
    try:
        # Get all admin activities with admin user info
        activities = db.session.query(AdminActivity, User).join(
            User, AdminActivity.admin_id == User.id
        ).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Activity ID', 'Admin Username', 'Admin Email', 'Action', 
            'Target Type', 'Target ID', 'Details', 'Timestamp'
        ])
        
        # Write activity data
        for activity, admin in activities:
            writer.writerow([
                activity.id,
                admin.username,
                admin.email,
                activity.action,
                activity.target_type,
                activity.target_id or '',
                activity.details or '',
                activity.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output.seek(0)
        csv_data = io.BytesIO(output.getvalue().encode('utf-8'))
        
        filename = f"foodmood_admin_activities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Log admin activity
        log_admin_activity(session['user_id'], "data_exported", "admin_activities", None, 
                          f"Exported {len(activities)} admin activities to CSV")
        
        return send_file(
            csv_data,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Error exporting admin activities: {str(e)}")
        return jsonify({"success": False, "message": "Failed to export admin activities"}), 500

@app.route('/api/admin/export/newsletter', methods=['GET'])
@require_admin
def export_newsletter_csv():
    """Export all newsletter subscriptions as CSV (if Newsletter model exists)"""
    try:
        # Check if Newsletter table exists
        if not hasattr(globals().get('Newsletter', None), '__tablename__'):
            return jsonify({"success": False, "message": "Newsletter table not found"}), 404
        
        # Get all newsletter subscriptions
        subscriptions = Newsletter.query.all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Email', 'Subscribed At', 'Is Active', 'IP Address', 'User Agent'
        ])
        
        # Write subscription data
        for sub in subscriptions:
            writer.writerow([
                sub.id,
                sub.email,
                sub.subscribed_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Yes' if sub.is_active else 'No',
                sub.ip_address or '',
                (sub.user_agent or '').replace('\n', ' ').replace('\r', ' ')
            ])
        
        output.seek(0)
        csv_data = io.BytesIO(output.getvalue().encode('utf-8'))
        
        filename = f"foodmood_newsletter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Log admin activity
        log_admin_activity(session['user_id'], "data_exported", "newsletter", None, 
                          f"Exported {len(subscriptions)} newsletter subscriptions to CSV")
        
        return send_file(
            csv_data,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Error exporting newsletter: {str(e)}")
        return jsonify({"success": False, "message": "Failed to export newsletter data"}), 500

@app.route('/api/admin/export/complete-backup', methods=['GET'])
@require_admin
def export_complete_backup():
    """Export all data as a ZIP file containing multiple CSVs"""
    try:
        # Create a ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            # 1. Export Users
            users = User.query.filter_by(is_admin=False).all()
            users_csv = io.StringIO()
            users_writer = csv.writer(users_csv)
            users_writer.writerow(['ID', 'Username', 'Email', 'Age', 'Gender', 'Is Active', 'Created At', 'Last Login'])
            for user in users:
                users_writer.writerow([
                    user.id, user.username, user.email, user.age or '', user.gender or '',
                    'Yes' if user.is_active else 'No',
                    user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                    user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else ''
                ])
            zip_file.writestr('users.csv', users_csv.getvalue())
            
            # 2. Export Search History
            searches = db.session.query(SearchHistory, User).join(User, SearchHistory.user_id == User.id).filter(User.is_admin == False).all()
            searches_csv = io.StringIO()
            searches_writer = csv.writer(searches_csv)
            searches_writer.writerow(['Search ID', 'Username', 'Mood', 'Place Type', 'Location', 'Custom Query', 'Results Count', 'Search Date', 'Latitude', 'Longitude'])
            for search, user in searches:
                searches_writer.writerow([
                    search.id, user.username, search.mood or '', search.place_type,
                    search.location or '', search.custom_query or '', search.results_count,
                    search.search_date.strftime('%Y-%m-%d %H:%M:%S'),
                    search.latitude or '', search.longitude or ''
                ])
            zip_file.writestr('search_history.csv', searches_csv.getvalue())
            
            # 3. Export Feedback
            feedback_query = db.session.query(Feedback, User).outerjoin(User, Feedback.user_id == User.id).all()
            feedback_csv = io.StringIO()
            feedback_writer = csv.writer(feedback_csv)
            feedback_writer.writerow(['Feedback ID', 'Username', 'Name', 'Email', 'Type', 'Rating', 'Title', 'Message', 'Status', 'Timestamp'])
            for feedback, user in feedback_query:
                feedback_writer.writerow([
                    feedback.id, user.username if user else 'Anonymous', feedback.name,
                    feedback.email, feedback.type, feedback.rating, feedback.title,
                    feedback.message.replace('\n', ' '), feedback.status,
                    feedback.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                ])
            zip_file.writestr('feedback.csv', feedback_csv.getvalue())
            
            # 4. Export Admin Activities
            activities = db.session.query(AdminActivity, User).join(User, AdminActivity.admin_id == User.id).all()
            activities_csv = io.StringIO()
            activities_writer = csv.writer(activities_csv)
            activities_writer.writerow(['Activity ID', 'Admin Username', 'Action', 'Target Type', 'Target ID', 'Details', 'Timestamp'])
            for activity, admin in activities:
                activities_writer.writerow([
                    activity.id, admin.username, activity.action, activity.target_type,
                    activity.target_id or '', activity.details or '',
                    activity.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                ])
            zip_file.writestr('admin_activities.csv', activities_csv.getvalue())
            
            # 5. Export Newsletter (if exists)
            try:
                if hasattr(globals().get('Newsletter', None), '__tablename__'):
                    subscriptions = Newsletter.query.all()
                    newsletter_csv = io.StringIO()
                    newsletter_writer = csv.writer(newsletter_csv)
                    newsletter_writer.writerow(['ID', 'Email', 'Subscribed At', 'Is Active'])
                    for sub in subscriptions:
                        newsletter_writer.writerow([
                            sub.id, sub.email,
                            sub.subscribed_at.strftime('%Y-%m-%d %H:%M:%S'),
                            'Yes' if sub.is_active else 'No'
                        ])
                    zip_file.writestr('newsletter_subscriptions.csv', newsletter_csv.getvalue())
            except:
                pass  # Newsletter table might not exist
            
            # 6. Create a summary report
            summary_csv = io.StringIO()
            summary_writer = csv.writer(summary_csv)
            summary_writer.writerow(['Metric', 'Count'])
            summary_writer.writerow(['Total Users', len(users)])
            summary_writer.writerow(['Total Searches', len(searches)])
            summary_writer.writerow(['Total Feedback', len(feedback_query)])
            summary_writer.writerow(['Total Admin Activities', len(activities)])
            summary_writer.writerow(['Export Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            summary_writer.writerow(['Exported By', session.get('username', 'Unknown')])
            zip_file.writestr('summary_report.csv', summary_csv.getvalue())
            
            # 7. Add README file
            readme_content = f"""
Food Mood Database Backup
=========================

Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Exported By: {session.get('username', 'Unknown')}

Files Included:
- users.csv: All user accounts (excluding admins)
- search_history.csv: All search queries and results
- feedback.csv: All user feedback and reviews
- admin_activities.csv: All admin actions and changes
- newsletter_subscriptions.csv: Newsletter subscribers (if applicable)
- summary_report.csv: Summary statistics

Notes:
- All dates are in YYYY-MM-DD HH:MM:SS format
- This backup can be used to restore data or migrate to a new database
- Passwords are not included for security reasons
- Admin accounts are excluded from the users export

For technical support, contact the development team.
            """
            zip_file.writestr('README.txt', readme_content)
        
        zip_buffer.seek(0)
        filename = f"foodmood_complete_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        # Log admin activity
        log_admin_activity(session['user_id'], "complete_backup_exported", "database", None, 
                          f"Complete database backup exported as {filename}")
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Error creating complete backup: {str(e)}")
        return jsonify({"success": False, "message": "Failed to create complete backup"}), 500

@app.route('/api/admin/export/database-schema', methods=['GET'])
@require_admin
def export_database_schema():
    """Export database schema for recreation"""
    try:
        # Get all table names and their columns
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        schema_info = []
        schema_info.append("# Food Mood Database Schema")
        schema_info.append("# Generated on: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        schema_info.append("")
        
        for table_name in tables:
            columns = inspector.get_columns(table_name)
            schema_info.append(f"## Table: {table_name}")
            schema_info.append("")
            
            for column in columns:
                col_info = f"- {column['name']}: {column['type']}"
                if column.get('nullable'):
                    col_info += " (nullable)"
                if column.get('primary_key'):
                    col_info += " (primary key)"
                schema_info.append(col_info)
            
            schema_info.append("")
        
        # Create the schema file
        schema_content = '\n'.join(schema_info)
        schema_buffer = io.BytesIO(schema_content.encode('utf-8'))
        
        filename = f"foodmood_schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        # Log admin activity
        log_admin_activity(session['user_id'], "schema_exported", "database", None, 
                          "Database schema exported")
        
        return send_file(
            schema_buffer,
            mimetype='text/markdown',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Error exporting schema: {str(e)}")
        return jsonify({"success": False, "message": "Failed to export schema"}), 500

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Cache-Control'] = 'no-store'
    return response

def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    # Create tables before running the app
    create_tables()
    app.run(debug=True, host='0.0.0.0', port=5001)
