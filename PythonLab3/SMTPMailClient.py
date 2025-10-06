# Lab 3: SMTP client (completed)
# Tested against local SMTP test servers.
from socket import *
import ssl

# ======= Config you can tweak =======
MAIL_SERVER_HOST = "127.0.0.1"   
MAIL_SERVER_PORT = 1025         
SENDER = "alice@example.com"
RECIPIENT = "bob@example.com"
SUBJECT = "Hello from raw SMTP"
BODY = "I love computer networks!"
# ====================================

msg = f"Subject: {SUBJECT}\r\nFrom: {SENDER}\r\nTo: {RECIPIENT}\r\n\r\n{BODY}\r\n"
endmsg = "\r\n.\r\n"

# Choose a mail server (e.g., Google mail server) and call it mailserver
mailserver = (MAIL_SERVER_HOST, MAIL_SERVER_PORT)  # Fill in

# Create socket called clientSocket and establish a TCP connection with mailserver
clientSocket = socket(AF_INET, SOCK_STREAM)        # Fill in
clientSocket.connect(mailserver)                   # Fill in

def recv_ok(expect_prefix="2", allow_3xx=False):
    """Receive a line from the server and print it. Return it."""
    data = clientSocket.recv(1024).decode()
    print(data, end="" if data.endswith("\n") else "\n")
    if not data:
        raise RuntimeError("No response from server.")
    code = data[:3]
    if allow_3xx and code.startswith("3"):
        return data
    if not code.startswith(expect_prefix):
        raise RuntimeError(f"Unexpected reply: {data.strip()}")
    return data

def send_line(line: str):
    print(f">>> {line.strip()}")
    clientSocket.send(line.encode())

# Greet / banner
recv = recv_ok(expect_prefix="220")

# Send HELO (or EHLO to detect STARTTLS support)
ehlo = "EHLO client.example\r\n"
send_line(ehlo)
resp = recv_ok(expect_prefix="250")

# Try to detect STARTTLS in EHLO lines (multi-line reply may include 250-STARTTLS)
if "STARTTLS" in resp.upper():
    # Some servers give multi-line 250 responses: keep reading until last line
    while resp.startswith("250-"):
        resp = clientSocket.recv(1024).decode()
        print(resp, end="" if resp.endswith("\n") else "\n")
        if "STARTTLS" in resp.upper():
            pass
        if not resp.startswith("250-"):
            break
    # Issue STARTTLS and wrap the socket
    send_line("STARTTLS\r\n")
    recv_ok(expect_prefix="220")
    context = ssl.create_default_context()
    clientSocket = context.wrap_socket(clientSocket, server_hostname=MAIL_SERVER_HOST)

    # Re-EHLO over TLS
    send_line(ehlo)
    recv_ok(expect_prefix="250")

# Send MAIL FROM command and print server response.
send_line(f"MAIL FROM:<{SENDER}>\r\n")     # Fill in
recv_ok(expect_prefix="250")               # Fill in

# Send RCPT TO command and print server response.
send_line(f"RCPT TO:<{RECIPIENT}>\r\n")    # Fill in
recv_ok(expect_prefix="250")               # Fill in

# Send DATA command and print server response.
send_line("DATA\r\n")                      # Fill in
recv_ok(expect_prefix="3", allow_3xx=True) # Fill in

# Send message data.
clientSocket.send(msg.encode())            # Fill in

# Message ends with a single period.
clientSocket.send(endmsg.encode())         # Fill in
recv_ok(expect_prefix="250")               # Fill in

# Send QUIT command and get server response.
send_line("QUIT\r\n")                      # Fill in
recv_ok(expect_prefix="221")               # Fill in

clientSocket.close()
print("SMTP session completed.")
