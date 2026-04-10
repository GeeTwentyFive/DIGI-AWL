import sys
import sqlite3
import ssl
import socket
from datetime import datetime
import threading

import bottle


MAX_TAG_CAPACITY = 255
DEFAULT_PORT = 55555
DEFAULT_WEB_PASSWORD = "DIGI-AWL"

CIPHER_OFFSET = -30
INTEGRITY_CHECK_STRING = "DAL_"


print("Usage: [SERVER_PORT] [WEB_INTERFACE_PASSWORD]")

port = (sys.argv[1]) if (len(sys.argv) >= 2) else DEFAULT_PORT
web_password = (sys.argv[2]) if (len(sys.argv) >= 3) else DEFAULT_WEB_PASSWORD


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
        if not bottle.request.auth or bottle.request.auth[1] != web_password:
                bottle.response.status = 401
                bottle.response.headers["WWW-Authenticate"] = 'Basic Realm="Login Required"'
                return
        
        html = (
                '<form method="post" action="/add" style="text-align: center;">'
                '<label for="name">Name:</label><br>'
                '<input id="name" name="name"><br>'
                '<br>'
                '<label for="date_and_time">Date and time:</label><br>'
                '<input id="date_and_time" type="datetime-local" name="date_and_time"><br>'
                '<br>'
                '<label for="extra_data">Extra info:</label><br>'
                '<textarea id="extra_data" name="extra_data"></textarea><br>'
                '<br>'
                '<input type="submit">'
                '</form>'

                '<br><br>'

                '<style>'
                'table {width: 100%; border-collapse: collapse;}'
                'td, th {border: 1px solid #dddddd; text-align: left; padding: 8px;}'
                '</style>'

                '<table>'
                '<tr>'
                '<th>' 'Name' '</th>'
                '<th>' 'Date and time' '</th>'
                '<th>' 'Extra info' '</th>'
                '<th>' '' '</th>'
                '</tr>'
        )

        for attendance in db_cur.execute("SELECT * FROM attendances ORDER BY date_and_time DESC").fetchall():
                html += '<tr>'
                html += '<td>' + attendance[0] + '</td>'
                html += '<td>' + attendance[1] + '</td>'
                html += '<td style="word-wrap: break-word; overflow-wrap: break-word; word-break: break-word;">' + attendance[2] + '</td>'

                html += '<td><form method="post" action="/delete" style="text-align: center;">'
                html += f'<input name="name" value="{attendance[0]}" type="hidden">'
                html += f'<input name="date_and_time" value="{attendance[1]}" type="hidden">'
                html += f'<input name="extra_data" value="{attendance[2]}" type="hidden">'
                html += '<input type="submit" value="Delete">'
                html += '</form></td>'

                html += '</tr>'
        
        return html

@bottle.post("/add")
def web_handle_add():
        if not bottle.request.forms.name:
                return "ERROR: name not provided"
        elif not bottle.request.forms.date_and_time:
                return "ERROR: date and time not provided"
        else:
                db_cur.execute(
                        "INSERT INTO attendances VALUES ("
                                '"' + bottle.request.forms.name + '",'
                                '"' + datetime.strptime(bottle.request.forms.date_and_time, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S") + '",'
                                '"' + bottle.request.forms.extra_data + '"'
                        ")"
                )
                return bottle.redirect("/")

@bottle.post("/delete")
def web_handle_delete():
        db_cur.execute(
                "DELETE FROM attendances WHERE "
                        'name="' + bottle.request.forms.name + '" AND '
                        'date_and_time="' + bottle.request.forms.date_and_time + '" AND '
                        'extra_data="' + bottle.request.forms.extra_data + '"'
        )
        return bottle.redirect("/")


print("Starting DIGI-AWL Server...")

def client_loop():
        while True:
                conn, _ = ssock.accept()

                received_data = conn.recv(MAX_TAG_CAPACITY)
                if not received_data:
                        conn.close()
                        continue

                deciphered_received_data = ""
                for c in received_data:
                        deciphered_received_data += chr(ord(c) - CIPHER_OFFSET)
                
                if (deciphered_received_data[:len(INTEGRITY_CHECK_STRING)] != INTEGRITY_CHECK_STRING):
                        print("Received invalid data from " + str(conn.getpeername()))
                        continue

                db_cur.execute(
                        "INSERT INTO attendances VALUES ("
                                '"' + deciphered_received_data + '",'
                                '"' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '",'
                                '""'
                        ")"
                )

                conn.close()
threading.Thread(target=client_loop, daemon=True).start()

print("DIGI-AWL Server running...")

bottle.run(host="0.0.0.0", port="443", server="wsgiref", ssl=ssl_context)
