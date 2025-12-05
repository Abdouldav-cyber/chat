import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

def init_database():
    conn = None
    cursor = None
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cursor = conn.cursor()

        # Création de la table employés
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS employes (
            id SERIAL PRIMARY KEY,
            nom VARCHAR(100) NOT NULL,
            prenom VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL DEFAULT 'employe',
            departement VARCHAR(100),
            poste VARCHAR(100),
            date_embauche DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Création d'un admin par défaut (mot de passe: admin123)
        admin_password = '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW'
        cursor.execute("""
        INSERT INTO employes (nom, prenom, email, password_hash, role)
        SELECT 'Admin', 'System', 'admin@rh.fr', %s, 'admin'
        WHERE NOT EXISTS (SELECT 1 FROM employes WHERE email = 'admin@rh.fr')
        """, (admin_password,))

        # Création de la table intents
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS intents (
            id SERIAL PRIMARY KEY,
            tag VARCHAR(50) UNIQUE NOT NULL,
            patterns TEXT[] NOT NULL,
            responses TEXT[] NOT NULL,
            context_set VARCHAR(50),
            context_filter VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Création de la table des conversations
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES employes(id) ON DELETE CASCADE,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            intent_tag VARCHAR(50),
            confidence FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        print("✅ Base de données initialisée avec succès !")
        print("   - Compte admin créé : admin@rh.fr / admin123")

    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la base de données : {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    init_database()