# import socket
# import struct
# import threading
# import time
# from typing import List, Tuple
# from enum import Enum
#
# # three possible states for the client
# class ClientState(Enum):
#     STARTUP = 1
#     LOOKING_FOR_SERVER = 2
#     SPEED_TEST = 3
#
# class SpeedTestClient:
#     def __init__(self):
#         self.magic_cookie = 0xabcddcba
#         self.state = ClientState.STARTUP
#         self.server_address = None
#         self.server_tcp_port = None
#         self.server_udp_port = None
#         self.running = True
#
#         # Create UDP socket for receiving broadcasts
#         self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
#         self.udp_socket.bind(('0.0.0.0', 13117))
#
#     def start(self):
#         """Start the client"""
#         while self.running:
#             try:
#                 if self.state == ClientState.STARTUP:
#                     self._get_user_input()
#                     print("Client started, listening for offer requests...")
#                     self.state = ClientState.LOOKING_FOR_SERVER
#
#                 elif self.state == ClientState.LOOKING_FOR_SERVER:
#                     self._wait_for_server()
#
#                 elif self.state == ClientState.SPEED_TEST:
#                     self._run_speed_test()
#                     self.state = ClientState.LOOKING_FOR_SERVER
#
#             except KeyboardInterrupt:
#                 self.running = False
#             except Exception as e:
#                 print(f"Error in main loop: {e}")
#                 time.sleep(1)
#
#     def _get_user_input(self):
#         """Get test parameters from user"""
#         self.file_size = int(input("Enter file size (bytes): "))
#         self.tcp_connections = int(input("Enter number of TCP connections: "))
#         self.udp_connections = int(input("Enter number of UDP connections: "))
#
#     def _wait_for_server(self):
#         """Wait for server offer message"""
#         try:
#             data, addr = self.udp_socket.recvfrom(1024) #waits to receive UDP data, with a maximum buffer size of 1024 bytes
#
#             # Checks if the received data is exactly 9 bytes long
#             if len(data) == 9:  # Magic cookie (4) + type (1) + UDP port (2) + TCP port (2)
#                 cookie, msg_type, udp_port, tcp_port = struct.unpack('!IbHH', data) # parse the binary data into variables
#
#                 # Validates the received message
#                 if cookie == self.magic_cookie and msg_type == 0x2:
#                     self.server_address = addr[0]
#                     self.server_udp_port = udp_port
#                     self.server_tcp_port = tcp_port
#                     print(f"Received offer from {self.server_address}")
#                     self.state = ClientState.SPEED_TEST
#
#         except Exception as e:
#             print(f"Error waiting for server: {e}")
#
#     def _run_speed_test(self):
#         """Run the speed test with multiple connections"""
#         print("Starting speed test...")
#
#
#         threads = []
#         connection_id = 1
#
#         # Start TCP transfers
#         for _ in range(self.tcp_connections):
#             thread = threading.Thread(
#                 target=self._tcp_transfer,
#                 args=(connection_id,)
#             )
#             threads.append(thread)
#             thread.start()
#             connection_id += 1
#
#         # Start UDP transfers
#         for _ in range(self.udp_connections):
#             thread = threading.Thread(
#                 target=self._udp_transfer,
#                 args=(connection_id,)
#             )
#             threads.append(thread)
#             thread.start()
#             connection_id += 1
#
#         # Wait for all transfers to complete
#         for thread in threads:
#             thread.join()
#
#         print("All transfers complete, listening to offer requests...")
#
#     def _tcp_transfer(self, connection_id: int) -> None:
#         """Handle single TCP transfer"""
#         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#
#         try:
#             # Connect and send file size request
#             sock.connect((self.server_address, self.server_tcp_port))
#             sock.send(f"{self.file_size}\n".encode('utf-8'))
#
#
#             start_time = time.perf_counter()
#
#             received = 0
#             buffer = bytearray(min(8192, self.file_size))
#
#             # Loops until all expected bytes are received
#             while received < self.file_size:
#                 view = memoryview(buffer)
#                 chunk_size = sock.recv_into(view, min(8192, self.file_size - received))
#
#                 # Breaks if server closes connection
#                 if not chunk_size:
#                     break
#                 # Updates total bytes received
#                 received += chunk_size
#
#             duration = time.perf_counter() - start_time
#
#             # Avoid division by zero
#             if duration < 0.000001:
#                 duration = 0.000001
#
#
#             speed = (received * 8) / duration  # speed in bits/second
#
#             print(f"TCP transfer #{connection_id} finished, "
#                   f"total time: {duration:.6f} seconds, "
#                   f"total speed: {speed:.2f} bits/second, "
#                   f"bytes received: {received}")
#
#         except Exception as e:
#             print(f"Error in TCP transfer #{connection_id}: {e}")
#         finally:
#             sock.close()
#
#     def _udp_transfer(self, connection_id: int):
#         """Handle single UDP transfer"""
#         try:
#             # Create UDP socket
#             sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#             sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#             sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
#
#             # Send request
#             request = struct.pack('!IbQ',
#                                   self.magic_cookie,
#                                   0x3,
#                                   self.file_size)
#             sock.sendto(request, (self.server_address, self.server_udp_port))
#
#             # Record start time
#             start_time = time.time()
#             last_receive_time = start_time
#
#             # Receive data
#             received_segments: List[bytes] = []
#             received_bytes = 0
#             total_segments = None
#
#             while True:
#                 try:
#                     sock.settimeout(1.0)
#                     data, _ = sock.recvfrom(2048)
#                     last_receive_time = time.time()
#
#                     # Checks if received data has complete header
#                     if len(data) >= 21:  # Magic cookie (4) + type (1) + total segments (8) + current segment (8)
#                         header = struct.unpack('!IbQQ', data[:21])
#                         cookie, msg_type, total_segs, current_seg = header
#
#                         if cookie == self.magic_cookie and msg_type == 0x4:
#                             if total_segments is None:
#                                 total_segments = total_segs
#                                 received_segments = [None] * total_segments
#
#                             # Extracts data payload after header
#                             payload = data[21:]
#                             received_segments[current_seg] = payload
#                             received_bytes += len(payload)
#
#                 except socket.timeout:
#                     if time.time() - last_receive_time >= 1.0:
#                         break
#
#             # Calculate duration, speed and successfully received packets
#             duration = last_receive_time - start_time
#             speed = (received_bytes * 8) / duration  # speed in bits per second
#             packet_success = sum(1 for seg in received_segments if seg is not None) / len(received_segments) * 100
#
#             print(f"UDP transfer #{connection_id} finished, "
#                   f"total time: {duration:.2f} seconds, "
#                   f"total speed: {speed:.2f} bits/second, "
#                   f"percentage of packets received successfully: {packet_success:.1f}%")
#
#         except Exception as e:
#             print(f"Error in UDP transfer #{connection_id}: {e}")
#         finally:
#             sock.close()
#
# if __name__ == "__main__":
#     client = SpeedTestClient()
#     client.start()


#
# import socket
# import struct
# import threading
# import time
# from typing import List, Tuple
# from enum import Enum
#
#
# # Three possible states for the client
# class ClientState(Enum):
#     STARTUP = 1
#     LOOKING_FOR_SERVER = 2
#     SPEED_TEST = 3
#
#
# class SpeedTestClient:
#     def __init__(self):
#         self.magic_cookie = 0xabcddcba
#         self.state = ClientState.STARTUP
#         self.server_address = None
#         self.server_tcp_port = None
#         self.server_udp_port = None
#         self.running = True
#
#         # Create UDP socket for receiving broadcasts
#         self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
#         self.udp_socket.bind(('0.0.0.0', 13117))
#
#     def start(self):
#         """Start the client"""
#         while self.running:
#             try:
#                 if self.state == ClientState.STARTUP:
#                     self._get_user_input()
#                     print("Client started, listening for offer requests...")
#                     self.state = ClientState.LOOKING_FOR_SERVER
#
#                 elif self.state == ClientState.LOOKING_FOR_SERVER:
#                     self._wait_for_server()
#
#                 elif self.state == ClientState.SPEED_TEST:
#                     self._run_speed_test()
#                     self.state = ClientState.LOOKING_FOR_SERVER
#
#             except KeyboardInterrupt:
#                 self.running = False
#             except Exception as e:
#                 print(f"Error in main loop: {e}")
#                 time.sleep(1)
#
#     def _get_user_input(self):
#         """Get test parameters from user"""
#         try:
#             self.file_size = int(input("Enter file size (bytes): "))
#             self.tcp_connections = int(input("Enter number of TCP connections: "))
#             self.udp_connections = int(input("Enter number of UDP connections: "))
#         except ValueError as e:
#             print(f"Invalid input: {e}")
#             self.running = False
#
#     def _wait_for_server(self):
#         """Wait for server offer message"""
#         try:
#             data, addr = self.udp_socket.recvfrom(1024)  # waits to receive UDP data
#
#             if len(data) == 9:  # Magic cookie (4) + type (1) + UDP port (2) + TCP port (2)
#                 cookie, msg_type, udp_port, tcp_port = struct.unpack('!IbHH', data)
#
#                 if cookie == self.magic_cookie and msg_type == 0x2:
#                     self.server_address = addr[0]
#                     self.server_udp_port = udp_port
#                     self.server_tcp_port = tcp_port
#                     print(f"Received offer from {self.server_address}")
#                     self.state = ClientState.SPEED_TEST
#                 else:
#                     print("Invalid message received, ignoring.")
#             else:
#                 print("Received malformed message, ignoring.")
#
#         except socket.timeout:
#             print("Timeout while waiting for server offer.")
#         except Exception as e:
#             print(f"Error waiting for server: {e}")
#
#     def _run_speed_test(self):
#         """Run the speed test with multiple connections"""
#         print("Starting speed test...")
#
#         threads = []
#         connection_id = 1
#
#         # Start TCP transfers
#         for _ in range(self.tcp_connections):
#             thread = threading.Thread(
#                 target=self._tcp_transfer,
#                 args=(connection_id,)
#             )
#             threads.append(thread)
#             thread.start()
#             connection_id += 1
#
#         # Start UDP transfers
#         for _ in range(self.udp_connections):
#             thread = threading.Thread(
#                 target=self._udp_transfer,
#                 args=(connection_id,)
#             )
#             threads.append(thread)
#             thread.start()
#             connection_id += 1
#
#         # Wait for all transfers to complete
#         for thread in threads:
#             thread.join()
#
#         print("All transfers complete, listening to offer requests...")
#
#     def _tcp_transfer(self, connection_id: int) -> None:
#         """Handle single TCP transfer"""
#         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#
#         try:
#             # Connect and send file size request
#             sock.connect((self.server_address, self.server_tcp_port))
#             sock.send(f"{self.file_size}\n".encode('utf-8'))
#
#             start_time = time.perf_counter()
#
#             received = 0
#             buffer = bytearray(min(8192, self.file_size))
#
#             # Loops until all expected bytes are received
#             while received < self.file_size:
#                 view = memoryview(buffer)
#                 chunk_size = sock.recv_into(view, min(8192, self.file_size - received))
#
#                 # Breaks if server closes connection
#                 if not chunk_size:
#                     print(f"Connection closed unexpectedly (TCP) for transfer #{connection_id}.")
#                     break
#                 received += chunk_size
#
#             duration = time.perf_counter() - start_time
#
#             if duration < 0.000001:
#                 duration = 0.000001
#
#             speed = (received * 8) / duration  # speed in bits/second
#
#             print(f"TCP transfer #{connection_id} finished, "
#                   f"total time: {duration:.6f} seconds, "
#                   f"total speed: {speed:.2f} bits/second, "
#                   f"bytes received: {received}")
#
#         except Exception as e:
#             print(f"Error in TCP transfer #{connection_id}: {e}")
#         finally:
#             sock.close()
#
#     def _udp_transfer(self, connection_id: int):
#         """Handle single UDP transfer"""
#         try:
#             sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#             sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#             sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
#
#             request = struct.pack('!IbQ', self.magic_cookie, 0x3, self.file_size)
#             sock.sendto(request, (self.server_address, self.server_udp_port))
#
#             start_time = time.time()
#             last_receive_time = start_time
#
#             received_segments: List[bytes] = []
#             received_bytes = 0
#             total_segments = None
#
#             while True:
#                 try:
#                     sock.settimeout(1.0)
#                     data, _ = sock.recvfrom(2048)
#                     last_receive_time = time.time()
#
#                     if len(data) >= 21:  # Magic cookie (4) + type (1) + total segments (8) + current segment (8)
#                         header = struct.unpack('!IbQQ', data[:21])
#                         cookie, msg_type, total_segs, current_seg = header
#
#                         if cookie == self.magic_cookie and msg_type == 0x4:
#                             if total_segments is None:
#                                 total_segments = total_segs
#                                 received_segments = [None] * total_segments
#
#                             payload = data[21:]
#                             received_segments[current_seg] = payload
#                             received_bytes += len(payload)
#
#                 except socket.timeout:
#                     if time.time() - last_receive_time >= 1.0:
#                         break
#
#             duration = last_receive_time - start_time
#             speed = (received_bytes * 8) / duration  # speed in bits per second
#             packet_success = sum(1 for seg in received_segments if seg is not None) / len(received_segments) * 100
#
#             print(f"UDP transfer #{connection_id} finished, "
#                   f"total time: {duration:.2f} seconds, "
#                   f"total speed: {speed:.2f} bits/second, "
#                   f"percentage of packets received successfully: {packet_success:.1f}%")
#
#         except Exception as e:
#             print(f"Error in UDP transfer #{connection_id}: {e}")
#         finally:
#             sock.close()
#
#
# if __name__ == "__main__":
#     client = SpeedTestClient()
#     client.start()

import socket
import struct
import threading
import time
from typing import List, Tuple
from enum import Enum


# Three possible states for the client
class ClientState(Enum):
    STARTUP = 1
    LOOKING_FOR_SERVER = 2
    SPEED_TEST = 3


class SpeedTestClient:
    def __init__(self):
        self.magic_cookie = 0xabcddcba
        self.state = ClientState.STARTUP
        self.server_address = None
        self.server_tcp_port = None
        self.server_udp_port = None
        self.running = True

        # Create UDP socket for receiving broadcasts
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.bind(('0.0.0.0', 13117))
        self.udp_socket.settimeout(1.0)  # Set a timeout to break out of busy-waiting

    def start(self):
        """Start the client"""
        while self.running:
            try:
                if self.state == ClientState.STARTUP:
                    self._get_user_input()
                    print("Client started, listening for offer requests...")
                    self.state = ClientState.LOOKING_FOR_SERVER

                elif self.state == ClientState.LOOKING_FOR_SERVER:
                    self._wait_for_server()

                elif self.state == ClientState.SPEED_TEST:
                    self._run_speed_test()
                    self.state = ClientState.LOOKING_FOR_SERVER

                time.sleep(0.1)  # Sleep to prevent high CPU usage

            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(1)

    def _get_user_input(self):
        """Get test parameters from user"""
        try:
            self.file_size = int(input("Enter file size (bytes): "))
            self.tcp_connections = int(input("Enter number of TCP connections: "))
            self.udp_connections = int(input("Enter number of UDP connections: "))
        except ValueError as e:
            print(f"Invalid input: {e}")
            self.running = False

    def _wait_for_server(self):
        """Wait for server offer message"""
        try:
            data, addr = self.udp_socket.recvfrom(1024)  # waits to receive UDP data

            if len(data) == 9:  # Magic cookie (4) + type (1) + UDP port (2) + TCP port (2)
                cookie, msg_type, udp_port, tcp_port = struct.unpack('!IbHH', data)

                if cookie == self.magic_cookie and msg_type == 0x2:
                    self.server_address = addr[0]
                    self.server_udp_port = udp_port
                    self.server_tcp_port = tcp_port
                    print(f"Received offer from {self.server_address}")
                    self.state = ClientState.SPEED_TEST
                else:
                    print("Invalid message received, ignoring.")
            else:
                print("Received malformed message, ignoring.")

        except socket.timeout:
            print("Timeout while waiting for server offer.")
        except Exception as e:
            print(f"Error waiting for server: {e}")

    def _run_speed_test(self):
        """Run the speed test with multiple connections"""
        print("Starting speed test...")

        threads = []
        connection_id = 1

        # Start TCP transfers
        for _ in range(self.tcp_connections):
            thread = threading.Thread(
                target=self._tcp_transfer,
                args=(connection_id,)
            )
            threads.append(thread)
            thread.start()
            connection_id += 1

        # Start UDP transfers
        for _ in range(self.udp_connections):
            thread = threading.Thread(
                target=self._udp_transfer,
                args=(connection_id,)
            )
            threads.append(thread)
            thread.start()
            connection_id += 1

        # Wait for all transfers to complete
        for thread in threads:
            thread.join()

        print("All transfers complete, listening to offer requests...")

    def _tcp_transfer(self, connection_id: int) -> None:
        """Handle single TCP transfer"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            # Connect and send file size request
            sock.connect((self.server_address, self.server_tcp_port))
            sock.send(f"{self.file_size}\n".encode('utf-8'))

            start_time = time.perf_counter()

            received = 0
            buffer = bytearray(min(8192, self.file_size))

            # Loops until all expected bytes are received
            while received < self.file_size:
                view = memoryview(buffer)
                chunk_size = sock.recv_into(view, min(8192, self.file_size - received))

                # Breaks if server closes connection
                if not chunk_size:
                    print(f"Connection closed unexpectedly (TCP) for transfer #{connection_id}.")
                    break
                received += chunk_size

            duration = time.perf_counter() - start_time

            if duration < 0.000001:
                duration = 0.000001

            speed = (received * 8) / duration  # speed in bits/second

            print(f"TCP transfer #{connection_id} finished, "
                  f"total time: {duration:.6f} seconds, "
                  f"total speed: {speed:.2f} bits/second, "
                  f"bytes received: {received}")

        except Exception as e:
            print(f"Error in TCP transfer #{connection_id}: {e}")
        finally:
            sock.close()

    def _udp_transfer(self, connection_id: int):
        """Handle single UDP transfer"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            request = struct.pack('!IbQ', self.magic_cookie, 0x3, self.file_size)
            sock.sendto(request, (self.server_address, self.server_udp_port))

            start_time = time.time()
            last_receive_time = start_time

            received_segments: List[bytes] = []
            received_bytes = 0
            total_segments = None

            while True:
                try:
                    sock.settimeout(1.0)
                    data, _ = sock.recvfrom(2048)
                    last_receive_time = time.time()

                    if len(data) >= 21:  # Magic cookie (4) + type (1) + total segments (8) + current segment (8)
                        header = struct.unpack('!IbQQ', data[:21])
                        cookie, msg_type, total_segs, current_seg = header

                        if cookie == self.magic_cookie and msg_type == 0x4:
                            if total_segments is None:
                                total_segments = total_segs
                                received_segments = [None] * total_segments

                            payload = data[21:]
                            received_segments[current_seg] = payload
                            received_bytes += len(payload)

                except socket.timeout:
                    if time.time() - last_receive_time >= 1.0:
                        break

            duration = last_receive_time - start_time
            speed = (received_bytes * 8) / duration  # speed in bits per second
            packet_success = sum(1 for seg in received_segments if seg is not None) / len(received_segments) * 100

            print(f"UDP transfer #{connection_id} finished, "
                  f"total time: {duration:.2f} seconds, "
                  f"total speed: {speed:.2f} bits/second, "
                  f"percentage of packets received successfully: {packet_success:.1f}%")

        except Exception as e:
            print(f"Error in UDP transfer #{connection_id}: {e}")
        finally:
            sock.close()


if __name__ == "__main__":
    client = SpeedTestClient()
    client.start()
