import socket
import threading
import struct
import time

MAGIC_COOKIE = 0xabcddcba
OFFER_MESSAGE_TYPE = 0x2
REQUEST_MESSAGE_TYPE = 0x3
PAYLOAD_MESSAGE_TYPE = 0x4

def send_offer_broadcast(udp_port, tcp_port):
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            offer = struct.pack('!IBHH', MAGIC_COOKIE, OFFER_MESSAGE_TYPE, udp_port, tcp_port)
            s.sendto(offer, ('<broadcast>', udp_port))
        time.sleep(1)

def handle_tcp_connection(client_socket, address):
    try:
        data = client_socket.recv(1024).decode().strip()
        file_size = int(data)
        # Send the requested file size worth of data
        payload = b'\x00' * file_size
        client_socket.sendall(payload)
    finally:
        client_socket.close()

def handle_udp_connection(server_socket, client_address, file_size):
    segment_count = (file_size + 1023) // 1024
    for i in range(segment_count):
        payload = struct.pack('!IBQQ', MAGIC_COOKIE, PAYLOAD_MESSAGE_TYPE, segment_count, i) + b'\x00' * 1024
        server_socket.sendto(payload, client_address)

def start_server():
    udp_port = 0
    tcp_port = 0

    # Setup TCP
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(('', 0))
    tcp_socket.listen(5)
    tcp_port = tcp_socket.getsockname()[1]
    server_ip = socket.gethostbyname(socket.gethostname())

    # Setup UDP
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('', 0))
    udp_port = udp_socket.getsockname()[1]

    print(f"Server started, listening on IP address {server_ip}, TCP: {tcp_port}, UDP: {udp_port}")

    threading.Thread(target=send_offer_broadcast, args=(udp_port, tcp_port), daemon=True).start()

    while True:
        conn, addr = tcp_socket.accept()
        threading.Thread(target=handle_tcp_connection, args=(conn, addr), daemon=True).start()

        data, client_address = udp_socket.recvfrom(1024)
        magic, msg_type, file_size = struct.unpack('!IBQ', data)
        if magic == MAGIC_COOKIE and msg_type == REQUEST_MESSAGE_TYPE:
            threading.Thread(target=handle_udp_connection, args=(udp_socket, client_address, file_size), daemon=True).start()

if __name__ == '__main__':
    start_server()