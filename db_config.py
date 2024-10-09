
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="srv1672.hstgr.io",
        user="u953503039_root",
        password="Radblox!1",
        database="u953503039_radschedule"
    )
