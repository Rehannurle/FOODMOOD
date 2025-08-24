# 🍽️ Food Mood - AI-Powered Mood-Based Discovery Platform

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-brightgreen?style=for-the-badge)](https://foodmood-fr4h.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-red?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

> **Food Mood** is an AI-powered web application that suggests restaurants, cafes, hotels, and dhabas based on your current mood and preferences. Created as a student project by **Rehan Nurle**, it helps users discover perfect dining experiences tailored to how they're feeling.

## 🌟 Live Demo

**🚀 [Try Food Mood Now](https://foodmood-fr4h.onrender.com)**

## 📋 Table of Contents

- [Features](#-features)
- [Screenshots](#-screenshots)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Environment Variables](#-environment-variables)
- [Database Setup](#-database-setup)
- [Deployment](#-deployment)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

## ✨ Features

### 🎭 **Mood-Based Discovery**
- Select your current mood (happy, sad, excited, stressed, etc.)
- Get AI-powered suggestions for restaurants, cafes, hotels, or dhabas
- Personalized recommendations based on emotional state

### 🗺️ **Location Intelligence**
- **GPS Integration**: Automatically detect your location
- **Manual Location**: Enter any city or area name
- **Radius Search**: Find places within your preferred distance
- **Best Coverage**: Mumbai, Delhi NCR, Bangalore, Pune, Hyderabad, Chennai, Kolkata

### 🏪 **Multi-Category Search**
- 🍽️ **Restaurants**: Fine dining, casual dining, ethnic cuisine
- ☕ **Cafes**: Coffee shops, tea houses, study spots
- 🏨 **Hotels**: Luxury, budget, business, romantic getaways
- 🛣️ **Dhabas**: Authentic roadside eateries, highway stops

### 👤 **User Management**
- Secure user registration and authentication
- Personal profile management
- Search history tracking
- Personalized dashboard

### 📊 **Advanced Analytics**
- Search history analysis
- Mood pattern tracking
- Popular place insights
- Personal statistics

### 💬 **Feedback System**
- Multi-type feedback (bugs, features, improvements)
- 5-star rating system
- Public testimonials
- Email notifications

### 🛡️ **Admin Dashboard**
- User management and analytics
- Feedback monitoring and responses
- Data export capabilities (CSV, ZIP)
- System activity logs
- Complete database backup

### 📧 **Email Integration**
- Welcome emails for new users
- Feedback notifications
- Newsletter subscriptions
- Contact form responses

## 🖼️ Screenshots

### Main Dashboard
![Dashboard](https://via.placeholder.com/800x400/4f46e5/ffffff?text=Food+Mood+Dashboard)

### Mood Selection
![Mood Selection](https://via.placeholder.com/800x400/059669/ffffff?text=Mood-Based+Search)

### Results Display
![Results](https://via.placeholder.com/800x400/dc2626/ffffff?text=Restaurant+Results)

## 🛠️ Tech Stack

### **Backend**
- ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) **Python 3.8+**
- ![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white) **Flask 2.0+**
- ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat&logo=sqlalchemy&logoColor=white) **SQLAlchemy ORM**
- ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white) **PostgreSQL (Production)**
- ![SQLite](https://img.shields.io/badge/SQLite-07405E?style=flat&logo=sqlite&logoColor=white) **SQLite (Development)**

### **Frontend**
- ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white) **HTML5**
- ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white) **CSS3**
- ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black) **Vanilla JavaScript**
- ![Bootstrap](https://img.shields.io/badge/Bootstrap-563D7C?style=flat&logo=bootstrap&logoColor=white) **Bootstrap 5**

### **APIs & Services**
- 🗺️ **Foursquare Places API**: Location data and restaurant information
- 📧 **SMTP Email**: Automated email notifications
- 🌐 **Geolocation API**: GPS-based location detection

### **Deployment**
- ![Render](https://img.shields.io/badge/Render-46E3B7?style=flat&logo=render&logoColor=white) **Render (Production)**
- ![GitHub](https://img.shields.io/badge/GitHub-100000?style=flat&logo=github&logoColor=white) **GitHub (Version Control)**

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Git
- Virtual Environment (recommended)

### 1. Clone the Repository
```bash
git clone https://github.com/Rehannurle/FOODMOOD.git
cd FOODMOOD
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the root directory:
```bash
cp .env.example .env
```

### 5. Run the Application
```bash
python fomo.py
```

The application will be available at `http://localhost:5001`

## 🔧 Environment Variables

Create a `.env` file in your project root with the following variables:

### **Required Environment Variables**

```bash
# Application Security
SECRET_KEY=your-super-secret-key-here-min-32-characters-long

# Database Configuration
DATABASE_URL=postgresql://username:password@host:port/database_name
# For local development, leave blank to use SQLite

# Foursquare API (Required for place search)
FOURSQUARE_API_KEY=your-foursquare-api-key-here

# Email Configuration (Optional but recommended)
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-specific-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
ADMIN_EMAIL=admin@yourapp.com
```

### **Setting Up Environment Variables**

#### **1. Local Development (.env file)**
```bash
# Create .env file
touch .env

# Add your environment variables
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" >> .env
echo "FOURSQUARE_API_KEY=your_api_key_here" >> .env
echo "EMAIL_USER=your_email@gmail.com" >> .env
echo "EMAIL_PASS=your_app_password" >> .env
echo "ADMIN_EMAIL=admin@yourapp.com" >> .env
```

#### **2. Render Deployment**
In your Render dashboard:
1. Go to your service settings
2. Navigate to "Environment" tab
3. Add these key-value pairs:

```
SECRET_KEY=your-generated-secret-key
DATABASE_URL=postgresql://... (auto-provided by Render)
FOURSQUARE_API_KEY=your-foursquare-api-key
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-specific-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
ADMIN_EMAIL=admin@yourapp.com
```

#### **3. Heroku Deployment**
```bash
# Using Heroku CLI
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set FOURSQUARE_API_KEY="your-api-key"
heroku config:set EMAIL_USER="your-email@gmail.com"
heroku config:set EMAIL_PASS="your-app-password"
heroku config:set ADMIN_EMAIL="admin@yourapp.com"
```

### **API Keys Setup Guide**

#### **🗺️ Foursquare API Key**
1. Visit [Foursquare for Developers](https://developer.foursquare.com/)
2. Create an account and new project
3. Get your API key from the project dashboard
4. Add it to your environment variables

#### **📧 Gmail SMTP Setup**
1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App-specific password:
   - Go to Google Account settings
   - Security → App passwords
   - Generate password for "Mail"
3. Use this app password in `EMAIL_PASS` variable

### **Environment Variables Validation**
The app includes built-in validation for required environment variables. Check the console output on startup for any missing configurations.

## 💾 Database Setup

### **Local Development (SQLite)**
```bash
# SQLite database is created automatically
# No additional setup required
python fomo.py
```

### **Production (PostgreSQL)**

#### **Using Render Database**
1. Create a PostgreSQL database service on Render
2. Copy the connection string
3. Set `DATABASE_URL` environment variable

#### **Using External PostgreSQL**
```bash
# Format: postgresql://username:password@host:port/database_name
DATABASE_URL=postgresql://user:pass@localhost:5432/foodmood
```

### **Database Migration**
```bash
# Initialize migrations (first time only)
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

### **Create Admin User**
```python
# Run this in Python shell or create a script
from fomo import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User(
        username='admin',
        email='admin@yourapp.com',
        password_hash=generate_password_hash('your-secure-password'),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print("Admin user created successfully!")
```

## 🚢 Deployment

### **Deploy to Render**

1. **Fork/Clone the Repository**
   ```bash
   git clone https://github.com/Rehannurle/FOODMOOD.git
   cd FOODMOOD
   ```

2. **Create Render Account**
   - Visit [render.com](https://render.com)
   - Sign up with GitHub

3. **Create New Web Service**
   - Connect your GitHub repository
   - Configure build settings:
     ```
     Build Command: pip install -r requirements.txt
     Start Command: python fomo.py
     ```

4. **Add Environment Variables**
   - Add all required environment variables in Render dashboard

5. **Create PostgreSQL Database**
   - Create a new PostgreSQL service
   - Copy connection string to `DATABASE_URL`

6. **Deploy**
   - Render will automatically deploy your application
   - Access via the provided URL

### **Deploy to Heroku**

1. **Install Heroku CLI**
   ```bash
   # Install Heroku CLI from heroku.com/cli
   ```

2. **Login and Create App**
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Add PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

4. **Set Environment Variables**
   ```bash
   heroku config:set SECRET_KEY="your-secret-key"
   heroku config:set FOURSQUARE_API_KEY="your-api-key"
   # Add other environment variables
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

### **Deploy to AWS/GCP/Azure**
For cloud deployment, ensure you have:
- Environment variables configured
- Database connection established
- HTTPS enabled for production
- Static files served properly

## 📚 API Documentation

### **Authentication Endpoints**

#### **POST /api/login**
Login user and create session
```json
{
  "email": "user@example.com",
  "password": "userpassword"
}
```

#### **POST /api/register**
Register new user
```json
{
  "username": "newuser",
  "email": "new@example.com",
  "password": "newpassword",
  "age": 25,
  "gender": "male"
}
```

#### **POST /api/logout**
Logout current user

### **Search Endpoints**

#### **POST /api/search**
Search for places based on mood and location
```json
{
  "mood": "happy",
  "place_type": "restaurant",
  "location": "Mumbai",
  "latitude": 19.0760,
  "longitude": 72.8777,
  "custom_query": "pizza"
}
```

**Response:**
```json
{
  "success": true,
  "places": [
    {
      "name": "Restaurant Name",
      "address": "Complete Address",
      "category": "Italian Restaurant",
      "rating": 4.5,
      "price": 3,
      "distance": 2.1,
      "website": "https://restaurant.com",
      "phone": "+91-XXXXXXXXXX"
    }
  ],
  "count": 15
}
```

### **Feedback Endpoints**

#### **POST /api/feedback**
Submit user feedback
```json
{
  "name": "User Name",
  "email": "user@example.com",
  "type": "feature",
  "rating": 5,
  "title": "Great App!",
  "message": "Love the mood-based search feature",
  "device": "Desktop",
  "features": ["mood-search", "location-detection"]
}
```

### **Admin Endpoints**

#### **GET /api/admin/stats**
Get dashboard statistics (admin only)

#### **GET /api/admin/users**
Get paginated users list (admin only)

#### **POST /api/admin/export/users**
Export users data as CSV (admin only)

## 📁 Project Structure

```
FOODMOOD/
├── fomo.py                 # Main Flask application
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore            # Git ignore rules
├── README.md             # Project documentation
├── static/               # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Main dashboard
│   ├── login.html       # Login page
│   ├── register.html    # Registration page
│   ├── profile.html     # User profile
│   ├── feedback.html    # Feedback form
│   ├── admin_dashboard.html  # Admin panel
│   └── ...
├── migrations/           # Database migrations
├── instance/            # Instance-specific files
└── venv/               # Virtual environment (local)
```

## 🧪 Testing

### **Run Tests**
```bash
# Install testing dependencies
pip install pytest pytest-flask

# Run tests
pytest

# Run with coverage
pytest --cov=fomo
```

### **Manual Testing Checklist**
- [ ] User registration and login
- [ ] Mood-based search functionality
- [ ] Location detection and manual entry
- [ ] Search results display and formatting
- [ ] Profile management
- [ ] Feedback submission
- [ ] Admin dashboard access
- [ ] Email notifications
- [ ] Mobile responsiveness

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### **1. Fork the Repository**
```bash
git fork https://github.com/Rehannurle/FOODMOOD.git
```

### **2. Create Feature Branch**
```bash
git checkout -b feature/amazing-feature
```

### **3. Make Changes**
- Follow Python PEP 8 style guide
- Add docstrings to functions
- Update tests if necessary
- Update documentation

### **4. Commit Changes**
```bash
git commit -m "Add amazing feature"
```

### **5. Push and Create PR**
```bash
git push origin feature/amazing-feature
```

### **Contribution Guidelines**
- Follow existing code style and structure
- Add comments for complex logic
- Test your changes thoroughly
- Update README if adding new features
- Be respectful and collaborative

### **Areas for Contribution**
- 🔍 **Search Algorithm**: Improve mood-to-place matching
- 🗺️ **Location Coverage**: Add support for more cities
- 🎨 **UI/UX**: Enhance user interface and experience
- 📱 **Mobile App**: Develop native mobile applications
- 🧪 **Testing**: Add comprehensive test coverage
- 📊 **Analytics**: Add more detailed insights and reports
- 🔧 **Performance**: Optimize database queries and API calls

## 🐛 Known Issues & Limitations

### **Current Limitations**
- Limited coverage in smaller cities and rural areas
- Foursquare API rate limits (5000 requests/day for free tier)
- Email notifications require SMTP configuration
- Real-time availability not supported

### **Planned Improvements**
- [ ] Integration with Google Places API for better coverage
- [ ] Real-time restaurant availability
- [ ] Social sharing features
- [ ] Voice-activated search
- [ ] Mobile apps for iOS and Android
- [ ] Integration with food delivery services
- [ ] AI-powered personalization
- [ ] Multi-language support

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Rehan Nurle

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## 📞 Contact & Support

### **Developer**
**Rehan Nurle** - *Creator & Lead Developer*
- 📧 Email: [Contact via GitHub](https://github.com/Rehannurle)
- 💼 LinkedIn: [Connect with Rehan](https://linkedin.com/in/rehannurle)
- 🐙 GitHub: [@Rehannurle](https://github.com/Rehannurle)

### **Project Links**
- 🌐 **Live Demo**: [foodmood-fr4h.onrender.com](https://foodmood-fr4h.onrender.com)
- 📂 **Source Code**: [github.com/Rehannurle/FOODMOOD](https://github.com/Rehannurle/FOODMOOD)
- 🐛 **Report Issues**: [GitHub Issues](https://github.com/Rehannurle/FOODMOOD/issues)

### **Support**
- 📖 Check the [Wiki](https://github.com/Rehannurle/FOODMOOD/wiki) for detailed guides
- 🐛 Report bugs via [GitHub Issues](https://github.com/Rehannurle/FOODMOOD/issues)
- 💡 Request features through [GitHub Discussions](https://github.com/Rehannurle/FOODMOOD/discussions)
- 📧 For private queries, use the contact form in the app

---

## 🎯 Quick Start Commands

```bash
# Clone and setup
git clone https://github.com/Rehannurle/FOODMOOD.git
cd FOODMOOD
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install and run
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python fomo.py
```

**🎉 That's it! Open http://localhost:5001 and start discovering places based on your mood!**

---

<div align="center">

### ⭐ Star this repository if you found it helpful!

*Made with ❤️ by [Rehan Nurle](https://github.com/Rehannurle)*

**Food Mood - Where Your Mood Meets Perfect Places! 🍽️✨**

</div>
