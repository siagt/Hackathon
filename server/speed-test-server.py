
import socket
import struct
import threading
import time
from typing import Tuple

class SpeedTestServer:
    def __init__(self):
        self.magic_cookie = 0xabcddcba
        self.running = True

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
        print(f"Server started, sending offers from IP address {socket.gethostbyname(socket.gethostname())}")

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
            # Define a safe chunk size for UDP payloads
            chunk_size = 1400  # A conservative size to avoid fragmentation (fits within Ethernet MTU)
            total_segments = (file_size + chunk_size - 1) // chunk_size  # Total number of segments
            data = b'x' * file_size  # Simulated data
            segment_index = 0

            while segment_index < total_segments:
                start_index = segment_index * chunk_size
                end_index = min((segment_index + 1) * chunk_size, file_size)
                chunk_data = data[start_index:end_index]

                # Create a packet with the header and chunk data
                packet = struct.pack('!IbQQ', self.magic_cookie, 0x4, total_segments, segment_index) + chunk_data
                self.udp_socket.sendto(packet, addr)  # Send the packet

                segment_index += 1

        except Exception as e:
            print(f"Error handling UDP client {addr}: {e}")


if __name__ == "__main__":
    server = SpeedTestServer()
    server.start()

