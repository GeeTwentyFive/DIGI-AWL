import sys
import sqlite3
import ssl
import socket
from datetime import datetime


DEFAULT_PORT = 55555
DEFAULT_PASSWORD = "DIGI-AWL"
MAX_NAME_LENGTH = 255


print("CLI Usage: [PASSWORD] [PORT]")

password = (sys.argv[1]) if (len(sys.argv) >= 2) else DEFAULT_PASSWORD
port = (sys.argv[2]) if (len(sys.argv) >= 3) else DEFAULT_PORT
max_data_transfer_limit = len(password) + MAX_NAME_LENGTH


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
sock.bind(("", port))
sock.listen(1)

ssock = ssl.create_default_context(
        purpose=ssl.Purpose.CLIENT_AUTH
).wrap_socket(
        sock,
        server_side=True
)


print("Server running...")

try:
        while True:
                conn, _ = ssock.accept()

                data = conn.recv(max_data_transfer_limit).decode("utf-8")
                if not data or data[:len(password)] != password:
                        conn.close()
                        continue

                db_cur.execute(
                        "INSERT INTO attendances VALUES ("
                                '"' + data[len(password):] + '",'
                                '"' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '",'
                                '""'
                        ")"
                )

                conn.close()

except KeyboardInterrupt: exit()