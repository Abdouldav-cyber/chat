import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib
import os

INTENTS_CSV = os.path.join('dataset', 'intents.csv')
VEC_PATH = os.path.join('services','vectorizer.pkl')
MODEL_PATH = os.path.join('services','classifier.pkl')

def train_model():
    if not os.path.exists(INTENTS_CSV):
        print('Le fichier dataset/intents.csv est manquant. CrÃ©ez-le d\'abord.')
        return
    df = pd.read_csv(INTENTS_CSV)
    df = df.dropna(subset=['example','intent'])
    X = df['example'].astype(str)
    y = df['intent'].astype(str)
    vec = TfidfVectorizer(stop_words='french', max_features=5000)
    Xv = vec.fit_transform(X)
    model = LogisticRegression(max_iter=1000)
    model.fit(Xv, y)
    os.makedirs('services', exist_ok=True)
    joblib.dump(vec, VEC_PATH)
    joblib.dump(model, MODEL_PATH)
    print('EntraÃ®nement terminÃ©. ModÃ¨les sauvegardÃ©s.')

if __name__ == '__main__':
    train_model()
