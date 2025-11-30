from flask import Flask, render_template
from app.controllers.chat_controller import chat_api
from app.database.connection import get_db

app = Flask(__name__)

# 1) Page d'accueil (chat.html)
@app.route('/')
def home():
    return render_template('chat.html')

# 2) Page du chatbot (chatbot.html)
@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

# 3) API du chatbot (POST)
@app.route('/chat', methods=['POST'])
def chat():
    return chat_api()

# 4) Test de la connexion MySQL
@app.route("/test-db")
def test_db():
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        cur.close()
        db.close()
        return f"Connexion MySQL OK ✔️ — Résultat : {result}"
    except Exception as e:
        return f"Erreur MySQL ❌ : {str(e)}"

# Afficher toutes les routes Flask au démarrage (débogage uniquement)
print("📌 Routes enregistrées :")
print(app.url_map)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
