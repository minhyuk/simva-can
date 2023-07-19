import can
from can import Message
import socket
import struct


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
        self._send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._send_socket.connect(SimVA.SIMVA_SEND_ADDR)

        self._recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._recv_socket.bind(SimVA.SIMVA_RECV_ADDR)

        self._channel = channel

    def fileno(self):
        return self._send_socket.fileno()

    def recv(self, timeout=None):
        msg, addr = self._recv_socket.recvfrom(1024)

        # data 필드의 길이
        data_length = len(msg) - struct.calcsize('<IBB')

        # 패킷의 언패킹을 위한 형식 문자열
        packet_format = f'<IBB{data_length}s'
        # 언패킹
        unpacked_data = struct.unpack(packet_format, msg)

        # 언패킹된 데이터를 각각의 변수에 할당
        arb_id, length, network, data = unpacked_data

        return Message(arbitration_id=arb_id, data=data[:length])

    def send(self, msg:can.Message):
        id = msg.arbitration_id
        data = msg.data
        # data 필드를 bytes 객체로 변환
        data_bytes = bytes(data)
        length = len(data_bytes)
        network = self._channel

        # 패킷을 패킹하기 위한 형식 문자열
        packet_format = f'<IBB{length}s'

        # 패킹
        packed_data = struct.pack(packet_format, id, length, network, data_bytes)

        self._send_socket.send(packed_data)  # 서버에 메시지 전송

    def close(self):
        self._send_socket.close()
        self._recv_socket.close()

    def terminate(self, exc):
        self.close()
