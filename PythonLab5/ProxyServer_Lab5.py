
from socket import *
import sys
import os

# Default listening port (change if your lab specifies a different one)
LISTEN_PORT = 8888

def safe_name(path):
    # convert a URL-like path into a filesystem-safe cache filename
    return path.strip('/').replace('/', '_') or 'index.html'

def main():
    if len(sys.argv) > 1:
        host_ip = sys.argv[1]
    else:
        host_ip = ''  # bind to all interfaces

    # Create a server socket, bind it to a port and start listening
    # Fill in start
    tcpSerSock = socket(AF_INET, SOCK_STREAM)
    tcpSerSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    tcpSerSock.bind((host_ip, LISTEN_PORT))
    tcpSerSock.listen(5)
    # Fill in end

    while True:
        # Start receiving data from the client
        print('Ready to serve...')
        # Fill in start
        tcpCliSock, addr = tcpSerSock.accept()
        # Fill in end
        print('Received a connection from:', addr)

        # Fill in start
        message = tcpCliSock.recv(4096)
        # Fill in end

        if not message:
            tcpCliSock.close()
            continue

        try:
            # Extract the requested path from the request line
            # e.g., b"GET /www.example.com/path HTTP/1.1"
            first_line = message.split(b'\r\n', 1)[0].decode('iso-8859-1')
            parts = first_line.split()
            if len(parts) < 2 or parts[0].upper() != 'GET':
                tcpCliSock.sendall(b"HTTP/1.0 400 Bad Request\r\nConnection: close\r\n\r\n")
                tcpCliSock.close()
                continue
            initial = parts[1]  # "/www.example.com/path"
        except Exception as e:
            tcpCliSock.sendall(b"HTTP/1.0 400 Bad Request\r\nConnection: close\r\n\r\n")
            tcpCliSock.close()
            continue

        # The lab skeleton usually does: filename = message.split()[1].partition("/")[2]
        # which strips the leading "/"
        # Fill in start
        filename = initial.partition("/")[2]  # drop leading "/"
        filetouse = "/" + filename
        # Fill in end
        print('Requested:', filetouse)

        fileExist = "false"
        cache_file = safe_name(filetouse)  # body-only cache

        try:
            # Check whether the file exists in the cache
            # Fill in start
            f = open(cache_file, "rb")
            outputdata = f.read()
            f.close()
            fileExist = "true"
            # Fill in end

            # Proxy finds a cache hit and generates a response message
            # Fill in start
            tcpCliSock.sendall(b"HTTP/1.0 200 OK\r\n")
            tcpCliSock.sendall(b"Content-Length: " + str(len(outputdata)).encode('ascii') + b"\r\n")
            tcpCliSock.sendall(b"Connection: close\r\n")
            tcpCliSock.sendall(b"\r\n")
            tcpCliSock.sendall(outputdata)
            # Fill in end
            print('Read from cache:', cache_file)

        except IOError:
            if fileExist == "false":
                # Create a socket on the proxy server to contact the origin
                # Fill in start
                c = socket(AF_INET, SOCK_STREAM)
                # Fill in end

                # The classic skeleton strips "www." once; keep that behavior
                # and also parse path if present
                if '/' in filename:
                    hostpart, pathpart = filename.split('/', 1)
                    path = '/' + pathpart
                else:
                    hostpart = filename
                    path = '/'

                hostn = hostpart.replace("www.", "", 1)
                try:
                    # Connect to the origin server at port 80
                    # Fill in start
                    c.connect((hostn, 80))
                    # Send a minimal HTTP/1.0 GET to the origin
                    req = ("GET " + path + " HTTP/1.0\r\nHost: " + hostpart + "\r\nConnection: close\r\n\r\n")
                    c.sendall(req.encode('iso-8859-1'))
                    # Receive the full origin response
                    response = b""
                    while True:
                        data = c.recv(4096)
                        if not data:
                            break
                        response += data
                    # Fill in end

                    # Split headers/body (body goes to cache, full response goes to client)
                    sep = b"\r\n\r\n"
                    body = b""
                    if sep in response:
                        _, body = response.split(sep, 1)

                    # Write body to cache (body-only as per classic lab)
                    # Fill in start
                    with open(cache_file, "wb") as tmpFile:
                        tmpFile.write(body)
                    # Fill in end

                    # Forward full origin response back to the client
                    # Fill in start
                    tcpCliSock.sendall(response)
                    # Fill in end

                except Exception as e:
                    print("Origin fetch failed:", e)
                    # Fill in start
                    tcpCliSock.sendall(b"HTTP/1.0 502 Bad Gateway\r\nConnection: close\r\n\r\n")
                    # Fill in end
                finally:
                    # Fill in start
                    c.close()
                    # Fill in end
            else:
                # HTTP response message for file not found in cache
                # Fill in start
                tcpCliSock.sendall(b"HTTP/1.0 404 Not Found\r\nConnection: close\r\n\r\n")
                # Fill in end

        # Close the client socket
        # Fill in start
        tcpCliSock.close()
        # Fill in end

    # Close server socket (unreachable in this loop)
    # Fill in start
    tcpSerSock.close()
    # Fill in end

if __name__ == "__main__":
    main()
