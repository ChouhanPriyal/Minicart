import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Pr@290105",
    database="ecommerce"
)

cursor = db.cursor(dictionary=True, buffered=True)