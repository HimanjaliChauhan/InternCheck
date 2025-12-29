InternCheck – AI-Powered Internship Scam Detector
InternCheck is a full-stack web application that detects fake internship postings using ML heuristics and rule-based analysis, enables scam reporting, supports company postings/student applications, and provides skill-based recommendations. Built to protect students from common internship scams in India.

Live Demo: https://interncheck.onrender.com
GitHub: github.com/HimanjaliChauhan/InternCheck
------------------------------------------------------------
Key Features

-Scam Detection: ML (Naive Bayes optional) + heuristics analyze stipend, fees, contact methods, job descriptions
-User Reporting: Students report suspicious postings (stored in SQLite)
-Company Portal: Post internships, manage applications
-Skill Recommendations: Match resume/skills to legitimate opportunities
-Admin Dashboard: View reported scams and platform stats
-Production Ready: Render deployment with session management
-------------------------------------------------------------------
Project Architecture

InternCheck/
│
├── app.py                  # Main Flask application
├── requirements.txt        # Dependencies
├── templates/              # Jinja2 HTML templates
├── static/                 # CSS, JS, images
├── model/                  # ML files (vectorizer.pkl, internship_model.pkl)
├── db/                     # SQLite database
└── screenshots/
----------------------------------------------------------------------
Tech Stack

-Category:	Technologies
-Backend:	Python, Flask, Jinja2
-Database:	SQLite
-ML/Heuristics:	scikit-learn (optional)
-Frontend	:HTML, CSS
-Deployment	:Render
-Version Control: Git, GitHub

-Dataset & Analysis
Analyzes these scam indicators:
Unrealistic stipends (₹0-₹5K red flags)
Training fees demands
Suspicious contact methods (WhatsApp only)
Vague job descriptions
Missing company details
ML Fallback: Uses heuristics if model files absent
----------------------------------------------------------------
How to Run Locally
Clone repository-   git clone https://github.com/HimanjaliChauhan/InternCheck.git
                    cd InternCheck
                    Create virtual environment
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate

-Install dependencies
pip install -r requirements.txt
-Set environment variable
export FLASK_SECRET="your-strong-secret-key"

Run application-  python app.py
Open: http://127.0.0.1:5000
-------------------------------------------------------------------
How InternCheck Is Different

Unlike basic scam checkers, InternCheck provides:
-Hybrid Detection: ML + rules (works without model files)
-Full Platform: Reporting, company postings, applications, recommendations
-Production Architecture: SQLite, sessions, admin dashboard
-Student-First: Real-time trust scores + prevention tips
-Scalable: Render deployment with proper secret management
--------------------------------------------------------------------------

Dashboard Modules

-Home/Analysis – Paste internship text → Get trust score
-Recommendations – Paste skills → Get matched opportunities
-Reports – View platform scam statistics
-Company Portal – Post internships, view applications
-Admin Dashboard – Manage reported postings
-----------------------------------------------------------------------------
Use Cases

-Student internship verification
-Campus placement cell integration
-Company legitimacy screening
-Data analytics/ML portfolio project
------------------------------------------------------------
Limitations
-ML model optional (falls back to heuristics)
-No user accounts (session-based)
-SQLite (not PostgreSQL for production scale)
-------------------------------------------------------------
Future Enhancements
-Naive Bayes ML model training
-User authentication & history
-REST API endpoints
-Email scam alerts
-Multi-language support (Hindi)
-Analytics dashboard
--------------------------------------------------------------
Author
Himanjali Chauhan
Final Year BSc Computer Science | Data Analytics & AI Enthusiast
-----------------------------------------------------------------
⭐ Star this repository if you find it useful!
📄 MIT License – Free to use and modify

