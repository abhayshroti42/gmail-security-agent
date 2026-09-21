"""
spam_classifier.py
-------------------
Loads the ALREADY-TRAINED TF-IDF vectorizer and MultinomialNB model from
disk (never retrains) and classifies email text as SPAM or NOT SPAM.

Preprocessing here is an exact copy of transform_text() from the original
spam-classifier project, because the loaded vectorizer's vocabulary was
built from text cleaned that exact way — any deviation (different
stemming, different stopword handling) would silently produce garbage
predictions.
"""

import os
import pickle
import string

import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

# ---------------------------------------------------------------------------
# One-time NLTK data check (safe to call every run — no-op if already present)
# ---------------------------------------------------------------------------

def _ensure_nltk_data():
    for resource, pkg in [("tokenizers/punkt_tab", "punkt_tab"),
                          ("corpora/stopwords", "stopwords")]:
        try:
            nltk.data.find(resource)
        except LookupError:
            nltk.download(pkg)

_ensure_nltk_data()

_STEMMER = PorterStemmer()
_STOPWORDS = set(stopwords.words("english"))  # cached once, not per-call


# ---------------------------------------------------------------------------
# Exact same cleaning pipeline used during training
# ---------------------------------------------------------------------------

def transform_text(text: str) -> str:
    """
    Reproduces the original notebook's transform_text() exactly:
    lowercase -> tokenize -> keep alphanumeric -> remove stopwords/
    punctuation -> stem. Must stay identical to training-time cleaning.
    """
    text = text.lower()
    tokens = nltk.word_tokenize(text)
    tokens = [t for t in tokens if t.isalnum()]
    tokens = [t for t in tokens if t not in _STOPWORDS and t not in string.punctuation]
    tokens = [_STEMMER.stem(t) for t in tokens]
    return " ".join(tokens)


# ---------------------------------------------------------------------------
# Load trained artifacts ONCE
# ---------------------------------------------------------------------------

_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
_VECTORIZER_PATH = os.path.join(_MODELS_DIR, "vectorizer.pkl")
_MODEL_PATH = os.path.join(_MODELS_DIR, "model.pkl")


def _load_pickle(path, label):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"[ERROR] {label} not found at: {path}\n"
            f"Copy your existing {os.path.basename(path)} from your spam-classifier "
            f"project into the models/ folder."
        )
    with open(path, "rb") as f:
        return pickle.load(f)


_VECTORIZER = _load_pickle(_VECTORIZER_PATH, "TF-IDF vectorizer")
_MODEL = _load_pickle(_MODEL_PATH, "MultinomialNB model")


# ---------------------------------------------------------------------------
# Public classification function
# ---------------------------------------------------------------------------

def classify_email(subject: str, body: str) -> dict:
    """
    Classify an email as SPAM or NOT SPAM using the loaded TF-IDF vectorizer
    and MultinomialNB model. Handles empty/missing subject or body safely.

    Args:
        subject: Email subject line (may be None or empty).
        body: Email body text (may be None or empty).

    Returns:
        dict: {"prediction": "SPAM" | "NOT SPAM", "confidence": float (0-100)}
    """
    combined_text = f"{subject or ''} {body or ''}".strip()

    if not combined_text:
        # No text at all to classify - default to NOT SPAM with 0 confidence
        # rather than guessing.
        return {"prediction": "NOT SPAM", "confidence": 0.0}

    cleaned = transform_text(combined_text)

    if not cleaned:
        # Text existed but nothing survived cleaning (e.g. pure punctuation/emoji)
        return {"prediction": "NOT SPAM", "confidence": 0.0}

    vector = _VECTORIZER.transform([cleaned])
    probabilities = _MODEL.predict_proba(vector)[0]  # [P(ham), P(spam)]

    spam_index = 1  # confirmed via LabelEncoder: ham=0, spam=1
    predicted_index = int(probabilities.argmax())

    label = "SPAM" if predicted_index == spam_index else "NOT SPAM"
    confidence = float(probabilities[predicted_index]) * 100

    return {"prediction": label, "confidence": confidence}


# ---------------------------------------------------------------------------
# Standalone test with hardcoded sample emails
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    samples = [
        ("Win a free iPhone now!", "Congratulations! You've won a FREE prize. Click here immediately to claim your reward before it expires!!!"),
        ("Meeting rescheduled", "Hi team, just a heads up that tomorrow's standup has been moved to 11am. See you then."),
        ("URGENT: Verify your account", "Your account has been suspended. Click this link now and enter your password to restore access."),
        ("Lunch tomorrow?", "Hey, are you free for lunch tomorrow around 1pm? Let me know."),
    ]

    print("=" * 40)
    print("Standalone spam_classifier.py test")
    print("=" * 40)
    for i, (subject, body) in enumerate(samples, start=1):
        result = classify_email(subject, body)
        print(f"\nSample {i}")
        print(f"Subject: {subject}")
        print(f"Prediction: {result['prediction']}")
        print(f"Confidence: {result['confidence']:.2f}%")
    print("\n" + "=" * 40)