import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# -----------------------------
# STEP 1: LOAD DATA
# -----------------------------
df = pd.read_csv("spam.csv", encoding="latin-1")

# Keep only relevant columns
df = df[["v1", "v2"]]
df.columns = ["label", "message"]

# Remove duplicates
df = df.drop_duplicates(subset="message")

print(f"Dataset loaded: {len(df)} messages")
print(f"Class distribution:\n{df['label'].value_counts()}\n")

# Encode labels: spam=1, ham=0
df["label_encoded"] = df["label"].map({"spam": 1, "ham": 0})

# -----------------------------
# STEP 2: FEATURE EXTRACTION (TF-IDF)
# -----------------------------
tfidf = TfidfVectorizer(
    max_features=5000,
    stop_words="english",
    ngram_range=(1, 2),   # unigrams + bigrams
    min_df=2
)

X = tfidf.fit_transform(df["message"])
y = df["label_encoded"]

# -----------------------------
# STEP 3: TRAIN/TEST SPLIT
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# -----------------------------
# STEP 4: TRAIN MODEL (Multinomial Naive Bayes)
# -----------------------------
model = MultinomialNB(alpha=0.1)
model.fit(X_train, y_train)

# -----------------------------
# STEP 5: EVALUATE
# -----------------------------
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print("==============================")
print("SPAM DETECTION MODEL RESULTS")
print("==============================")
print(f"Accuracy: {accuracy:.4f}")
print(f"\nConfusion Matrix:\n{confusion_matrix(y_test, y_pred)}")
print(f"\nClassification Report:\n{classification_report(y_test, y_pred, target_names=['HAM', 'SPAM'])}")

# -----------------------------
# STEP 6: SAVE MODEL + VECTORIZER
# -----------------------------
joblib.dump(model, "spam_model.pkl")
joblib.dump(tfidf, "spam_vectorizer.pkl")

print("✅ Spam model saved to spam_model.pkl")
print("✅ TF-IDF vectorizer saved to spam_vectorizer.pkl")

# -----------------------------
# STEP 7: QUICK DEMO
# -----------------------------
demo_messages = [
    "WINNER!! You have won a £1000 prize. Call 09061701461 to claim NOW!",
    "Hi, are you coming to the party tonight?",
    "URGENT: Your bank account has been compromised. Transfer funds immediately to secure account.",
    "Hey mom, I'll be home by 6 for dinner",
    "You are under digital arrest. Transfer ₹50,000 to this account or face legal action.",
    "Congratulations! You've been selected for a cash prize. Send your details NOW",
    "This is CBI officer calling. You are involved in money laundering. Pay fine immediately.",
]

print("\n==============================")
print("DEMO PREDICTIONS")
print("==============================")
for msg in demo_messages:
    X_demo = tfidf.transform([msg])
    pred = model.predict(X_demo)[0]
    prob = model.predict_proba(X_demo)[0]
    label = "🔴 SPAM" if pred == 1 else "🟢 HAM"
    confidence = max(prob) * 100
    print(f"{label} ({confidence:.1f}%) → {msg[:80]}")
