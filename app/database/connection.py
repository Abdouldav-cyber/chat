"""
Connexion à la base de données PostgreSQL
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration de la base de données
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "port": os.environ.get("DB_PORT", "5432"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASS", "A RENSEIGNER "),
    "database": os.environ.get("DB_NAME", "botrh"),
}


def get_db():
    """
    Retourne une connexion à la base de données PostgreSQL
    """
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
    )


def get_db_cursor(dict_cursor=True):
    """
    Retourne une connexion et un curseur
    Args:
        dict_cursor: Si True, retourne les résultats sous forme de dictionnaire
    """
    conn = get_db()
    if dict_cursor:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    else:
        cursor = conn.cursor()
    return conn, cursor


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Exécute une requête SQL de manière sécurisée
    
    Args:
        query: La requête SQL
        params: Les paramètres de la requête (tuple ou dict)
        fetch_one: Retourne un seul résultat
        fetch_all: Retourne tous les résultats
        commit: Effectue un commit après l'exécution
    
    Returns:
        Le résultat de la requête ou None
    """
    conn, cursor = get_db_cursor()
    try:
        cursor.execute(query, params)
        
        result = None
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        
        if commit:
            conn.commit()
            # Pour les INSERT avec RETURNING, récupérer le résultat
            if result is None and "RETURNING" in query.upper():
                result = cursor.fetchone()
        
        return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def init_database():
    """
    Initialise la base de données avec les tables nécessaires
    """
    import os
    migrations_path = os.path.join(os.path.dirname(__file__), '..', '..', 'migrations.sql')
    
    if os.path.exists(migrations_path):
        # Utiliser utf-8-sig pour supprimer un éventuel BOM au début du fichier SQL
        # Cela évite l'erreur de syntaxe "sur ou près de \"\ufeff\"" lors de l'exécution
        with open(migrations_path, 'r', encoding='utf-8-sig') as f:
            sql = f.read()
        
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            conn.commit()
            print("✅ Base de données initialisée avec succès!")
        except Exception as e:
            conn.rollback()
            print(f"❌ Erreur lors de l'initialisation: {e}")
        finally:
            cursor.close()
            conn.close()
