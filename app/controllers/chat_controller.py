from flask import request, jsonify
from app.services.nlp_service import load_models, predict_intent
from app.database.connection import get_db

VEC, MODEL = load_models()

def get_answer_from_db(intent):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT answer FROM intents WHERE intent_name=%s LIMIT 1", (intent,))
    row = cur.fetchone()
    cur.close()
    db.close()

    if row:
        return row["answer"]
    return "Désolé, je n'ai pas trouvé de réponse dans la base."

def chat_api():
    data = request.get_json(force=True)
    message = data.get("message", "")

    intent = predict_intent(message, VEC, MODEL)
    answer = get_answer_from_db(intent)

    return jsonify({
        "intent": intent,
        "answer": answer
    })
