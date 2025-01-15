import socket
import struct
import threading
import time

MAGIC_COOKIE = 0xabcddcba
OFFER_MESSAGE_TYPE = 0x2
REQUEST_MESSAGE_TYPE = 0x3

def listen_for_offers():
    print("Client started, listening for offer requests...")
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind(('', 6666))
    
    while True:
        data, addr = udp_socket.recvfrom(1024)
        magic, msg_type, udp_port, tcp_port = struct.unpack('!IBHH', data)
        if magic == MAGIC_COOKIE and msg_type == OFFER_MESSAGE_TYPE:
            print(f"Received offer from {addr[0]} on TCP: {tcp_port}, UDP: {udp_port}")
            return addr[0], udp_port, tcp_port

def tcp_transfer(server_ip, tcp_port, file_size, transfer_id):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_ip, tcp_port))
    s.sendall(struct.pack('!IBQ', MAGIC_COOKIE, REQUEST_MESSAGE_TYPE, file_size))
    received = 0
    start_time = time.time()
    try:
        while True:
            try:
                data = s.recv(1024)
                if not data:
                    break
                received += len(data)
            except ConnectionResetError:
                print(f"Connection was reset by the server during TCP transfer #{transfer_id}")
                break
    finally:
        s.close()
    duration = time.time() - start_time
    speed = (received * 8) / duration
    print(f"TCP transfer #{transfer_id} finished, total time: {duration:.2f} seconds, total speed: {speed:.2f} bits/second")

def udp_transfer(server_ip, udp_port, file_size, transfer_id):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(1)
    request = struct.pack('!IBQ', MAGIC_COOKIE, REQUEST_MESSAGE_TYPE, file_size)
    udp_socket.sendto(request, (server_ip, udp_port))
    start_time = time.time()
    received = 0
    total_packets = 1
    try:
        while True:
            data, _ = udp_socket.recvfrom(1024)
            received += len(data)
            total_packets += 1
    except socket.timeout:
        pass
    duration = time.time() - start_time
    speed = (received * 8) / duration
    packet_loss = ((total_packets * 1024 - received) / (total_packets * 1024)) * 100
    print(f"UDP transfer #{transfer_id} finished, total time: {duration:.2f} seconds, total speed: {speed:.2f} bits/second, percentage of packets received successfully: {100 - packet_loss:.2f}%")

if __name__ == '__main__':
    while True:
        file_size = int(input("Enter file size in bytes: "))
        tcp_connections = int(input("Enter number of TCP connections: "))
        udp_connections = int(input("Enter number of UDP connections: "))

        server_ip, udp_port, tcp_port = listen_for_offers()
        print(f"IP: {server_ip}, TCP port: {tcp_port}, UDP: {udp_port}")
        threads = []
        for i in range(tcp_connections):
            t = threading.Thread(target=tcp_transfer, args=(server_ip, tcp_port, file_size, i + 1))
            threads.append(t)
            t.start()

        for i in range(udp_connections):
            t = threading.Thread(target=udp_transfer, args=(server_ip, udp_port, file_size, i + 1))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        print("All transfers complete, listening to offer requests")