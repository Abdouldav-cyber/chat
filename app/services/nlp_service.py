import joblib
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

VEC_PATH = os.path.join('services','vectorizer.pkl')
MODEL_PATH = os.path.join('services','classifier.pkl')

def load_models():
    vec = None
    model = None
    if os.path.exists(VEC_PATH) and os.path.exists(MODEL_PATH):
        vec = joblib.load(VEC_PATH)
        model = joblib.load(MODEL_PATH)
    return vec, model

def predict_intent(text, vec, model):
    if not vec or not model:
        return 'unknown_intent'
    X = vec.transform([text])
    pred = model.predict(X)[0]
    return pred
