import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import pickle
import os

# ✅ Set your path
DATA_PATH = r"D:\The New Data Trio\phishing_svm_dataset.csv"
MODEL_PATH = r"D:\The New Data Trio\phishing_svm_model.pkl"

# ✅ Load data
df = pd.read_csv(DATA_PATH)
X = df["text"]
y = df["label"]

# ✅ Split for validation
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# ✅ Create pipeline
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1,2), stop_words="english", max_features=5000)),
    ('clf', LinearSVC())
])

# ✅ Train model
pipeline.fit(X_train, y_train)
accuracy = pipeline.score(X_test, y_test)
print(f"✅ Model trained with accuracy: {accuracy:.2%}")

# ✅ Save model
with open(MODEL_PATH, "wb") as f:
    pickle.dump(pipeline, f)

print(f"✅ Model saved at: {MODEL_PATH}")
