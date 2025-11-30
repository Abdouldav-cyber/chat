# Fichier helper; on utilise la table intents pour stocker rÃ©ponses
# Vous pouvez complÃ©ter ici des fonctions d'insertion/lecture supplÃ©mentaires.
from app.database.connection import get_db

def insert_intent(intent_name, answer):
    db = get_db()
    cur = db.cursor()
    cur.execute('INSERT INTO intents (intent_name, answer) VALUES (%s,%s)', (intent_name, answer))
    db.commit()
    cur.close()
    db.close()
