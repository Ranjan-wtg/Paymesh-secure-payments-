import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    ConfusionMatrixDisplay,
    roc_curve,
    auc,
    precision_recall_curve,
    PrecisionRecallDisplay
)
import matplotlib.pyplot as plt
import matplotlib
import pickle
import os
import seaborn as sns

# Set your path
DATA_PATH = r"D:\The New Data Trio\phishing_svm_dataset.csv"
MODEL_PATH = r"D:\The New Data Trio\phishing_svm_model.pkl"
PLOT_DIR = r"D:\The New Data Trio\plots0"

# Create plot directory if not exists
os.makedirs(PLOT_DIR, exist_ok=True)

# Set plot style
sns.set(style="whitegrid")
matplotlib.rcParams['figure.dpi'] = 300
plt.rcParams["axes.edgecolor"] = "0.15"
plt.rcParams["axes.linewidth"] = 1.25

# Load data
df = pd.read_csv(DATA_PATH)
X = df["text"]
y = df["label"]

# Split for validation
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Create pipeline
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=5000)),
    ('clf', LinearSVC())
])

# Train model
pipeline.fit(X_train, y_train)
accuracy = pipeline.score(X_test, y_test)
print(f"✅ Model trained with accuracy: {accuracy:.2%}")

# Generate predictions
y_pred = pipeline.predict(X_test)
y_scores = pipeline.decision_function(X_test)

# Save model
with open(MODEL_PATH, "wb") as f:
    pickle.dump(pipeline, f)
print(f"✅ Model saved at: {MODEL_PATH}")

# ========================
# Paper-Ready Visualizations
# ========================

# 1. Classification Report
report = classification_report(y_test, y_pred, output_dict=True)
report_df = pd.DataFrame(report).transpose()
report_df.to_csv(os.path.join(PLOT_DIR, "classification_report.csv"))
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# 2. Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm)
disp.plot(cmap="Blues", values_format="d")
plt.title("Confusion Matrix - Phishing Detection")
plt.savefig(os.path.join(PLOT_DIR, "confusion_matrix.png"), bbox_inches="tight")
plt.close()

# 3. ROC Curve
fpr, tpr, _ = roc_curve(y_test, y_scores)
roc_auc = auc(fpr, tpr)

plt.figure()
plt.plot(fpr, tpr, color='darkorange', lw=2, 
         label=f'ROC curve (AUC = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve - Phishing Detection')
plt.legend(loc="lower right")
plt.savefig(os.path.join(PLOT_DIR, "roc_curve.png"), bbox_inches="tight")
plt.close()

# 4. Precision-Recall Curve
precision, recall, _ = precision_recall_curve(y_test, y_scores)
disp = PrecisionRecallDisplay(precision=precision, recall=recall)
disp.plot()
plt.title('Precision-Recall Curve - Phishing Detection')
plt.savefig(os.path.join(PLOT_DIR, "precision_recall_curve.png"), bbox_inches="tight")
plt.close()

# 5. Feature Importance (Top 20)
feature_names = pipeline.named_steps['tfidf'].get_feature_names_out()
coefs = pipeline.named_steps['clf'].coef_[0]  # ✅ Fixed: removed .toarray()
top_features = pd.DataFrame({
    'feature': feature_names,
    'importance': coefs
}).sort_values('importance', ascending=False).head(20)

plt.figure(figsize=(10, 6))
sns.barplot(data=top_features, x='importance', y='feature', palette="viridis")
plt.title('Top 20 Important Features for Phishing Detection')
plt.xlabel('Feature Importance')
plt.ylabel('')
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "feature_importance.png"), bbox_inches="tight")
plt.close()

print(f"✅ All metrics and plots saved to: {PLOT_DIR}")
