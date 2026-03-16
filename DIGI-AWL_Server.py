import socket
import sqlite3
from datetime import datetime


PORT = 55555
MAX_DATA_TRANSFER_LIMIT = 255
AUTH = "DIGI-AWL"


db = sqlite3.connect("attendences.sqlite", isolation_level=None)
db_cur = db.cursor()

try: db_cur.execute("SELECT * FROM attendances LIMIT 1")
except sqlite3.OperationalError:
        print("Database table 'attendances' not found; creating...")
        db_cur.execute(
                "CREATE TABLE attendances ("
                        "name varchar(255),"
                        "date_and_time datetime,"
                        "extra_data varchar(1024)"
                ")"
        )

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(("", PORT))
sock.listen(1)

print("Server running...")

try:
        while True:
                conn, _ = sock.accept()

                data = conn.recv(MAX_DATA_TRANSFER_LIMIT).decode("utf-8")
                if not data or data[:len(AUTH)] != AUTH:
                        conn.close()
                        continue

                db_cur.execute(
                        "INSERT INTO attendances VALUES ("
                                '"' + data[len(AUTH):] + '",'
                                '"' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '",'
                                '""'
                        ")"
                )

                conn.close()

except KeyboardInterrupt: exit()