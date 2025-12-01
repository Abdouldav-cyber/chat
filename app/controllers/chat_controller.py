"""
Contrôleur du Chatbot RH
Gère les requêtes de chat et les interactions avec le chatbot
"""
from flask import request, jsonify, session
from app.services.nlp_service import nlp_service
import uuid


def chat_api():
    """
    API principale du chatbot
    POST /chat
    Body: { "message": "...", "session_id": "..." (optionnel) }
    """
    try:
        data = request.get_json(force=True)
        message = data.get("message", "").strip()
        
        if not message:
            return jsonify({
                "error": "Message vide",
                "answer": "Veuillez entrer un message."
            }), 400
        
        # Récupérer ou créer un ID de session
        session_id = data.get("session_id") or str(uuid.uuid4())
        
        # Récupérer l'ID de l'employé si connecté
        employe_id = session.get("employe_id") if hasattr(session, 'get') else None
        
        # Traiter le message
        result = nlp_service.process_message(
            message=message,
            employe_id=employe_id,
            session_id=session_id
        )
        
        # Ajouter l'ID de session à la réponse
        result["session_id"] = session_id
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Erreur chat_api: {e}")
        return jsonify({
            "error": str(e),
            "answer": "Une erreur s'est produite. Veuillez réessayer.",
            "intent": "error"
        }), 500


def feedback_api():
    """
    API pour enregistrer le feedback utilisateur
    POST /chat/feedback
    Body: { "conversation_id": ..., "feedback": 1 ou -1 }
    """
    try:
        data = request.get_json(force=True)
        conversation_id = data.get("conversation_id")
        feedback = data.get("feedback")  # 1 = positif, -1 = négatif
        
        if not conversation_id or feedback not in [1, -1]:
            return jsonify({"error": "Paramètres invalides"}), 400
        
        from app.database.connection import execute_query
        query = "UPDATE conversations SET feedback = %s WHERE id = %s"
        execute_query(query, (feedback, conversation_id), commit=True)
        
        return jsonify({"success": True, "message": "Merci pour votre feedback !"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
