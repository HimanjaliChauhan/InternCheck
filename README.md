#InternCheck
AI-powered internship scam detector and recommendation web app built with Flask, SQLite and simple ML/NLP heuristics.

#Summary
InternCheck analyses internship postings and resume/skill text to detect suspicious or fake internship listings, lets users report
suspicious postings,supports company posting and student applications, and provides simple recommendations based on skills.

#Features
Detects suspicious internship postings using ML (if model present) and heuristics.
Report suspicious postings and store reports in the database.
Company users can post internships; students can apply and view applications.
Basic recommendation feature (uses optional recommender module if available).
Admin view for reported postings.

#Tech stack
Flask - Jinja2 - SQLite - Python - scikit-learn (optional) - HTML/CSS

#Project structure
InternCheck/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── templates/              # Jinja2 HTML templates
├── static/                 # CSS, JS, images
├── model/                  # optional ML model & vectorizer pickles
├── db/                     # sqlite DB files (not required in repo)
└── screenshots/          

#Future Enhancements
- ML Model: scikit-learn Naive Bayes (Python 3.11 upgrade)
- Database: SQLite/PostgreSQL for user reports
- User Accounts: Save analysis history
- Dashboard: Analytics + trends
-API: REST endpoints for integrations
- Alerts: Email notifications for new scams
- Multi-language: Hindi + regional support

#Quick start (run locally)
Clone:
git clone https://github.com/HimanjaliChauhan/InternCheck.git

Enter project:
cd InternCheck

Create and activate venv:

Windows:
python -m venv venv
venv\Scripts\activate

macOS / Linux:
python -m venv venv
source venv/bin/activate

Install dependencies:
pip install -r requirements.txt

Start app:
python app.py

Open in browser:
http://127.0.0.1:5000

#Notes about dependencies
If requirements.txt is missing, create it locally with:
pip freeze > requirements.txt

Model files (if included) live in model/ as:
vectorizer.pkl
internship_model.pkl
If absent, the app will fall back to heuristics.

#How to use the app
Home page: paste internship description and click Check/Analyze to get a prediction and trust score.
Recommend: paste your skills/resume text and click Get Recommendations.
Reports: view platform stats; Admin → /admin/reports shows reported postings.
Manage: login as company/admin to post internships and manage applications.

#Environment 
The app uses an app secret key for sessions. Set it as an environment variable in production:
export FLASK_SECRET="your-strong-secret" (Windows PowerShell: $env:FLASK_SECRET="your-strong-secret")

Deployment
This project is deployed on render.

MIT License - Free to use

Live Demo Link:
https://interncheck.onrender.com





Built by Himanjali Chauhan | Final Year CS Student  
LinkedIn- https://www.linkedin.com/in/himanjali-chauhan-0a7aa9295/ 




