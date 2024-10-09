
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="hostinger_database_host",
        user="your_username",
        password="your_password",
        database="doctor_management"
    )
