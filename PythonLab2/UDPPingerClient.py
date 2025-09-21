#!/usr/bin/env python3
"""
UDPPingerClient.py
A UDP ping client that sends 10 pings to a server and measures RTT.
Message format sent: "Ping <sequence_number> <timestamp>"
"""

import time
import socket
import sys
from statistics import mean

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 12000
TIMEOUT_SECS = 1.0
COUNT = 10

def main():
    # Allow optional CLI overrides: python UDPPingerClient.py [host] [port]
    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    try:
        port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT
    except ValueError:
        print("Port must be an integer.")
        sys.exit(1)

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT_SECS)

    sent = 0
    received = 0
    rtts = []

    print(f"UDP Ping Client -> server {host}:{port} (timeout={TIMEOUT_SECS:.1f}s)")
    print("-" * 60)

    for seq in range(1, COUNT + 1):
        # Construct message
        send_time = time.time()
        message = f"Ping {seq} {send_time:.6f}".encode("ascii", errors="ignore")

        # Send
        try:
            sock.sendto(message, (host, port))
            sent += 1
        except OSError as e:
            print(f"Seq={seq}: send failed: {e}")
            continue

        # Receive with timeout
        try:
            data, addr = sock.recvfrom(1024)
            recv_time = time.time()
            rtt = recv_time - send_time
            received += 1
            rtts.append(rtt)
            # Print server response and RTT
            try:
                text = data.decode("ascii", errors="ignore")
            except Exception:
                text = str(data)
            print(f"Reply from {addr[0]}:{addr[1]} | seq={seq} | RTT={rtt:.3f} s | payload={text!r}")
        except socket.timeout:
            print(f"Request timed out for seq={seq}")
        except OSError as e:
            print(f"Seq={seq}: receive failed: {e}")

    # Summary statistics
    loss_count = sent - received
    loss_pct = (loss_count / sent * 100.0) if sent else 0.0
    print("-" * 60)
    print("Ping statistics:")
    print(f"  Packets: sent = {sent}, received = {received}, lost = {loss_count} ({loss_pct:.1f}% loss)")
    if rtts:
        print(f"  RTTs: min = {min(rtts):.3f} s, avg = {mean(rtts):.3f} s, max = {max(rtts):.3f} s")
    else:
        print("  RTTs: min/avg/max = N/A (no replies)")

    sock.close()

if __name__ == "__main__":
    main()
