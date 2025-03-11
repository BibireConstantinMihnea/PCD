import socket
import sys

BUF_SIZE = 65536
PORT_NUM = 5001

def usage(progname):
    print(f"Usage: {progname} <protocol> [mode]")
    print("  protocol: tcp or udp")
    print("  mode (for udp only): streaming (use: st) or stopandwait (use: sw) (default: streaming)")
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        usage(sys.argv[0])
    protocol = sys.argv[1].lower()
    mode = None

    if protocol not in ['tcp', 'udp']:
        print("Invalid protocol")
        usage(sys.argv[0])
    
    if protocol == 'udp':
        if len(sys.argv) < 3:
            usage(sys.argv[0])
        mode = sys.argv[2].lower()
        if mode not in ['st', 'sw']:
            print("Invalid mode")
            usage(sys.argv[0])
    else:
        if len(sys.argv) > 2:
            usage(sys.argv[0])

    total_bytes = 0
    total_messages = 0

    if protocol == 'tcp':
        # ------------------- TCP Protocol -------------------
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_sock.bind(('', PORT_NUM))
        except Exception as e:
            print("ERROR binding socket:", e)
            sys.exit(1)
        server_sock.listen(5)
        print(f"Listening on port {PORT_NUM}...")

        client_sock, client_addr = server_sock.accept()
        print(f"Connection accepted from {client_addr[0]}")

        while True:
            data = client_sock.recv(BUF_SIZE)
            if not data:
                break
            total_bytes += len(data)
            total_messages += 1

        print("Protocol used: TCP")
        print("Mode used: Streaming (default)")
        print(f"Total messages received: {total_messages}")
        print(f"Total bytes received: {total_bytes}")

        client_sock.close()
        server_sock.close()

    elif protocol == 'udp':
        # ------------------- UDP Protocol -------------------
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            server_sock.bind(('', PORT_NUM))
        except Exception as e:
            print("ERROR binding socket:", e)
            sys.exit(1)
        print(f"UDP server listening on port {PORT_NUM}...")

        while True:
            data, client_addr = server_sock.recvfrom(BUF_SIZE)
            if len(data) == 3 and data == b"FIN":
                fin_ack = b"ACK_FIN"
                try:
                    server_sock.sendto(fin_ack, client_addr)
                except Exception as e:
                    print("ERROR sending FIN ACK:", e)
                    sys.exit(1)
                break

            total_bytes += len(data)
            total_messages += 1

            if mode == 'sw':
                ack = b"ACK"
                try:
                    server_sock.sendto(ack, client_addr)
                except Exception as e:
                    print("ERROR sending ACK:", e)
                    sys.exit(1)

        print("Protocol used: UDP")
        if mode == 'sw':
            print("Mode used: Stop and Wait")
        else:
            print("Mode used: Streaming")
        print(f"Total messages received: {total_messages}")
        print(f"Total bytes received: {total_bytes}")
        
        server_sock.close()

if __name__ == '__main__':
    main()
