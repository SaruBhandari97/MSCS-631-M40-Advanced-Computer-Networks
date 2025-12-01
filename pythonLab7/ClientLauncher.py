import sys
from tkinter import Tk
from Client import Client

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python ClientLauncher.py <server_addr> <server_port> <rtp_port> <movie_file>")
        sys.exit(1)

    serverAddr = sys.argv[1]
    serverPort = sys.argv[2]
    rtpPort = sys.argv[3]
    filename = sys.argv[4]

    root = Tk()
    root.title("RTP Video Client")
    app = Client(root, serverAddr, serverPort, rtpPort, filename)
    root.mainloop()
