import can
from can import Message
import socket
import struct
import time


class SimVABus(can.bus.BusABC):
    def __init__(self, channel):
        """
        Initialize the SimVABus with a specific channel.
        :param channel: A unique identifier for the communication channel.
        """
        self.simva = SimVA(channel)

    def fileno(self):
        """
        Return the file descriptor of the send socket.
        """
        return self.simva.fileno()

    def recv(self, timeout=None):
        """
        Receive a message from the SimVA device.
        :param timeout: How long to wait for a message before giving up.
        :return: A can.Message object if a message is received; otherwise, None.
        """
        event = self.simva.recv(timeout)
        if isinstance(event, can.Message):
            return event
        return None

    def send(self, msg, timeout=None):
        """
        Send a message to the SimVA device.
        :param msg: The can.Message to send.
        :param timeout: How long to wait for sending the message; not used here.
        """
        self.simva.send(msg)

    def send_periodic(self, message, period, duration=None):
        """
        Send messages periodically - Not implemented.
        :param message: The message to be sent periodically.
        :param period: The period with which to send the message.
        :param duration: How long to continue sending; not used here.
        :return: None
        """
        return None

    def shutdown(self):
        """
        Shutdown the connection with the SimVA device properly.
        """
        self.simva.close()


class SimVA(object):
    SERVER_IP = '127.0.0.1'
    SERVER_PORT = 10001
    RECV_PORT = 10002
    SIZE = 1024
    SIMVA_SEND_ADDR = (SERVER_IP, SERVER_PORT)
    SIMVA_RECV_ADDR = (SERVER_IP, RECV_PORT)

    def __init__(self, channel: int):
        """
        Initialize the SimVA simulation interface.
        :param channel: The specific channel for this instance to listen and send CAN messages.
        """
        print("simva initialized")
        self._send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._send_socket.connect(SimVA.SIMVA_SEND_ADDR)

        self._recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._recv_socket.bind(SimVA.SIMVA_RECV_ADDR)
        self._channel = channel

    def fileno(self):
        """
        Return the file descriptor of the send socket, for integration with select.
        :return: File descriptor of the send socket.
        """
        return self._send_socket.fileno()

    def recv(self, timeout=3):
        """
        Receive a message from the SimVA device within a given timeout.
        :param timeout: The maximum time to wait for an incoming message.
        :return: A CAN message if received within the timeout; otherwise, None.
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
        """
        Send a CAN message via the SimVA interface.
        :param msg: The CAN message to send, containing the arbitration ID and data.
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
        """
        Close the send and receive sockets.
        """
        self._send_socket.close()
        self._recv_socket.close()

    def terminate(self, exc):
        """
        Terminate the SimVA interface and close sockets. 
        :param exc: Exception object if an error occurred leading to termination.
        """
        self.close()

