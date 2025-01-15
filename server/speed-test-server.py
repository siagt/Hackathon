# import socket
# import struct
# import threading
# import time
# from typing import Tuple
#
# def get_network_ip():
#     """Get the non localhost IP address of the machine"""
#     try:
#         # Create a temporary socket to connect to an external address
#         temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         temp_socket.connect(("8.8.8.8", 80))  # Google's DNS server
#         network_ip = temp_socket.getsockname()[0]
#         temp_socket.close()
#         return network_ip
#     except Exception:
#         return "0.0.0.0"  # Fallback to all interfaces if we can't determine IP
#
# class SpeedTestServer:
#     def __init__(self, host: str = ""):
#         self.host = host
#         self.magic_cookie = 0xabcddcba
#         self.running = True
#         self.network_ip = get_network_ip()  # Get the actual network IP
#
#         # Create UDP socket
#         self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
#         self.udp_socket.bind(('0.0.0.0', 0))
#         self.udp_port = self.udp_socket.getsockname()[1]
#
#         # Create TCP socket
#         self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         self.tcp_socket.bind(('0.0.0.0', 0))
#         self.tcp_port = self.tcp_socket.getsockname()[1]
#         self.tcp_socket.listen(5)
#
#     def start(self):
#         """Start the server threads"""
#         print(f"Server started, listening on IP address {self.network_ip}")
#
#         offer_thread = threading.Thread(target=self._broadcast_offers)
#         offer_thread.daemon = True
#         offer_thread.start()
#
#         tcp_thread = threading.Thread(target=self._handle_tcp_connections)
#         tcp_thread.daemon = True
#         tcp_thread.start()
#
#         udp_thread = threading.Thread(target=self._handle_udp_connections)
#         udp_thread.daemon = True
#         udp_thread.start()
#
#         # Keep running until interrupted
#         try:
#             while self.running:
#                 time.sleep(1)
#         except KeyboardInterrupt:
#             self.running = False
#
#     def _broadcast_offers(self):
#         """Continuously broadcast offer messages"""
#         # magic cookie (4) + msg type (1) + UDP port (2) + TCP port (2)
#         offer_data = struct.pack('!IbHH',
#                                self.magic_cookie,
#                                0x2,
#                                self.udp_port,
#                                self.tcp_port)
#
#         while self.running:
#             try:
#                 # Send broadcast every second
#                 self.udp_socket.sendto(offer_data, ('<broadcast>', 13117))
#                 time.sleep(1)
#             except Exception as e:
#                 print(f"Error broadcasting offer: {e}")
#
#     def _handle_tcp_connections(self):
#         """Handle incoming TCP connections"""
#         while self.running:
#             try:
#                 client_socket, addr = self.tcp_socket.accept()
#                 # Create new thread for each client
#                 client_thread = threading.Thread(
#                     target=self._handle_tcp_client,
#                     args=(client_socket, addr)
#                 )
#                 client_thread.daemon = True
#                 client_thread.start()
#             except Exception as e:
#                 if self.running:
#                     print(f"Error accepting TCP connection: {e}")
#
#     def _handle_tcp_client(self, client_socket: socket.socket, addr: Tuple[str, int]):
#         """Handle individual TCP client connections"""
#         try:
#             # Receive file size request
#             data = client_socket.recv(1024).decode().strip()
#             file_size = int(data)
#
#             # Generate random data
#             data = b'x' * file_size
#
#             # Send data
#             client_socket.sendall(data)
#
#         except Exception as e:
#             print(f"Error handling TCP client {addr}: {e}")
#         finally:
#             client_socket.close()
#
#     def _handle_udp_connections(self):
#         """Handle incoming UDP connections"""
#         while self.running:
#             try:
#                 # Receive request
#                 data, addr = self.udp_socket.recvfrom(1024)
#
#                 # Verify message format
#                 if len(data) >= 13:  # Magic cookie (4) + type (1) + file size (8)
#                     cookie, msg_type, file_size = struct.unpack('!IbQ', data[:13])
#
#                     if cookie == self.magic_cookie and msg_type == 0x3:
#                         # Start new thread to handle UDP transfer
#                         client_thread = threading.Thread(
#                             target=self._handle_udp_client,
#                             args=(addr, file_size)
#                         )
#                         client_thread.daemon = True
#                         client_thread.start()
#
#             except Exception as e:
#                 if self.running:
#                     print(f"Error handling UDP connection: {e}")
#
#     def _handle_udp_client(self, addr: Tuple[str, int], file_size: int):
#         """Handle individual UDP client transfers"""
#         try:
#             # Calculate number of segments needed
#             segment_size = 1024
#             total_segments = (file_size + segment_size - 1) // segment_size
#
#             # Generate and send segments
#             for i in range(total_segments):
#                 remaining = min(segment_size, file_size - i * segment_size)
#                 payload = b'x' * remaining
#
#                 # Create header: magic cookie (4) + type (1) + total segments (8) + current segment (8)
#                 header = struct.pack('!IbQQ',
#                                    self.magic_cookie,
#                                    0x4,  # Payload type
#                                    total_segments,
#                                    i)
#                 # Send packet
#                 packet = header + payload
#                 self.udp_socket.sendto(packet, addr)
#                 time.sleep(0.001)
#
#         except Exception as e:
#             print(f"Error handling UDP client {addr}: {e}")
#
# if __name__ == "__main__":
#     server = SpeedTestServer()
#     server.start()
#
#
# import socket
# import struct
# import threading
# import time
# from typing import Tuple
#
# def get_network_ip():
#     """Get the non localhost IP address of the machine"""
#     try:
#         temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         temp_socket.connect(("8.8.8.8", 80))  # Google's DNS server
#         network_ip = temp_socket.getsockname()[0]
#         temp_socket.close()
#         return network_ip
#     except Exception:
#         return "0.0.0.0"  # Fallback to all interfaces if we can't determine IP
#
# class SpeedTestServer:
#     def __init__(self, host: str = ""):
#         self.host = host
#         self.magic_cookie = 0xabcddcba
#         self.running = True
#         self.network_ip = get_network_ip()  # Get the actual network IP
#
#         self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
#         self.udp_socket.bind(('0.0.0.0', 0))
#         self.udp_port = self.udp_socket.getsockname()[1]
#
#         self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         self.tcp_socket.bind(('0.0.0.0', 0))
#         self.tcp_port = self.tcp_socket.getsockname()[1]
#         self.tcp_socket.listen(5)
#
#     def start(self):
#         """Start the server threads"""
#         print(f"Server started, listening on IP address {self.network_ip}")
#
#         offer_thread = threading.Thread(target=self._broadcast_offers)
#         offer_thread.daemon = True
#         offer_thread.start()
#
#         tcp_thread = threading.Thread(target=self._handle_tcp_connections)
#         tcp_thread.daemon = True
#         tcp_thread.start()
#
#         udp_thread = threading.Thread(target=self._handle_udp_connections)
#         udp_thread.daemon = True
#         udp_thread.start()
#
#         try:
#             while self.running:
#                 time.sleep(1)
#         except KeyboardInterrupt:
#             self.running = False
#
#     def _broadcast_offers(self):
#         """Continuously broadcast offer messages"""
#         offer_data = struct.pack('!IbHH', self.magic_cookie, 0x2, self.udp_port, self.tcp_port)
#
#         while self.running:
#             try:
#                 self.udp_socket.sendto(offer_data, ('<broadcast>', 13117))
#                 time.sleep(1)
#             except Exception as e:
#                 print(f"Error broadcasting offer: {e}")
#
#     def _handle_tcp_connections(self):
#         """Handle incoming TCP connections"""
#         while self.running:
#             try:
#                 client_socket, addr = self.tcp_socket.accept()
#                 client_thread = threading.Thread(target=self._handle_tcp_client, args=(client_socket, addr))
#                 client_thread.daemon = True
#                 client_thread.start()
#             except Exception as e:
#                 if self.running:
#                     print(f"Error accepting TCP connection: {e}")
#
#     def _handle_tcp_client(self, client_socket: socket.socket, addr: Tuple[str, int]):
#         """Handle individual TCP client connections"""
#         try:
#             data = client_socket.recv(1024).decode().strip()
#             file_size = int(data)
#
#             data = b'x' * file_size
#             client_socket.sendall(data)
#
#         except Exception as e:
#             print(f"Error handling TCP client {addr}: {e}")
#         finally:
#             client_socket.close()
#
#     def _handle_udp_connections(self):
#         """Handle incoming UDP connections"""
#         while self.running:
#             try:
#                 data, addr = self.udp_socket.recvfrom(1024)
#
#                 if len(data) >= 13:  # Magic cookie (4) + type (1) + file size (8)
#                     cookie, msg_type, file_size = struct.unpack('!IbQ', data[:13])
#
#                     if cookie == self.magic_cookie and msg_type == 0x3:
#                         client_thread = threading.Thread(target=self._handle_udp_client, args=(addr, file_size))
#                         client_thread.daemon = True
#                         client_thread.start()
#
#             except Exception as e:
#                 if self.running:
#                     print(f"Error receiving UDP connection: {e}")
#
#     def _handle_udp_client(self, addr: Tuple[str, int], file_size: int):
#         """Handle individual UDP client transfers"""
#         try:
#             total_segments = (file_size + 8191) // 8192  # Chunk size 8192 bytes
#             data = b'x' * file_size
#             segment_index = 0
#
#             while segment_index < total_segments:
#                 start_index = segment_index * 8192
#                 end_index = min((segment_index + 1) * 8192, file_size)
#                 chunk_data = data[start_index:end_index]
#
#                 packet = struct.pack('!IbQQ', self.magic_cookie, 0x4, total_segments, segment_index) + chunk_data
#                 self.udp_socket.sendto(packet, addr)
#
#                 segment_index += 1
#
#         except Exception as e:
#             print(f"Error handling UDP client {addr}: {e}")
#
# if __name__ == "__main__":
#     server = SpeedTestServer()
#     server.start()


import socket
import struct
import threading
import time
from typing import Tuple

def get_network_ip():
    """Get the non localhost IP address of the machine"""
    try:
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_socket.connect(("8.8.8.8", 80))  # Google's DNS server
        network_ip = temp_socket.getsockname()[0]
        temp_socket.close()
        return network_ip
    except Exception:
        return "0.0.0.0"  # Fallback to all interfaces if we can't determine IP

class SpeedTestServer:
    def __init__(self, host: str = ""):
        self.host = host
        self.magic_cookie = 0xabcddcba
        self.running = True
        self.network_ip = get_network_ip()  # Get the actual network IP

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.bind(('0.0.0.0', 0))
        self.udp_port = self.udp_socket.getsockname()[1]

        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind(('0.0.0.0', 0))
        self.tcp_port = self.tcp_socket.getsockname()[1]
        self.tcp_socket.listen(5)

    def start(self):
        """Start the server threads"""
        print(f"Server started, listening on IP address {self.network_ip}")

        offer_thread = threading.Thread(target=self._broadcast_offers)
        offer_thread.daemon = True
        offer_thread.start()

        tcp_thread = threading.Thread(target=self._handle_tcp_connections)
        tcp_thread.daemon = True
        tcp_thread.start()

        udp_thread = threading.Thread(target=self._handle_udp_connections)
        udp_thread.daemon = True
        udp_thread.start()

        try:
            while self.running:
                time.sleep(0.1)  # Sleep to prevent busy-waiting
        except KeyboardInterrupt:
            self.running = False

    def _broadcast_offers(self):
        """Continuously broadcast offer messages"""
        offer_data = struct.pack('!IbHH', self.magic_cookie, 0x2, self.udp_port, self.tcp_port)

        while self.running:
            try:
                self.udp_socket.sendto(offer_data, ('<broadcast>', 13117))
                time.sleep(1)  # Broadcast every second, keep it efficient
            except Exception as e:
                print(f"Error broadcasting offer: {e}")

    def _handle_tcp_connections(self):
        """Handle incoming TCP connections"""
        while self.running:
            try:
                client_socket, addr = self.tcp_socket.accept()
                client_thread = threading.Thread(target=self._handle_tcp_client, args=(client_socket, addr))
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self.running:
                    print(f"Error accepting TCP connection: {e}")
            time.sleep(0.1)  # Sleep to prevent busy-waiting

    def _handle_tcp_client(self, client_socket: socket.socket, addr: Tuple[str, int]):
        """Handle individual TCP client connections"""
        try:
            data = client_socket.recv(1024).decode().strip()
            file_size = int(data)

            data = b'x' * file_size
            client_socket.sendall(data)

        except Exception as e:
            print(f"Error handling TCP client {addr}: {e}")
        finally:
            client_socket.close()

    def _handle_udp_connections(self):
        """Handle incoming UDP connections"""
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(1024)

                if len(data) >= 13:  # Magic cookie (4) + type (1) + file size (8)
                    cookie, msg_type, file_size = struct.unpack('!IbQ', data[:13])

                    if cookie == self.magic_cookie and msg_type == 0x3:
                        client_thread = threading.Thread(target=self._handle_udp_client, args=(addr, file_size))
                        client_thread.daemon = True
                        client_thread.start()

            except Exception as e:
                if self.running:
                    print(f"Error receiving UDP connection: {e}")
            time.sleep(0.1)  # Sleep to prevent busy-waiting

    def _handle_udp_client(self, addr: Tuple[str, int], file_size: int):
        """Handle individual UDP client transfers"""
        try:
            total_segments = (file_size + 8191) // 8192  # Chunk size 8192 bytes
            data = b'x' * file_size
            segment_index = 0

            while segment_index < total_segments:
                start_index = segment_index * 8192
                end_index = min((segment_index + 1) * 8192, file_size)
                chunk_data = data[start_index:end_index]

                packet = struct.pack('!IbQQ', self.magic_cookie, 0x4, total_segments, segment_index) + chunk_data
                self.udp_socket.sendto(packet, addr)

                segment_index += 1

        except Exception as e:
            print(f"Error handling UDP client {addr}: {e}")

if __name__ == "__main__":
    server = SpeedTestServer()
    server.start()

