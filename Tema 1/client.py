import socket
import sys
import time

PORT_NUM = 5001
MAX_BUF_SIZE = 65536
ONE_GB = 1073741824
FIVE_HUNDRED_MB = 524288000

def usage(progname):
    print(f"Usage: {progname} <protocol> [mode] <ip_address> <block_size> <total_bytes_to_send>")
    print("  protocol: tcp or udp")
    print("  mode (for udp only): streaming (use: st) or stopandwait (use: sw) (default: streaming)")
    print(f"  block_size: size of each message (1 to {MAX_BUF_SIZE})")
    print(f"  total_bytes_to_send: total number of bytes to send (1GB or 500MB)")
    sys.exit(1)

def main():
    argc = len(sys.argv)
    if argc < 5:
        usage(sys.argv[0])
    
    protocol = sys.argv[1].lower()
    if protocol not in ['tcp', 'udp']:
        print("Invalid protocol")
        usage(sys.argv[0])
    
    ip_address = None
    mode = None
    block_size = 0
    total_bytes_to_send = 0

    # Parse arguments
    if protocol == 'udp':
        if argc >= 6 and sys.argv[2].lower() in ['sw', 'st']:
            mode = sys.argv[2].lower()
            ip_address = sys.argv[3]
            try:
                block_size = int(sys.argv[4])
                total_bytes_to_send = ONE_GB if sys.argv[5] == '1GB' else FIVE_HUNDRED_MB
            except ValueError:
                print("Invalid block size or total bytes")
                usage(sys.argv[0])
        else:
            mode = 'st'
            ip_address = sys.argv[2]
            try:
                block_size = int(sys.argv[3])
                total_bytes_to_send = ONE_GB if sys.argv[4] == '1GB' else FIVE_HUNDRED_MB
            except ValueError:
                print("Invalid block size or total bytes")
                usage(sys.argv[0])
    elif protocol == 'tcp':
        ip_address = sys.argv[2]
        try:
            block_size = int(sys.argv[3])
            total_bytes_to_send = ONE_GB if sys.argv[4] == '1GB' else FIVE_HUNDRED_MB
        except ValueError:
            print("Invalid block size or total bytes")
            usage(sys.argv[0])
        
    
    if block_size < 1 or block_size > MAX_BUF_SIZE:
        print("Invalid block size")
        sys.exit(1)
    
    data = bytes(block_size)
    bytes_sent = 0
    total_messages = 0

    if protocol == 'tcp':
        # ------------------- TCP Protocol -------------------
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_sock.connect((ip_address, PORT_NUM))
        except Exception as e:
            print("ERROR connecting:", e)
            sys.exit(1)
        start_time = time.time()
        while bytes_sent < total_bytes_to_send:
            to_send = min(block_size, total_bytes_to_send - bytes_sent)
            sent = client_sock.send(data[:to_send])
            if sent == 0:
                print("Socket connection broken")
                sys.exit(1)
            bytes_sent += sent
            total_messages += 1
        end_time = time.time()
        elapsed = end_time - start_time

        print("Protocol used: TCP")
        print("Mode used: Streaming (default)")
        print(f"Total transmission time: {elapsed:.6f} seconds")
        print(f"Total number of messages sent: {total_messages}")
        print(f"Total number of bytes sent: {bytes_sent}")

        client_sock.close()

    elif protocol == 'udp':
        # ------------------- UDP Protocol -------------------
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if mode == 'sw':
            client_sock.settimeout(2.0)
        server_address = (ip_address, PORT_NUM)
        start_time = time.time()
        while bytes_sent < total_bytes_to_send:
            to_send = min(block_size, total_bytes_to_send - bytes_sent)
            try:
                sent = client_sock.sendto(data[:to_send], server_address)
            except Exception as e:
                print("ERROR sending to socket:", e)
                sys.exit(1)
            bytes_sent += sent
            total_messages += 1

            if mode == 'sw':
                try:
                    ack, _ = client_sock.recvfrom(16)
                except socket.timeout:
                    print("ERROR receiving ACK")
                    sys.exit(1)
                    
        fin = b"FIN"
        try:
            client_sock.sendto(fin, server_address)
            if mode == 'sw':
                ack, _ = client_sock.recvfrom(16)
        except Exception as e:
            print("ERROR sending/receiving FIN:", e)
            sys.exit(1)
        end_time = time.time()
        elapsed = end_time - start_time

        print("Protocol used: UDP")
        if mode == 'sw':
            print("Mode used: Stop and Wait")
        else:
            print("Mode used: Streaming")
        print(f"Total transmission time: {elapsed:.6f} seconds")
        print(f"Total number of messages sent: {total_messages}")
        print(f"Total number of bytes sent: {bytes_sent}")

        client_sock.close()
        
if __name__ == '__main__':
    main()
