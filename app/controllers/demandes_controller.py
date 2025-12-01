"""
Contrôleur des demandes RH
Gère les demandes de congés, remboursements, attestations, etc.
"""
from flask import request, jsonify, session
from app.database.connection import execute_query
from datetime import datetime, timedelta
from decimal import Decimal


def creer_demande():
    """
    Créer une nouvelle demande
    POST /api/demandes
    """
    try:
        data = request.get_json(force=True)
        
        employe_id = data.get("employe_id") or session.get("employe_id")
        if not employe_id:
            return jsonify({"error": "Employé non identifié"}), 401
        
        type_demande = data.get("type_demande")  # conge, remboursement, attestation
        sous_type = data.get("sous_type")  # conge_annuel, remboursement_transport, etc.
        date_debut = data.get("date_debut")
        date_fin = data.get("date_fin")
        montant = data.get("montant")
        motif = data.get("motif", "")
        
        if not type_demande:
            return jsonify({"error": "Type de demande requis"}), 400
        
        # Calcul du nombre de jours pour les congés
        nb_jours = None
        if type_demande == "conge" and date_debut and date_fin:
            d1 = datetime.strptime(date_debut, "%Y-%m-%d")
            d2 = datetime.strptime(date_fin, "%Y-%m-%d")
            nb_jours = (d2 - d1).days + 1
            
            # Vérifier le solde de congés
            solde = get_solde_conges(employe_id)
            if solde is not None and nb_jours > solde:
                return jsonify({
                    "error": f"Solde insuffisant. Vous avez {solde} jours disponibles."
                }), 400
        
        query = """
            INSERT INTO demandes 
            (employe_id, type_demande, sous_type, date_debut, date_fin, nb_jours, montant, motif)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
        """
        result = execute_query(
            query,
            (employe_id, type_demande, sous_type, date_debut, date_fin, nb_jours, montant, motif),
            fetch_one=True,
            commit=True
        )
        
        # Créer une notification pour les gestionnaires RH
        creer_notification_gestionnaires(
            titre=f"Nouvelle demande de {type_demande}",
            message=f"Une nouvelle demande de {type_demande} a été soumise et attend votre validation.",
            type_notification="demande"
        )
        
        return jsonify({
            "success": True,
            "message": "Demande créée avec succès",
            "demande_id": result['id'] if result else None,
            "statut": "en_attente"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_solde_conges(employe_id: int):
    """Récupère le solde de congés d'un employé"""
    query = "SELECT solde_conges FROM employes WHERE id = %s"
    result = execute_query(query, (employe_id,), fetch_one=True)
    return float(result['solde_conges']) if result else None


def liste_demandes():
    """
    Liste les demandes d'un employé
    GET /api/demandes?employe_id=X&statut=Y
    """
    try:
        employe_id = request.args.get("employe_id") or session.get("employe_id")
        statut = request.args.get("statut")
        
        query = """
            SELECT d.*, e.nom, e.prenom 
            FROM demandes d
            JOIN employes e ON d.employe_id = e.id
            WHERE 1=1
        """
        params = []
        
        if employe_id:
            query += " AND d.employe_id = %s"
            params.append(employe_id)
        
        if statut:
            query += " AND d.statut = %s"
            params.append(statut)
        
        query += " ORDER BY d.created_at DESC"
        
        demandes = execute_query(query, tuple(params), fetch_all=True) or []
        
        # Convertir les dates et Decimal pour JSON
        for d in demandes:
            for key, value in d.items():
                if isinstance(value, datetime):
                    d[key] = value.isoformat()
                elif isinstance(value, Decimal):
                    d[key] = float(value)
        
        return jsonify({"demandes": demandes})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def traiter_demande():
    """
    Traiter une demande (approuver/refuser)
    PUT /api/demandes/<id>/traiter
    """
    try:
        data = request.get_json(force=True)
        demande_id = data.get("demande_id")
        action = data.get("action")  # approuver, refuser
        commentaire = data.get("commentaire", "")
        gestionnaire_id = data.get("gestionnaire_id") or session.get("employe_id")
        
        if action not in ["approuver", "refuser"]:
            return jsonify({"error": "Action invalide"}), 400
        
        nouveau_statut = "approuve" if action == "approuver" else "refuse"
        
        # Mettre à jour la demande
        query = """
            UPDATE demandes 
            SET statut = %s, commentaire_gestionnaire = %s, 
                traite_par = %s, date_traitement = NOW(), updated_at = NOW()
            WHERE id = %s
            RETURNING employe_id, type_demande, nb_jours
        """
        result = execute_query(
            query,
            (nouveau_statut, commentaire, gestionnaire_id, demande_id),
            fetch_one=True,
            commit=True
        )
        
        if result:
            # Si congé approuvé, déduire du solde
            if action == "approuver" and result['type_demande'] == "conge" and result['nb_jours']:
                update_solde = """
                    UPDATE employes 
                    SET solde_conges = solde_conges - %s 
                    WHERE id = %s
                """
                execute_query(update_solde, (result['nb_jours'], result['employe_id']), commit=True)
            
            # Notifier l'employé
            statut_texte = "approuvée" if action == "approuver" else "refusée"
            creer_notification(
                employe_id=result['employe_id'],
                titre=f"Demande {statut_texte}",
                message=f"Votre demande de {result['type_demande']} a été {statut_texte}. {commentaire}",
                type_notification="demande"
            )
        
        return jsonify({
            "success": True,
            "message": f"Demande {nouveau_statut}e avec succès"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def annuler_demande():
    """
    Annuler une demande en attente
    PUT /api/demandes/<id>/annuler
    """
    try:
        data = request.get_json(force=True)
        demande_id = data.get("demande_id")
        employe_id = data.get("employe_id") or session.get("employe_id")
        
        # Vérifier que la demande appartient à l'employé et est en attente
        query = """
            UPDATE demandes 
            SET statut = 'annule', updated_at = NOW()
            WHERE id = %s AND employe_id = %s AND statut = 'en_attente'
            RETURNING id
        """
        result = execute_query(query, (demande_id, employe_id), fetch_one=True, commit=True)
        
        if result:
            return jsonify({"success": True, "message": "Demande annulée"})
        else:
            return jsonify({"error": "Impossible d'annuler cette demande"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def creer_notification(employe_id: int, titre: str, message: str, type_notification: str = "info"):
    """Crée une notification pour un employé"""
    query = """
        INSERT INTO notifications (employe_id, titre, message, type_notification)
        VALUES (%s, %s, %s, %s)
    """
    execute_query(query, (employe_id, titre, message, type_notification), commit=True)


def creer_notification_gestionnaires(titre: str, message: str, type_notification: str = "info"):
    """Crée une notification pour tous les gestionnaires RH"""
    query = """
        INSERT INTO notifications (employe_id, titre, message, type_notification)
        SELECT id, %s, %s, %s FROM employes WHERE role IN ('gestionnaire', 'admin')
    """
    execute_query(query, (titre, message, type_notification), commit=True)


