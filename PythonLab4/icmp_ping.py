#!/usr/bin/env python3
import os
import sys
import struct
import time
import select
import socket
from socket import AF_INET, SOCK_RAW, getprotobyname, htons, gethostbyname

ICMP_ECHO_REQUEST = 8  # Type code for Echo Request

def checksum(data: bytes) -> int:
    """Compute Internet Checksum of the supplied data."""
    csum = 0
    count_to = (len(data) // 2) * 2
    count = 0

    # Handle 16-bit chunks
    while count < count_to:
        this_val = data[count + 1] * 256 + data[count]
        csum = csum + this_val
        csum = csum & 0xffffffff
        count += 2

    # Handle odd trailing byte
    if count_to < len(data):
        csum = csum + data[-1]
        csum = csum & 0xffffffff

    # Fold 32-bit sum to 16 bits
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum & 0xffff
    # Swap bytes
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def receiveOnePing(mySocket: socket.socket, ID: int, timeout: float, destAddr: str):
    """Receive the ping from the socket."""
    time_left = timeout
    while True:
        started_select = time.time()
        ready = select.select([mySocket], [], [], time_left)
        how_long_in_select = time.time() - started_select

        if ready[0] == []:  # Timeout
            return "Request timed out."

        time_received = time.time()
        rec_packet, addr = mySocket.recvfrom(2048)

        # ---------- Fill-in: parse ICMP header from IP packet ----------
        # IP header is variable length; IHL tells its size (in 32-bit words)
        # rec_packet[0] = Version(4 bits) | IHL(4 bits)
        ip_header_len = (rec_packet[0] & 0x0F) * 4
        ip_header = rec_packet[:ip_header_len]

        # TTL is byte 9 of the IP header
        ttl = ip_header[8]

        # ICMP header immediately follows IP header
        icmp_header = rec_packet[ip_header_len:ip_header_len + 8]
        icmp_type, icmp_code, icmp_checksum, packet_id, sequence = struct.unpack("bbHHh", icmp_header)
        # ----------------------------------------------------------------

        if icmp_type == 0 and icmp_code == 0 and packet_id == ID:
            # This is our echo reply. Extract the timestamp from the payload.
            data_section = rec_packet[ip_header_len + 8:]
            # First 8 bytes of data are the original time sent (struct "d")
            try:
                time_sent = struct.unpack("d", data_section[:8])[0]
            except struct.error:
                # If payload is shorter than expected, treat as timed out
                return "Reply received but payload malformed."

            rtt_ms = (time_received - time_sent) * 1000.0
            bytes_len = len(rec_packet)
            return f"Reply from {destAddr}: bytes={bytes_len} time={rtt_ms:.2f}ms TTL={ttl}"

        # Not our packet; keep waiting until timeout
        time_left = time_left - how_long_in_select
        if time_left <= 0:
            return "Request timed out."

def sendOnePing(mySocket: socket.socket, destAddr: str, ID: int):
    """Send one ICMP Echo Request."""
    # Header: type (8), code (8), checksum (16), id (16), sequence (16)
    my_checksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
    data = struct.pack("d", time.time())  # put timestamp in payload

    # Calculate checksum on the header + data
    my_checksum = checksum(header + data)

    # Convert checksum to network byte order
    my_checksum = htons(my_checksum)

    # Repack header with correct checksum
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
    packet = header + data

    # Port number is irrelevant for ICMP, but tuple requires something
    mySocket.sendto(packet, (destAddr, 1))

def doOnePing(destAddr: str, timeout: float):
    """Perform a single ping to the destination address."""
    icmp_proto = getprotobyname("icmp")
    # Raw socket (requires admin/root)
    mySocket = socket.socket(AF_INET, SOCK_RAW, icmp_proto)

    myID = os.getpid() & 0xFFFF
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay

def ping(host: str, count: int = 4, timeout: float = 1.0):
    """Ping a host 'count' times."""
    dest = gethostbyname(host)
    print(f"Pinging {host} [{dest}] with Python ICMP:")
    for i in range(count):
        result = doOnePing(dest, timeout)
        print(result)
        time.sleep(1)

if __name__ == "__main__":
    # Simple CLI: python icmp_ping.py <host> [count]
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <host> [count]")
        sys.exit(1)
    host = sys.argv[1]
    cnt = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    ping(host, cnt)
