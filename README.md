# RH Chatbot - Scaffold automatique

ExÃ©cution rapide:
1. CrÃ©er et activer venv: py -3.10 -m venv .venv puis .\.venv\Scripts\Activate.ps1
2. Installer dÃ©pendances: pip install -r requirements.txt
3. PrÃ©parer la BDD MySQL (voir migrations.sql)
4. Lancer l'entraÃ®nement: python services/training.py
5. Lancer l'app: python app.py

N'oubliez pas de configurer vos variables d'environnement DB (DB_USER, DB_PASS, DB_NAME).
