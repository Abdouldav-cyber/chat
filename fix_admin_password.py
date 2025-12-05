from werkzeug.security import generate_password_hash
from app.database.connection import get_db

def fix_admin_password():
    # Générer un hash compatible (pbkdf2:sha256) pour 'admin123'
    hashed = generate_password_hash("admin123")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE employes SET mot_de_passe = %s WHERE email = %s",
        (hashed, "admin@rh.fr")
    )
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Mot de passe admin corrigé (admin@rh.fr / admin123).")

if __name__ == "__main__":
    try:
        fix_admin_password()
        print("✅ Script exécuté avec succès.")
    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        # No need to close cur and conn here, it's already done in fix_admin_password()
        pass