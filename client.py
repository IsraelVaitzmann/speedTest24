import socket
import struct
import threading
import time

MAGIC_COOKIE = 0xabcddcba
OFFER_MESSAGE_TYPE = 0x2
REQUEST_MESSAGE_TYPE = 0x3

def listen_for_offers():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind(('', 13117))
    
    while True:
        data, addr = udp_socket.recvfrom(1024)
        magic, msg_type, udp_port, tcp_port = struct.unpack('!IBHH', data)
        if magic == MAGIC_COOKIE and msg_type == OFFER_MESSAGE_TYPE:
            print(f"Received offer from {addr[0]} on TCP: {tcp_port}, UDP: {udp_port}")
            return addr[0], udp_port, tcp_port

def tcp_transfer(server_ip, tcp_port, file_size):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server_ip, tcp_port))
        s.sendall(f"{file_size}\n".encode())
        start_time = time.time()
        data = s.recv(file_size)
        duration = time.time() - start_time
        print(f"TCP transfer finished: {len(data)} bytes in {duration:.2f} seconds")

def udp_transfer(server_ip, udp_port, file_size):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(1)
    request = struct.pack('!IBQ', MAGIC_COOKIE, REQUEST_MESSAGE_TYPE, file_size)
    udp_socket.sendto(request, (server_ip, udp_port))
    start_time = time.time()
    received = 0
    try:
        while True:
            data, _ = udp_socket.recvfrom(1024)
            received += len(data)
    except socket.timeout:
        pass
    duration = time.time() - start_time
    print(f"UDP transfer finished: {received} bytes in {duration:.2f} seconds")

if __name__ == '__main__':
    file_size = int(input("Enter file size in bytes: "))
    server_ip, udp_port, tcp_port = listen_for_offers()
    threading.Thread(target=tcp_transfer, args=(server_ip, tcp_port, file_size)).start()
    threading.Thread(target=udp_transfer, args=(server_ip, udp_port, file_size)).start()