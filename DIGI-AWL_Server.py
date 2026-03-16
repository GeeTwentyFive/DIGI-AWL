import sys
import sqlite3
import ssl
import socket
from datetime import datetime
import threading

import bottle


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


ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(("", port))
sock.listen(1)

ssock = ssl_context.wrap_socket(
        sock,
        server_side=True
)


@bottle.hook("before_request")
def force_https():
        if bottle.request.urlparts.scheme == "http":
                bottle.redirect(bottle.request.url.replace("http://", "https://"))

@bottle.route("/")
def web_interface():
        if not bottle.request.auth or bottle.request.auth[1] != password:
                bottle.response.status = 401
                bottle.response.headers["WWW-Authenticate"] = 'Basic Realm="Login Required"'
                return
        
        return "WIP" # TODO


print("Starting DIGI-AWL Server...")

def client_loop():
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
threading.Thread(target=client_loop, daemon=True).start()

print("DIGI-AWL Server running...")

bottle.run(host="0.0.0.0", port="443", server="wsgiref", ssl=ssl_context)
