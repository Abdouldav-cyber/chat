"""
Contrôleur d'authentification
Gère la connexion, inscription et gestion de session des utilisateurs
"""
from flask import request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from app.database.connection import execute_query
from functools import wraps
import re


def login_required(f):
    """Décorateur pour protéger les routes nécessitant une authentification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'employe_id' not in session:
            if request.is_json:
                return jsonify({"error": "Non authentifié", "redirect": "/login"}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


def gestionnaire_required(f):
    """Décorateur pour les routes réservées aux gestionnaires RH"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'employe_id' not in session:
            if request.is_json:
                return jsonify({"error": "Non authentifié"}), 401
            return redirect(url_for('login_page'))
        
        if session.get('role') not in ['gestionnaire', 'admin']:
            if request.is_json:
                return jsonify({"error": "Accès refusé - Gestionnaire requis"}), 403
            return redirect(url_for('home'))
        
        return f(*args, **kwargs)
    return decorated_function


def login():
    """
    Authentification d'un utilisateur
    POST /api/auth/login
    Body: { "email": "...", "password": "..." }
    """
    try:
        data = request.get_json(force=True)
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        if not email or not password:
            return jsonify({"error": "Email et mot de passe requis"}), 400
        
        # Rechercher l'utilisateur
        query = """
            SELECT id, matricule, nom, prenom, email, mot_de_passe, role, actif, 
                   departement, poste, solde_conges
            FROM employes 
            WHERE LOWER(email) = %s
        """
        user = execute_query(query, (email,), fetch_one=True)
        
        if not user:
            return jsonify({"error": "Email ou mot de passe incorrect"}), 401
        
        if not user.get('actif', True):
            return jsonify({"error": "Compte désactivé. Contactez le service RH."}), 401
        
        # Vérifier le mot de passe
        if not user.get('mot_de_passe'):
            return jsonify({"error": "Compte non configuré. Contactez le service RH."}), 401
        
        if not check_password_hash(user['mot_de_passe'], password):
            return jsonify({"error": "Email ou mot de passe incorrect"}), 401
        
        # Créer la session
        session['employe_id'] = user['id']
        session['matricule'] = user['matricule']
        session['nom'] = user['nom']
        session['prenom'] = user['prenom']
        session['email'] = user['email']
        session['role'] = user['role']
        session['departement'] = user['departement']
        session.permanent = True
        
        # Déterminer la redirection
        redirect_url = "/gestionnaire" if user['role'] in ['gestionnaire', 'admin'] else "/employe"
        
        return jsonify({
            "success": True,
            "message": f"Bienvenue {user['prenom']} !",
            "user": {
                "id": user['id'],
                "nom": user['nom'],
                "prenom": user['prenom'],
                "email": user['email'],
                "role": user['role'],
                "departement": user['departement']
            },
            "redirect": redirect_url
        })
    
    except Exception as e:
        print(f"Erreur login: {e}")
        return jsonify({"error": "Erreur de connexion"}), 500


def register():
    """
    Inscription d'un nouvel utilisateur
    POST /api/auth/register
    """
    try:
        data = request.get_json(force=True)
        
        matricule = data.get("matricule", "").strip().upper()
        nom = data.get("nom", "").strip()
        prenom = data.get("prenom", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        telephone = data.get("telephone", "").strip()
        departement = data.get("departement", "").strip()
        
        # Validations
        if not all([matricule, nom, prenom, email, password]):
            return jsonify({"error": "Tous les champs obligatoires doivent être remplis"}), 400
        
        if len(password) < 6:
            return jsonify({"error": "Le mot de passe doit contenir au moins 6 caractères"}), 400
        
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            return jsonify({"error": "Format d'email invalide"}), 400
        
        # Vérifier si l'email existe déjà
        check_query = "SELECT id FROM employes WHERE LOWER(email) = %s OR matricule = %s"
        existing = execute_query(check_query, (email, matricule), fetch_one=True)
        
        if existing:
            return jsonify({"error": "Un compte existe déjà avec cet email ou ce matricule"}), 400
        
        # Hasher le mot de passe
        hashed_password = generate_password_hash(password)
        
        # Créer l'utilisateur
        insert_query = """
            INSERT INTO employes (matricule, nom, prenom, email, mot_de_passe, telephone, departement, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'employe')
            RETURNING id
        """
        result = execute_query(
            insert_query,
            (matricule, nom, prenom, email, hashed_password, telephone, departement),
            fetch_one=True,
            commit=True
        )
        
        if result:
            return jsonify({
                "success": True,
                "message": "Compte créé avec succès ! Vous pouvez maintenant vous connecter."
            })
        
        return jsonify({"error": "Erreur lors de la création du compte"}), 500
    
    except Exception as e:
        print(f"Erreur register: {e}")
        return jsonify({"error": str(e)}), 500


def logout():
    """
    Déconnexion de l'utilisateur
    POST /api/auth/logout
    """
    session.clear()
    return jsonify({"success": True, "message": "Déconnexion réussie", "redirect": "/login"})


def get_current_user():
    """
    Récupère les informations de l'utilisateur connecté
    GET /api/auth/me
    """
    if 'employe_id' not in session:
        return jsonify({"authenticated": False}), 401
    
    try:
        query = """
            SELECT id, matricule, nom, prenom, email, role, departement, poste, solde_conges
            FROM employes WHERE id = %s
        """
        user = execute_query(query, (session['employe_id'],), fetch_one=True)
        
        if user:
            from decimal import Decimal
            for key, value in user.items():
                if isinstance(value, Decimal):
                    user[key] = float(value)
            
            return jsonify({
                "authenticated": True,
                "user": user
            })
        
        session.clear()
        return jsonify({"authenticated": False}), 401
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def change_password():
    """
    Changer le mot de passe
    POST /api/auth/change-password
    """
    if 'employe_id' not in session:
        return jsonify({"error": "Non authentifié"}), 401
    
    try:
        data = request.get_json(force=True)
        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")
        
        if not current_password or not new_password:
            return jsonify({"error": "Mot de passe actuel et nouveau requis"}), 400
        
        if len(new_password) < 6:
            return jsonify({"error": "Le nouveau mot de passe doit contenir au moins 6 caractères"}), 400
        
        # Vérifier le mot de passe actuel
        query = "SELECT mot_de_passe FROM employes WHERE id = %s"
        user = execute_query(query, (session['employe_id'],), fetch_one=True)
        
        if not check_password_hash(user['mot_de_passe'], current_password):
            return jsonify({"error": "Mot de passe actuel incorrect"}), 400
        
        # Mettre à jour le mot de passe
        hashed = generate_password_hash(new_password)
        update_query = "UPDATE employes SET mot_de_passe = %s WHERE id = %s"
        execute_query(update_query, (hashed, session['employe_id']), commit=True)
        
        return jsonify({"success": True, "message": "Mot de passe modifié avec succès"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


