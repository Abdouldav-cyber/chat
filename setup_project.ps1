# setup_project.ps1
# Usage: Exécutez ce script dans le dossier du projet pour créer l'arborescence et les fichiers.

$ErrorActionPreference = "Stop"

# Créer arborescence
$dirs = @(
    "app",
    "app/controllers",
    "app/models",
    "app/views",
    "app/services",
    "app/database",
    "dataset",
    "templates",
    "static",
    "services"
)
foreach ($d in $dirs) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d | Out-Null }
}

# .gitignore
@"
venv/
.venv/
__pycache__/
*.pyc
services/*.pkl
*.sqlite3
.env
"@ | Out-File -Encoding utf8 ".gitignore"

# requirements.txt
@"
Flask>=2.0
scikit-learn>=1.0
pandas>=1.3
mysql-connector-python>=8.0
joblib
numpy
"@ | Out-File -Encoding utf8 "requirements.txt"

# app.py (point d'entrée)
@"
from flask import Flask, request, jsonify, render_template
from app.controllers.chat_controller import chat, home, train

app = Flask(__name__, template_folder='templates', static_folder='static')

app.add_url_rule('/', 'home', home, methods=['GET'])
app.add_url_rule('/chat', 'chat', chat, methods=['POST'])
app.add_url_rule('/train', 'train', train, methods=['POST'])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
"@ | Out-File -Encoding utf8 "app.py"

# app/controllers/chat_controller.py
@"
import json
from flask import request, jsonify, render_template
from app.services.nlp_service import predict_intent, load_models
from app.database.connection import get_db
import joblib
import os

# charge les modèles si présents
VEC, MODEL = load_models()

def home():
    return render_template('chat.html')

def get_answer_from_db(intent):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute('SELECT answer FROM intents WHERE intent_name=%s LIMIT 1', (intent,))
    row = cur.fetchone()
    cur.close()
    db.close()
    if row:
        return row['answer']
    return None

def chat():
    data = request.get_json(force=True)
    message = data.get('message', '')
    intent = predict_intent(message, VEC, MODEL)
    answer = get_answer_from_db(intent)
    if not answer:
        answer = \"Désolé, je n'ai pas trouvé de réponse dans la base. Vous pouvez ajouter cette Q/R au dataset.\"
    return jsonify({'intent': intent, 'answer': answer})

def train():
    # endpoint simple pour relancer l'entraînement (sécuriser en prod)
    from services.training import train_model
    train_model()
    return jsonify({'status':'trained'})
"@ | Out-File -Encoding utf8 "app/controllers/chat_controller.py"

# app/services/nlp_service.py
@"
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
"@ | Out-File -Encoding utf8 "app/services/nlp_service.py"

# app/database/connection.py
@"
import mysql.connector
import os

def get_db():
    # Lire variables d'environnement si existantes
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASS = os.environ.get('DB_PASS', '')
    DB_NAME = os.environ.get('DB_NAME', 'chatbot_rh')

    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset='utf8mb4'
    )
    return conn
"@ | Out-File -Encoding utf8 "app/database/connection.py"

# services/training.py (entraîneur)
@"
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
        print('Le fichier dataset/intents.csv est manquant. Créez-le d\'abord.')
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
    print('Entraînement terminé. Modèles sauvegardés.')

if __name__ == '__main__':
    train_model()
"@ | Out-File -Encoding utf8 "services/training.py"

# dataset/intents.csv (exemple minimal)
@"
intent,example,answer
conge_general,comment calculer mes congés ?,Vous avez droit à 2.5 jours/mois de service effectif.
prime_anciennete,comment calculer la prime d'ancienneté ?,La prime d'ancienneté est calculée sur la base du salaire et du nombre d'années.
heures_sup,taux des heures supplémentaires,Les heures supplémentaires se calculent par semaine; vérifiez le code du travail local.
"@ | Out-File -Encoding utf8 "dataset/intents.csv"

# dataset/clean_whatsapp.py (script nettoyage)
@"
import re

def nettoyer_whatsapp(infile, outfile):
    with open(infile, 'r', encoding='utf-8') as f:
        txt = f.read()
    # supprimer timestamps et numéros basiques
    txt = re.sub(r'\d{2}/\d{2}/\d{4}.*?- ', '', txt)
    txt = re.sub(r'\+?\d{1,3} ?\d{2}(?: \d{2}){3,4}', '', txt)
    txt = txt.replace('<Médias omis>', '')
    lignes = [l.strip() for l in txt.split('\\n') if len(l.strip())>10]
    with open(outfile, 'w', encoding='utf-8') as f:
        for l in lignes:
            f.write(l + '\\n')

if __name__ == '__main__':
    nettoyer_whatsapp('Discussion WhatsApp avec Professionnels des RH.txt', 'dataset/whatsapp_clean.txt')
"@ | Out-File -Encoding utf8 "dataset/clean_whatsapp.py"

# templates/chat.html
@"
<!doctype html>
<html lang='fr'>
  <head>
    <meta charset='utf-8'>
    <title>Chatbot RH</title>
    <link rel='stylesheet' href='/static/style.css'>
  </head>
  <body>
    <div class='container'>
      <h1>Chatbot RH</h1>
      <div id='chatbox'></div>
      <input id='msg' placeholder='Posez votre question...' />
      <button id='send'>Envoyer</button>
    </div>

    <script>
      document.getElementById('send').onclick = async function(){
        const msg = document.getElementById('msg').value;
        if(!msg) return;
        const resp = await fetch('/chat', {
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({message: msg})
        });
        const data = await resp.json();
        const box = document.getElementById('chatbox');
        box.innerHTML += '<div class=\"user\">Q: '+msg+'</div>';
        box.innerHTML += '<div class=\"bot\">A: '+data.answer+'</div>';
        document.getElementById('msg').value = '';
      }
    </script>
  </body>
</html>
"@ | Out-File -Encoding utf8 "templates/chat.html"

# static/style.css
@"
body { font-family: Arial, sans-serif; padding: 20px; background:#f7f7f7; }
.container { max-width:700px; margin:0 auto; background:white; padding:20px; border-radius:6px; box-shadow:0 2px 6px rgba(0,0,0,0.1);}
#chatbox { min-height:200px; border:1px solid #eee; padding:10px; margin-bottom:10px; overflow:auto; max-height:400px;}
.user { color: #0b6; margin:6px 0; }
.bot { color:#06b; margin:6px 0;}
input { width:80%; padding:10px; margin-right:6px;}
button { padding:10px 14px;}
"@ | Out-File -Encoding utf8 "static/style.css"

# app/models/intent_model.py (simple helper)
@"
# Fichier helper; on utilise la table `intents` pour stocker réponses
# Vous pouvez compléter ici des fonctions d'insertion/lecture supplémentaires.
from app.database.connection import get_db

def insert_intent(intent_name, answer):
    db = get_db()
    cur = db.cursor()
    cur.execute('INSERT INTO intents (intent_name, answer) VALUES (%s,%s)', (intent_name, answer))
    db.commit()
    cur.close()
    db.close()
"@ | Out-File -Encoding utf8 "app/models/intent_model.py"

# README.md
@"
# RH Chatbot - Scaffold automatique

Exécution rapide:
1. Créer et activer venv: `py -3.10 -m venv .venv` puis `.\.venv\Scripts\Activate.ps1`
2. Installer dépendances: `pip install -r requirements.txt`
3. Préparer la BDD MySQL (voir migrations.sql)
4. Lancer l'entraînement: `python services/training.py`
5. Lancer l'app: `python app.py`

N'oubliez pas de configurer vos variables d'environnement DB (DB_USER, DB_PASS, DB_NAME).
"@ | Out-File -Encoding utf8 "README.md"

# migrations.sql (création BDD)
@"
CREATE DATABASE IF NOT EXISTS chatbot_rh CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE chatbot_rh;

CREATE TABLE IF NOT EXISTS intents (
  id INT AUTO_INCREMENT PRIMARY KEY,
  intent_name VARCHAR(255) UNIQUE,
  answer TEXT
);

CREATE TABLE IF NOT EXISTS messages (
  id INT AUTO_INCREMENT PRIMARY KEY,
  question TEXT,
  answer TEXT
);

CREATE TABLE IF NOT EXISTS demandes_rh (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user VARCHAR(255),
  type VARCHAR(100),
  contenu TEXT,
  statut VARCHAR(50) DEFAULT 'En attente',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"@ | Out-File -Encoding utf8 "migrations.sql"

Write-Host "Scaffold créé avec succès. Vérifiez les fichiers créés et éditez app/database/connection.py pour ajouter le mot de passe MySQL si besoin."
