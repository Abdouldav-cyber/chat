"""
Contrôleur pour l'interface Gestionnaire RH
Dashboard et outils de gestion
"""
from flask import request, jsonify, session
from app.database.connection import execute_query
from datetime import datetime, timedelta
from decimal import Decimal


def dashboard_stats():
    """
    Statistiques du dashboard gestionnaire
    GET /api/gestionnaire/stats
    """
    try:
        stats = {}
        
        # Demandes en attente
        query = "SELECT COUNT(*) as count FROM demandes WHERE statut = 'en_attente'"
        result = execute_query(query, fetch_one=True)
        stats['demandes_en_attente'] = result['count'] if result else 0
        
        # Demandes par type (ce mois)
        query = """
            SELECT type_demande, COUNT(*) as count 
            FROM demandes 
            WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY type_demande
        """
        result = execute_query(query, fetch_all=True) or []
        stats['demandes_par_type'] = {r['type_demande']: r['count'] for r in result}
        
        # Employés actifs
        query = "SELECT COUNT(*) as count FROM employes WHERE actif = TRUE"
        result = execute_query(query, fetch_one=True)
        stats['employes_actifs'] = result['count'] if result else 0
        
        # Échéances cette semaine
        today = datetime.now().date()
        next_week = today + timedelta(days=7)
        query = """
            SELECT COUNT(*) as count FROM echeances 
            WHERE date_echeance BETWEEN %s AND %s
        """
        result = execute_query(query, (today, next_week), fetch_one=True)
        stats['echeances_semaine'] = result['count'] if result else 0
        
        # Conversations chatbot aujourd'hui
        query = """
            SELECT COUNT(*) as count FROM conversations 
            WHERE DATE(created_at) = CURRENT_DATE
        """
        result = execute_query(query, fetch_one=True)
        stats['conversations_jour'] = result['count'] if result else 0
        
        # Taux de satisfaction (feedback positif)
        query = """
            SELECT 
                COUNT(*) FILTER (WHERE feedback = 1) as positif,
                COUNT(*) FILTER (WHERE feedback = -1) as negatif,
                COUNT(*) FILTER (WHERE feedback IS NOT NULL) as total
            FROM conversations
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        """
        result = execute_query(query, fetch_one=True)
        if result and result['total'] > 0:
            stats['satisfaction'] = round((result['positif'] / result['total']) * 100, 1)
        else:
            stats['satisfaction'] = None
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def liste_demandes_gestionnaire():
    """
    Liste toutes les demandes pour les gestionnaires
    GET /api/gestionnaire/demandes?statut=en_attente&page=1
    """
    try:
        statut = request.args.get("statut")
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 20))
        offset = (page - 1) * limit
        
        query = """
            SELECT d.*, e.nom, e.prenom, e.matricule, e.departement,
                   g.nom as gestionnaire_nom, g.prenom as gestionnaire_prenom
            FROM demandes d
            JOIN employes e ON d.employe_id = e.id
            LEFT JOIN employes g ON d.traite_par = g.id
            WHERE 1=1
        """
        params = []
        
        if statut:
            query += " AND d.statut = %s"
            params.append(statut)
        
        query += " ORDER BY d.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        demandes = execute_query(query, tuple(params), fetch_all=True) or []
        
        # Compter le total
        count_query = "SELECT COUNT(*) as total FROM demandes"
        if statut:
            count_query += " WHERE statut = %s"
            count_result = execute_query(count_query, (statut,), fetch_one=True)
        else:
            count_result = execute_query(count_query, fetch_one=True)
        
        total = count_result['total'] if count_result else 0
        
        # Convertir pour JSON
        for d in demandes:
            for key, value in d.items():
                if isinstance(value, datetime):
                    d[key] = value.isoformat()
                elif isinstance(value, Decimal):
                    d[key] = float(value)
                elif hasattr(value, 'isoformat'):
                    d[key] = value.isoformat()
        
        return jsonify({
            "demandes": demandes,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def liste_employes():
    """
    Liste des employés
    GET /api/gestionnaire/employes
    """
    try:
        search = request.args.get("search", "")
        departement = request.args.get("departement")
        
        query = """
            SELECT id, matricule, nom, prenom, email, telephone, 
                   departement, poste, date_embauche, solde_conges, role, actif
            FROM employes
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (nom ILIKE %s OR prenom ILIKE %s OR matricule ILIKE %s OR email ILIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param, search_param])
        
        if departement:
            query += " AND departement = %s"
            params.append(departement)
        
        query += " ORDER BY nom, prenom"
        
        employes = execute_query(query, tuple(params), fetch_all=True) or []
        
        # Convertir pour JSON
        for e in employes:
            for key, value in e.items():
                if isinstance(value, Decimal):
                    e[key] = float(value)
                elif hasattr(value, 'isoformat'):
                    e[key] = value.isoformat()
        
        return jsonify({"employes": employes})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def detail_employe(employe_id: int):
    """
    Détail d'un employé avec son historique
    GET /api/gestionnaire/employes/<id>
    """
    try:
        # Infos employé
        query = "SELECT * FROM employes WHERE id = %s"
        employe = execute_query(query, (employe_id,), fetch_one=True)
        
        if not employe:
            return jsonify({"error": "Employé non trouvé"}), 404
        
        # Demandes récentes
        query = """
            SELECT type_demande, sous_type, date_debut, date_fin, statut, created_at
            FROM demandes 
            WHERE employe_id = %s 
            ORDER BY created_at DESC LIMIT 10
        """
        demandes = execute_query(query, (employe_id,), fetch_all=True) or []
        
        # Avantages
        query = """
            SELECT a.nom, a.description, ea.date_attribution
            FROM employes_avantages ea
            JOIN avantages a ON ea.avantage_id = a.id
            WHERE ea.employe_id = %s AND ea.actif = TRUE
        """
        avantages = execute_query(query, (employe_id,), fetch_all=True) or []
        
        # Échéances
        query = """
            SELECT type_echeance, date_echeance, description
            FROM echeances
            WHERE employe_id = %s AND date_echeance >= CURRENT_DATE
            ORDER BY date_echeance ASC LIMIT 5
        """
        echeances = execute_query(query, (employe_id,), fetch_all=True) or []
        
        # Convertir pour JSON
        for key, value in employe.items():
            if isinstance(value, Decimal):
                employe[key] = float(value)
            elif hasattr(value, 'isoformat'):
                employe[key] = value.isoformat()
        
        # Supprimer le mot de passe de la réponse
        employe.pop('mot_de_passe', None)
        
        return jsonify({
            "employe": employe,
            "demandes_recentes": demandes,
            "avantages": avantages,
            "echeances": echeances
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def analytics_chatbot():
    """
    Analytiques du chatbot pour les gestionnaires
    GET /api/gestionnaire/analytics/chatbot
    """
    try:
        analytics = {}
        
        # Intentions les plus fréquentes
        query = """
            SELECT intent_detecte, COUNT(*) as count
            FROM conversations
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            AND intent_detecte IS NOT NULL
            GROUP BY intent_detecte
            ORDER BY count DESC
            LIMIT 10
        """
        result = execute_query(query, fetch_all=True) or []
        analytics['top_intents'] = result
        
        # Conversations par jour (7 derniers jours)
        query = """
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM conversations
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        result = execute_query(query, fetch_all=True) or []
        analytics['conversations_par_jour'] = [
            {"date": r['date'].isoformat(), "count": r['count']} for r in result
        ]
        
        # Questions sans réponse (unknown intent)
        query = """
            SELECT message_utilisateur, COUNT(*) as count
            FROM conversations
            WHERE intent_detecte = 'unknown'
            AND created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY message_utilisateur
            ORDER BY count DESC
            LIMIT 10
        """
        result = execute_query(query, fetch_all=True) or []
        analytics['questions_non_comprises'] = result
        
        # Score de confiance moyen
        query = """
            SELECT AVG(score_confiance) as avg_confidence
            FROM conversations
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            AND score_confiance IS NOT NULL
        """
        result = execute_query(query, fetch_one=True)
        analytics['confiance_moyenne'] = round(float(result['avg_confidence']) * 100, 1) if result and result['avg_confidence'] else None
        
        return jsonify(analytics)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def gerer_intents():
    """
    Gérer les intentions du chatbot
    GET/POST /api/gestionnaire/intents
    """
    if request.method == 'GET':
        try:
            query = """
                SELECT id, intent_name, categorie, reponse, mots_cles, priorite, actif
                FROM intents
                ORDER BY categorie, priorite DESC
            """
            intents = execute_query(query, fetch_all=True) or []
            return jsonify({"intents": intents})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json(force=True)
            
            intent_name = data.get("intent_name")
            categorie = data.get("categorie")
            reponse = data.get("reponse")
            mots_cles = data.get("mots_cles", [])
            priorite = data.get("priorite", 5)
            
            if not all([intent_name, reponse]):
                return jsonify({"error": "Nom et réponse requis"}), 400
            
            query = """
                INSERT INTO intents (intent_name, categorie, reponse, mots_cles, priorite)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (intent_name) DO UPDATE SET
                    categorie = EXCLUDED.categorie,
                    reponse = EXCLUDED.reponse,
                    mots_cles = EXCLUDED.mots_cles,
                    priorite = EXCLUDED.priorite
                RETURNING id
            """
            result = execute_query(
                query,
                (intent_name, categorie, reponse, mots_cles, priorite),
                fetch_one=True,
                commit=True
            )
            
            # Recharger les intents dans le service NLP
            from app.services.nlp_service import nlp_service
            nlp_service.reload_intents()
            
            return jsonify({
                "success": True,
                "intent_id": result['id'] if result else None
            })
        
        except Exception as e:
            return jsonify({"error": str(e)}), 500


