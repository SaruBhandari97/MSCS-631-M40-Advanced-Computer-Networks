from socket import *
import sys
import struct
import time
import select

MAX_HOPS = 30
TIMEOUT = 2.0
TRIES = 2
DEST_PORT = 33434   # high UDP port, like classic traceroute


def traceroute(hostname):
    try:
        dest_addr = gethostbyname(hostname)
    except Exception as e:
        print(f"Could not resolve {hostname}: {e}")
        return

    print(f"Tracing route to {hostname} [{dest_addr}]")
    print(f"over a maximum of {MAX_HOPS} hops:\n")

    for ttl in range(1, MAX_HOPS + 1):
        sys.stdout.write(f"{ttl:2d}  ")
        sys.stdout.flush()

        curr_addr = None

        for attempt in range(TRIES):
            # Socket to receive ICMP (Time Exceeded / Dest Unreachable)
            recv_socket = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)
            recv_socket.settimeout(TIMEOUT)
            recv_socket.bind(("", DEST_PORT))

            # UDP socket to send probe
            send_socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
            send_socket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack("I", ttl))

            start_time = time.time()

            try:
                send_socket.sendto(b"", (dest_addr, DEST_PORT))

                ready = select.select([recv_socket], [], [], TIMEOUT)
                if not ready[0]:
                    # No reply within timeout
                    sys.stdout.write("  *  ")
                    continue

                recv_packet, addr = recv_socket.recvfrom(512)
                curr_addr = addr[0]
                elapsed_ms = (time.time() - start_time) * 1000

                try:
                    curr_name = gethostbyaddr(curr_addr)[0]
                except Exception:
                    curr_name = curr_addr

                sys.stdout.write(f"  {curr_addr}  {elapsed_ms:.0f} ms")

            except timeout:
                sys.stdout.write("  *  ")
            finally:
                recv_socket.close()
                send_socket.close()

        sys.stdout.write("\n")

        # If we reached destination, stop
        if curr_addr == dest_addr:
            break


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "google.com"

    traceroute(target)
