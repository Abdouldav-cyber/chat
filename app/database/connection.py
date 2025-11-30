import mysql.connector
import os

def get_db():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASS", ""),  
        database=os.environ.get("DB_NAME", "botrh"),
        charset="utf8mb4"
    )
