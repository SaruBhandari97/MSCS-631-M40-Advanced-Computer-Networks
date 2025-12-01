import sys
import socket
import threading
import time

from VideoStream import VideoStream
from RtpPacket import RtpPacket

# RTSP states
INIT = 0
READY = 1
PLAYING = 2

# RTSP request types
SETUP = "SETUP"
PLAY = "PLAY"
PAUSE = "PAUSE"
TEARDOWN = "TEARDOWN"


class ServerWorker:
    def __init__(self, clientInfo):
        self.clientInfo = clientInfo
        self.state = INIT
        self.sessionId = 123456
        self.event = threading.Event()
        self.rtpSocket = None
        self.frameRate = 0.05  # ~20 fps

    def run(self):
        """Start thread to receive RTSP requests."""
        threading.Thread(target=self.recvRtspRequest, daemon=True).start()

    def recvRtspRequest(self):
        """Receive RTSP requests from the client."""
        connSocket = self.clientInfo["rtspSocket"]
        while True:
            data = connSocket.recv(256)
            if data:
                data = data.decode("utf-8")
                print("\nReceived RTSP request:\n" + data)
                self.processRtspRequest(data)
            else:
                break

    def processRtspRequest(self, data):
        """Process RTSP request."""
        lines = data.split('\n')
        requestLine = lines[0].split(' ')
        requestType = requestLine[0]
        filename = requestLine[1]
        seq = int(lines[1].split(' ')[1])

        if requestType == SETUP:
            if self.state == INIT:
                transport = lines[2]
                clientPort = int(transport.split('client_port=')[1].strip())
                self.clientInfo["rtpPort"] = clientPort

                self.clientInfo["videoStream"] = VideoStream(filename)
                self.state = READY

                self.sendRtspReply(seq)

        elif requestType == PLAY:
            if self.state == READY:
                self.state = PLAYING
                self.event.clear()
                self.sendRtspReply(seq)

                self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.rtpSocket = self.clientInfo["rtpSocket"]

                threading.Thread(target=self.sendRtp, daemon=True).start()

        elif requestType == PAUSE:
            if self.state == PLAYING:
                self.state = READY
                self.event.set()
                self.sendRtspReply(seq)

        elif requestType == TEARDOWN:
            self.event.set()
            self.sendRtspReply(seq)

            if self.rtpSocket:
                self.rtpSocket.close()
            self.clientInfo["rtspSocket"].close()

    def sendRtspReply(self, seq):
        """Send RTSP reply."""
        connSocket = self.clientInfo["rtspSocket"]
        reply = "RTSP/1.0 200 OK\nCSeq: " + str(seq) + "\nSession: 123456"
        connSocket.send(reply.encode())
        print("Sent RTSP reply:\n" + reply)

    def sendRtp(self):
        """Send RTP packets over UDP."""
        addr = self.clientInfo["addr"][0]
        port = self.clientInfo["rtpPort"]
        videoStream = self.clientInfo["videoStream"]

        seqnum = 0
        ssrc = 999999

        while True:
            if self.event.is_set():
                break

            data = videoStream.nextFrame()
            if data is None:
                break

            seqnum += 1
            rtpPacket = RtpPacket()
            # v=2, p=0, x=0, cc=0, m=0, pt=26 (MJPEG)
            rtpPacket.encode(2, 0, 0, 0, seqnum, 0, 26, ssrc, data)
            packet = rtpPacket.getPacket()

            try:
                self.rtpSocket.sendto(packet, (addr, port))
            except:
                print("Failed to send RTP packet")

            time.sleep(self.frameRate)


class Server:
    def __init__(self, port):
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtspSocket.bind(('', port))
        self.rtspSocket.listen(5)
        print("RTSP server listening on port", port)

    def start(self):
        while True:
            clientSocket, clientAddress = self.rtspSocket.accept()
            print("Received connection from:", clientAddress)
            clientInfo = {
                "rtspSocket": clientSocket,
                "addr": clientAddress
            }
            worker = ServerWorker(clientInfo)
            worker.run()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python Server.py <server_port>")
        sys.exit(1)

    serverPort = int(sys.argv[1])
    server = Server(serverPort)
    server.start()
