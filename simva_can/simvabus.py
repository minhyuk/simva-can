import can
from can import Message
import socket
import struct
import time

class SimVABus(can.bus.BusABC):
    def __init__(self, channel):
        """Initialize the SimVABus with a specific channel.
        
        Args:
            channel: an integer representing the channel used for communication.
        """
        self.simva = SimVA(channel)

    def fileno(self):
        """Retrieve the file descriptor of the send socket."""
        return self.simva.fileno()

    def recv(self, timeout=None):
        """Receive a message with an optional timeout.
        
        Args:
            timeout: The maximum time in seconds to wait for a message. If None, wait indefinitely.
            
        Returns:
            A can.Message object if a message is received within the timeout period, None otherwise.
        """
        event = self.simva.recv(timeout)
        if isinstance(event, can.Message):
            return event
        return None

    def send(self, msg, timeout=None):
        """Send a message.
        
        Args:
            msg: The can.Message object to be sent.
            timeout: (unused) for compatibility with base class, but not implemented.
        """
        self.simva.send(msg)

    def send_periodic(self, message, period, duration=None):
        """This method is not implemented. It returns None by default.
        
        Args:
            message: The message to be sent periodically.
            period: The period between messages.
            duration: (Optional) How long to send messages for.
            
        Returns:
            None
        """
        return None

    def shutdown(self):
        """Closes the socket connection."""
        self.simva.close()


class SimVA(object):
    SERVER_IP = '127.0.0.1'
    SERVER_PORT = 10001
    RECV_PORT = 10002
    SIZE = 1024
    SIMVA_SEND_ADDR = (SERVER_IP, SERVER_PORT)
    SIMVA_RECV_ADDR = (SERVER_IP, RECV_PORT)

    def __init__(self, channel: int):
        """Initialize the SimVA connection.
        
        Args:
            channel: The channel to be used for the SimVA communication.
        """
        print("simva initialized")
        self._send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._send_socket.connect(SimVA.SIMVA_SEND_ADDR)

        self._recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._recv_socket.bind(SimVA.SIMVA_RECV_ADDR)
        self._channel = channel

    def fileno(self):
        """Return the file descriptor of the send socket."""
        return self._send_socket.fileno()

    def recv(self, timeout=3):
        """Receive a message with an optional timeout.
        
        Args:
            timeout: The maximum time in seconds to wait before giving up.
            
        Returns:
            A can.Message object if a message is received within the timeout period, else returns None.
        """
        current_time = time.time()
        while True:
            if timeout is not None:
                if time.time() - current_time > timeout:
                    return None
                
            # simva always send 70 bytes for each message
            msg, addr = self._recv_socket.recvfrom(70)

            data_length = len(msg) - struct.calcsize('<IBB')
            packet_format = f'<IBB{data_length}s'
            
            unpacked_data = struct.unpack(packet_format, msg)

            arb_id, length, channel, data = unpacked_data
            if self._channel == channel:
                return Message(arbitration_id=arb_id, data=data[:length])
            else:
                # wait for next message
                continue

    def send(self, msg:can.Message):
        """Send a message.
        
        Args:
            msg: The can.Message object to be sent.
        """
        id = msg.arbitration_id
        data = msg.data

        data_bytes = bytes(data)
        length = len(data_bytes)
        channel = self._channel

        packet_format = f'<IBB{length}s'

        packed_data = struct.pack(packet_format, id, length, channel, data_bytes)

        self._send_socket.send(packed_data)

    def close(self):
        """Closes both the send and receive sockets."""
        self._send_socket.close()
        self._recv_socket.close()

    def terminate(self, exc):
        """Terminates the connection and cleans up resources.
        
        Args:
            exc: The exception that caused termination, for logging or handling purposes.
        """
        self.close()


