
import psycopg2
from datetime import datetime, timedelta 


conn = psycopg2.connect(
        host="34.72.244.217",
        database="postgres", 
        user="postgres", 
        password="tKJ6uSBpwvMy")
conn.autocommit=True


conn.close()
curr.close()

