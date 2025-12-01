"""
Chatbot RH - Fonction Publique
Application Flask principale avec authentification
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
from datetime import timedelta
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Création de l'application Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chatbot-rh-secret-key-2024")
app.permanent_session_lifetime = timedelta(days=7)
CORS(app, supports_credentials=True)

# =============================================
# Import des contrôleurs
# =============================================
from app.controllers.chat_controller import chat_api, feedback_api
from app.controllers.auth_controller import (
    login, register, logout, get_current_user, change_password,
    login_required, gestionnaire_required
)
from app.controllers.demandes_controller import (
    creer_demande, liste_demandes, traiter_demande, annuler_demande
)
from app.controllers.notifications_controller import (
    get_notifications, marquer_lue, marquer_toutes_lues,
    verifier_echeances, creer_echeance, liste_echeances
)
from app.controllers.gestionnaire_controller import (
    dashboard_stats, liste_demandes_gestionnaire, liste_employes,
    detail_employe, analytics_chatbot, gerer_intents
)
from app.database.connection import get_db, execute_query

# =============================================
# Routes des pages HTML
# =============================================

@app.route('/')
def home():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Page de connexion"""
    if 'employe_id' in session:
        if session.get('role') in ['gestionnaire', 'admin']:
            return redirect(url_for('espace_gestionnaire'))
        return redirect(url_for('espace_employe'))
    return render_template('login.html')

@app.route('/chatbot')
def chatbot():
    """Interface du chatbot (accessible à tous)"""
    return render_template('chatbot.html')

@app.route('/employe')
@login_required
def espace_employe():
    """Espace employé (protégé)"""
    return render_template('employe.html')

@app.route('/gestionnaire')
@gestionnaire_required
def espace_gestionnaire():
    """Dashboard gestionnaire RH (protégé)"""
    return render_template('gestionnaire.html')

# =============================================
# API Authentification
# =============================================

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Connexion"""
    return login()

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """Inscription"""
    return register()

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """Déconnexion"""
    return logout()

@app.route('/api/auth/me', methods=['GET'])
def api_me():
    """Utilisateur courant"""
    return get_current_user()

@app.route('/api/auth/change-password', methods=['POST'])
@login_required
def api_change_password():
    """Changer mot de passe"""
    return change_password()

# =============================================
# API Chatbot
# =============================================

@app.route('/chat', methods=['POST'])
def chat():
    """API du chatbot"""
    return chat_api()

@app.route('/chat/feedback', methods=['POST'])
def chat_feedback():
    """Feedback sur les réponses du chatbot"""
    return feedback_api()

# =============================================
# API Demandes (protégées)
# =============================================

@app.route('/api/demandes', methods=['GET', 'POST'])
@login_required
def api_demandes():
    """Gestion des demandes"""
    if request.method == 'POST':
        return creer_demande()
    return liste_demandes()

@app.route('/api/demandes/traiter', methods=['PUT'])
@gestionnaire_required
def api_traiter_demande():
    """Traiter une demande (approuver/refuser)"""
    return traiter_demande()

@app.route('/api/demandes/annuler', methods=['PUT'])
@login_required
def api_annuler_demande():
    """Annuler une demande"""
    return annuler_demande()

# =============================================
# API Notifications (protégées)
# =============================================

@app.route('/api/notifications', methods=['GET'])
@login_required
def api_notifications():
    """Liste des notifications"""
    return get_notifications()

@app.route('/api/notifications/lue', methods=['PUT'])
@login_required
def api_marquer_lue():
    """Marquer une notification comme lue"""
    return marquer_lue()

@app.route('/api/notifications/lire-tout', methods=['PUT'])
@login_required
def api_marquer_toutes_lues():
    """Marquer toutes les notifications comme lues"""
    return marquer_toutes_lues()

# =============================================
# API Échéances (protégées)
# =============================================

@app.route('/api/echeances', methods=['GET', 'POST'])
@login_required
def api_echeances():
    """Gestion des échéances"""
    if request.method == 'POST':
        return creer_echeance()
    return liste_echeances()

@app.route('/api/echeances/verifier', methods=['POST'])
@gestionnaire_required
def api_verifier_echeances():
    """Vérifier les échéances et envoyer les notifications"""
    return verifier_echeances()

# =============================================
# API Gestionnaire RH (protégées)
# =============================================

@app.route('/api/gestionnaire/stats', methods=['GET'])
@gestionnaire_required
def api_gestionnaire_stats():
    """Statistiques du dashboard"""
    return dashboard_stats()

@app.route('/api/gestionnaire/demandes', methods=['GET'])
@gestionnaire_required
def api_gestionnaire_demandes():
    """Liste des demandes pour les gestionnaires"""
    return liste_demandes_gestionnaire()

@app.route('/api/gestionnaire/employes', methods=['GET'])
@gestionnaire_required
def api_gestionnaire_employes():
    """Liste des employés"""
    return liste_employes()

@app.route('/api/gestionnaire/employes/<int:employe_id>', methods=['GET'])
@gestionnaire_required
def api_gestionnaire_detail_employe(employe_id):
    """Détail d'un employé"""
    return detail_employe(employe_id)

@app.route('/api/gestionnaire/analytics/chatbot', methods=['GET'])
@gestionnaire_required
def api_analytics_chatbot():
    """Analytiques du chatbot"""
    return analytics_chatbot()

@app.route('/api/gestionnaire/intents', methods=['GET', 'POST'])
@gestionnaire_required
def api_gerer_intents():
    """Gestion des intentions du chatbot"""
    return gerer_intents()

# =============================================
# API Utilitaires
# =============================================

@app.route('/api/employe/profil', methods=['GET'])
@login_required
def api_profil_employe():
    """Récupère le profil de l'employé connecté"""
    try:
        employe_id = session.get('employe_id')
        
        query = """
            SELECT id, matricule, nom, prenom, email, telephone, 
                   departement, poste, date_embauche, solde_conges
            FROM employes WHERE id = %s
        """
        employe = execute_query(query, (employe_id,), fetch_one=True)
        
        if employe:
            from decimal import Decimal
            for key, value in employe.items():
                if isinstance(value, Decimal):
                    employe[key] = float(value)
                elif hasattr(value, 'isoformat'):
                    employe[key] = value.isoformat()
            return jsonify(employe)
        
        return jsonify({"error": "Employé non trouvé"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/avantages', methods=['GET'])
def api_avantages():
    """Liste des avantages sociaux"""
    try:
        query = "SELECT * FROM avantages WHERE actif = TRUE ORDER BY categorie, nom"
        avantages = execute_query(query, fetch_all=True) or []
        return jsonify({"avantages": avantages})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/test-db")
def test_db():
    """Test de la connexion PostgreSQL"""
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT version()")
        result = cur.fetchone()
        cur.close()
        db.close()
        return f"✅ Connexion PostgreSQL OK — Version : {result[0]}"
    except Exception as e:
        return f"❌ Erreur PostgreSQL : {str(e)}"

@app.route("/init-db")
def init_db():
    """Initialise la base de données"""
    try:
        from app.database.connection import init_database
        init_database()
        
        # Recharger les intentions
        from app.services.nlp_service import nlp_service
        nlp_service.reload_intents()
        
        return "✅ Base de données initialisée avec succès !"
    except Exception as e:
        return f"❌ Erreur : {str(e)}"

# =============================================
# Démarrage de l'application
# =============================================

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🤖 CHATBOT RH - FONCTION PUBLIQUE")
    print("="*50)
    print("\n📌 Routes disponibles :")
    print("   - /          → Page d'accueil")
    print("   - /login     → Connexion / Inscription")
    print("   - /chatbot   → Interface chatbot")
    print("   - /employe   → Espace employé (auth)")
    print("   - /gestionnaire → Dashboard RH (auth)")
    print("   - /test-db   → Test connexion PostgreSQL")
    print("   - /init-db   → Initialiser la base de données")
    print("\n🔐 Compte démo: admin@rh.fr / admin123")
    print("="*50 + "\n")
    
    app.run(debug=True, port=5000, host="0.0.0.0")
