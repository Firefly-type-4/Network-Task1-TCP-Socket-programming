import socket
import struct
import sys
import random
import datetime

def recv_exact(sock, length):
    data = b''
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError("Connection closed prematurely")
        data += chunk
    return data

def split_file(total_len, Lmin, Lmax, seed):
    random.seed(seed)
    chunks = []
    remaining = total_len
    while remaining > 0:
        if remaining <= Lmax:
            chunks.append(remaining)
            break
        chunk_len = random.randint(Lmin, Lmax)
        chunks.append(chunk_len)
        remaining -= chunk_len
    return chunks

def log_event(log_file, event_type, packet_type, src_addr, dst_addr, length):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_line = f"{timestamp} [{event_type}] {packet_type} from {src_addr[0]}:{src_addr[1]} to {dst_addr[0]}:{dst_addr[1]}, length={length} bytes\n"
    log_file.write(log_line)
    log_file.flush()

def main():
    if len(sys.argv) != 8:
        print("Usage: python reversetcpclient.py <server_ip> <server_port> <input_file> <output_file> <Lmin> <Lmax> <chunk_seed>")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    input_file = sys.argv[3]
    output_file = sys.argv[4]
    Lmin = int(sys.argv[5])
    Lmax = int(sys.argv[6])
    chunk_seed = int(sys.argv[7])

    try:
        with open(input_file, 'rb') as f:
            file_data = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)

    chunks = split_file(len(file_data), Lmin, Lmax, chunk_seed)
    N = len(chunks)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_addr = (server_ip, server_port)
    local_addr = None  # 新增：保存本地套接字地址

    try:
        sock.connect(server_addr)
        local_addr = sock.getsockname()  # 连接成功后立即保存本地地址
    except ConnectionRefusedError:
        print(f"Error: Could not connect to server at {server_ip}:{server_port}")
        sys.exit(1)

    log_file = open('client_run_log.txt', 'w', encoding='utf-8')
    log_event(log_file, 'CONNECT', 'Client', local_addr, server_addr, 0)

    try:
        init_packet = struct.pack('>HI', 1, N)
        sock.sendall(init_packet)
        log_event(log_file, 'SEND', 'Initialization (Type=1)', local_addr, server_addr, len(init_packet))

        agree_data = recv_exact(sock, 2)
        agree_type, = struct.unpack('>H', agree_data)
        if agree_type != 2:
            raise ValueError(f"Expected Type=2 (Agree), got {agree_type}")
        log_event(log_file, 'RECV', 'Agree (Type=2)', server_addr, local_addr, len(agree_data))

        reversed_data_list = []
        for i in range(N):
            chunk_len = chunks[i]
            start = sum(chunks[:i])
            end = start + chunk_len
            data_chunk = file_data[start:end]

            req_header = struct.pack('>HI', 3, chunk_len)
            req_packet = req_header + data_chunk
            sock.sendall(req_packet)
            log_event(log_file, 'SEND', f'ReverseRequest (Type=3) Block {i+1}', local_addr, server_addr, len(req_packet))

            ans_header = recv_exact(sock, 6)
            ans_type, ans_length = struct.unpack('>HI', ans_header)
            if ans_type != 4:
                raise ValueError(f"Expected Type=4 (ReverseAnswer), got {ans_type}")
            reversed_chunk = recv_exact(sock, ans_length)
            log_event(log_file, 'RECV', f'ReverseAnswer (Type=4) Block {i+1}', server_addr, local_addr, 6 + ans_length)

            print(f"{i+1}: {reversed_chunk.decode('ascii')}")
            reversed_data_list.append(reversed_chunk)

        full_reversed = b''.join(reversed_data_list)
        with open(output_file, 'wb') as f:
            f.write(full_reversed)
        print(f"\nSuccess! Full reversed file saved to {output_file}")

    except Exception as e:
        log_event(log_file, 'ERROR', f'Client error: {str(e)}', local_addr, server_addr, 0)
        print(f"Error: {str(e)}")
    finally:
        sock.close()
        # 现在使用提前保存的local_addr，而不是sock.getsockname()
        log_event(log_file, 'DISCONNECT', 'Client', local_addr, server_addr, 0)
        log_file.close()

if __name__ == "__main__":
    main()

    #  python reversetcpserver.py 8888