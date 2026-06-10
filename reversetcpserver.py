import socket
import struct
import sys
import threading
import datetime

def recv_exact(sock, length):
    data = b''
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError("Connection closed prematurely")
        data += chunk
    return data

def log_event(log_file, event_type, packet_type, src_addr, dst_addr, length):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_line = f"{timestamp} [{event_type}] {packet_type} from {src_addr[0]}:{src_addr[1]} to {dst_addr[0]}:{dst_addr[1]}, length={length} bytes\n"
    log_file.write(log_line)
    log_file.flush()

def handle_client(client_sock, client_addr, log_file):
    server_addr = client_sock.getsockname()  # 提前保存服务器端地址
    try:
        init_header = recv_exact(client_sock, 6)
        init_type, N = struct.unpack('>HI', init_header)
        if init_type != 1:
            raise ValueError(f"Expected Type=1 (Initialization), got {init_type}")
        log_event(log_file, 'RECV', f'Initialization (Type=1) N={N}', client_addr, server_addr, 6)

        agree_packet = struct.pack('>H', 2)
        client_sock.sendall(agree_packet)
        log_event(log_file, 'SEND', 'Agree (Type=2)', server_addr, client_addr, 2)

        for i in range(N):
            req_header = recv_exact(client_sock, 6)
            req_type, req_length = struct.unpack('>HI', req_header)
            if req_type != 3:
                raise ValueError(f"Expected Type=3 (ReverseRequest), got {req_type}")
            data_chunk = recv_exact(client_sock, req_length)
            log_event(log_file, 'RECV', f'ReverseRequest (Type=3) Block {i+1}', client_addr, server_addr, 6 + req_length)

            reversed_chunk = data_chunk[::-1]
            ans_header = struct.pack('>HI', 4, len(reversed_chunk))
            ans_packet = ans_header + reversed_chunk
            client_sock.sendall(ans_packet)
            log_event(log_file, 'SEND', f'ReverseAnswer (Type=4) Block {i+1}', server_addr, client_addr, len(ans_packet))

    except Exception as e:
        log_event(log_file, 'ERROR', f'Client error: {str(e)}', client_addr, server_addr, 0)
    finally:
        client_sock.close()
        log_event(log_file, 'DISCONNECT', 'Client', client_addr, server_addr, 0)

def main():
    if len(sys.argv) != 2:
        print("Usage: python reversetcpserver.py <server_port>")
        sys.exit(1)

    server_port = int(sys.argv[1])
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_addr = ('0.0.0.0', server_port)

    try:
        server_sock.bind(server_addr)
    except OSError:
        print(f"Error: Port {server_port} is already in use")
        sys.exit(1)

    server_sock.listen(5)
    log_file = open('server_run_log.txt', 'w', encoding='utf-8')
    log_event(log_file, 'START', 'Server', server_addr, ('', 0), 0)
    print(f"Server listening on 0.0.0.0:{server_port}")

    try:
        while True:
            client_sock, client_addr = server_sock.accept()
            log_event(log_file, 'ACCEPT', 'New client', client_addr, client_sock.getsockname(), 0)
            client_thread = threading.Thread(target=handle_client, args=(client_sock, client_addr, log_file))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server_sock.close()
        log_event(log_file, 'STOP', 'Server', server_addr, ('', 0), 0)
        log_file.close()

if __name__ == "__main__":
    main()