import psycopg2
from dotenv import load_dotenv
import os

# Charger les variables d'environnement (.env)
load_dotenv()

def drop_intents():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    # On supprime les tables qui ont un schéma incompatible avec migrations.sql
    # 1) Table des intentions du chatbot
    cur.execute("DROP TABLE IF EXISTS intents CASCADE;")

    # 2) Table des employés (sera recréée avec colonnes matricule, solde_conges, etc.)
    cur.execute("DROP TABLE IF EXISTS employes CASCADE;")

    # 3) Table des conversations (sera recréée avec colonne session_id, etc.)
    cur.execute("DROP TABLE IF EXISTS conversations CASCADE;")

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Tables 'intents', 'employes' et 'conversations' supprimées.")

if __name__ == "__main__":
    drop_intents()