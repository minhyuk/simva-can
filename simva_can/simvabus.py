import can
from can import Message
import socket
import struct
import time


class SimVABus(can.bus.BusABC):
    def __init__(self, channel):
        self.simva = SimVA(channel)

    def fileno(self):
        return self.simva.fileno()

    def recv(self, timeout=None):
        event = self.simva.recv(timeout)
        if isinstance(event, can.Message):
            return event
        return None

    def send(self, msg, timeout=None):
        self.simva.send(msg)

    def send_periodic(self, message, period, duration=None):
        return None

    def shutdown(self):
        self.simva.close()


class SimVA(object):
    SERVER_IP = '127.0.0.1'
    SERVER_PORT = 10001
    RECV_PORT = 10002
    SIZE = 1024
    SIMVA_SEND_ADDR = (SERVER_IP, SERVER_PORT)
    SIMVA_RECV_ADDR = (SERVER_IP, RECV_PORT)

    def __init__(self, channel: int):
        print("simva initialized")
        self._send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._send_socket.connect(SimVA.SIMVA_SEND_ADDR)

        self._recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._recv_socket.bind(SimVA.SIMVA_RECV_ADDR)
        self._channel = channel

    def fileno(self):
        return self._send_socket.fileno()

    def recv(self, timeout=3):
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
        id = msg.arbitration_id
        data = msg.data

        data_bytes = bytes(data)
        length = len(data_bytes)
        channel = self._channel

        packet_format = f'<IBB{length}s'

        packed_data = struct.pack(packet_format, id, length, channel, data_bytes)

        self._send_socket.send(packed_data)

    def close(self):
        self._send_socket.close()
        self._recv_socket.close()

    def terminate(self, exc):
        self.close()
