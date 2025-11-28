from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, accuracy_score
import joblib

# Resolve paths so it works no matter where you run it from
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "internships.csv"
MODEL_DIR = ROOT / "model"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# 1) Load dataset
df = pd.read_csv(DATA_PATH)

# 2) Features/labels
X = df["description"].astype(str)
y = df["label"].astype(str)

# 3) Vectorize
vectorizer = TfidfVectorizer(stop_words="english")
X_vec = vectorizer.fit_transform(X)

# 4) Split
X_train, X_test, y_train, y_test = train_test_split(
    X_vec, y, test_size=0.2, random_state=42, stratify=y
)

# 5) Train model
model = MultinomialNB()
model.fit(X_train, y_train)

# 6) Evaluate
y_pred = model.predict(X_test)
print("Accuracy:", round(accuracy_score(y_test, y_pred), 4))
print(classification_report(y_test, y_pred))

# 7) Save artifacts
joblib.dump(model, MODEL_DIR / "internship_model.pkl")
joblib.dump(vectorizer, MODEL_DIR / "vectorizer.pkl")
print("✅ Saved: model/internship_model.pkl and model/vectorizer.pkl")
