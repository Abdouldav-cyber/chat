"""
Contrôleur des notifications RH
Gère les notifications et les échéances
"""
from flask import request, jsonify, session
from app.database.connection import execute_query
from datetime import datetime, timedelta
from decimal import Decimal


def get_notifications():
    """
    Récupère les notifications d'un employé
    GET /api/notifications?employe_id=X&non_lues=true
    """
    try:
        employe_id = request.args.get("employe_id") or session.get("employe_id")
        non_lues_only = request.args.get("non_lues", "false").lower() == "true"
        
        if not employe_id:
            return jsonify({"error": "Employé non identifié"}), 401
        
        query = """
            SELECT id, titre, message, type_notification, lue, created_at
            FROM notifications
            WHERE employe_id = %s
        """
        params = [employe_id]
        
        if non_lues_only:
            query += " AND lue = FALSE"
        
        query += " ORDER BY created_at DESC LIMIT 50"
        
        notifications = execute_query(query, tuple(params), fetch_all=True) or []
        
        # Convertir les dates pour JSON
        for n in notifications:
            if isinstance(n.get('created_at'), datetime):
                n['created_at'] = n['created_at'].isoformat()
        
        # Compter les non lues
        count_query = "SELECT COUNT(*) as count FROM notifications WHERE employe_id = %s AND lue = FALSE"
        count_result = execute_query(count_query, (employe_id,), fetch_one=True)
        non_lues_count = count_result['count'] if count_result else 0
        
        return jsonify({
            "notifications": notifications,
            "non_lues_count": non_lues_count
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def marquer_lue():
    """
    Marquer une notification comme lue
    PUT /api/notifications/<id>/lue
    """
    try:
        data = request.get_json(force=True)
        notification_id = data.get("notification_id")
        employe_id = data.get("employe_id") or session.get("employe_id")
        
        query = """
            UPDATE notifications 
            SET lue = TRUE 
            WHERE id = %s AND employe_id = %s
        """
        execute_query(query, (notification_id, employe_id), commit=True)
        
        return jsonify({"success": True})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def marquer_toutes_lues():
    """
    Marquer toutes les notifications comme lues
    PUT /api/notifications/lire-tout
    """
    try:
        data = request.get_json(force=True)
        employe_id = data.get("employe_id") or session.get("employe_id")
        
        query = "UPDATE notifications SET lue = TRUE WHERE employe_id = %s AND lue = FALSE"
        execute_query(query, (employe_id,), commit=True)
        
        return jsonify({"success": True, "message": "Toutes les notifications ont été marquées comme lues"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def verifier_echeances():
    """
    Vérifie les échéances et crée des notifications
    Cette fonction devrait être appelée périodiquement (cron job)
    """
    try:
        today = datetime.now().date()
        
        # Trouver les échéances à venir non notifiées
        query = """
            SELECT e.*, emp.nom, emp.prenom, emp.email
            FROM echeances e
            JOIN employes emp ON e.employe_id = emp.id
            WHERE e.notification_envoyee = FALSE
            AND e.date_echeance <= %s
        """
        
        # Échéances dans les 7 prochains jours
        date_limite = today + timedelta(days=7)
        echeances = execute_query(query, (date_limite,), fetch_all=True) or []
        
        notifications_creees = 0
        
        for ech in echeances:
            jours_restants = (ech['date_echeance'] - today).days
            
            if jours_restants <= ech.get('jours_avant_notification', 7):
                # Créer la notification
                titre = f"Échéance RH : {ech['type_echeance']}"
                if jours_restants == 0:
                    message = f"L'échéance '{ech['type_echeance']}' est aujourd'hui !"
                elif jours_restants < 0:
                    message = f"L'échéance '{ech['type_echeance']}' est dépassée de {abs(jours_restants)} jour(s)."
                else:
                    message = f"L'échéance '{ech['type_echeance']}' est dans {jours_restants} jour(s). {ech.get('description', '')}"
                
                # Insérer la notification
                insert_query = """
                    INSERT INTO notifications (employe_id, titre, message, type_notification)
                    VALUES (%s, %s, %s, 'echeance')
                """
                execute_query(insert_query, (ech['employe_id'], titre, message), commit=True)
                
                # Marquer l'échéance comme notifiée
                update_query = "UPDATE echeances SET notification_envoyee = TRUE WHERE id = %s"
                execute_query(update_query, (ech['id'],), commit=True)
                
                notifications_creees += 1
        
        return jsonify({
            "success": True,
            "notifications_creees": notifications_creees
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def creer_echeance():
    """
    Créer une nouvelle échéance RH
    POST /api/echeances
    """
    try:
        data = request.get_json(force=True)
        
        employe_id = data.get("employe_id")
        type_echeance = data.get("type_echeance")
        date_echeance = data.get("date_echeance")
        description = data.get("description", "")
        jours_avant = data.get("jours_avant_notification", 7)
        
        if not all([employe_id, type_echeance, date_echeance]):
            return jsonify({"error": "Paramètres manquants"}), 400
        
        query = """
            INSERT INTO echeances 
            (employe_id, type_echeance, date_echeance, description, jours_avant_notification)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        result = execute_query(
            query,
            (employe_id, type_echeance, date_echeance, description, jours_avant),
            fetch_one=True,
            commit=True
        )
        
        return jsonify({
            "success": True,
            "echeance_id": result['id'] if result else None
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def liste_echeances():
    """
    Liste les échéances
    GET /api/echeances?employe_id=X&periode=30
    """
    try:
        employe_id = request.args.get("employe_id")
        periode_jours = int(request.args.get("periode", 30))
        
        today = datetime.now().date()
        date_limite = today + timedelta(days=periode_jours)
        
        query = """
            SELECT e.*, emp.nom, emp.prenom
            FROM echeances e
            JOIN employes emp ON e.employe_id = emp.id
            WHERE e.date_echeance BETWEEN %s AND %s
        """
        params = [today, date_limite]
        
        if employe_id:
            query += " AND e.employe_id = %s"
            params.append(employe_id)
        
        query += " ORDER BY e.date_echeance ASC"
        
        echeances = execute_query(query, tuple(params), fetch_all=True) or []
        
        # Convertir les dates pour JSON
        for e in echeances:
            for key, value in e.items():
                if isinstance(value, (datetime,)):
                    e[key] = value.isoformat()
                elif hasattr(value, 'isoformat'):
                    e[key] = value.isoformat()
        
        return jsonify({"echeances": echeances})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


