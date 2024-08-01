import serial
import serial.tools.list_ports
from loguru import logger
from serial.tools.list_ports_common import ListPortInfo

from toolbox.modem import YModem


class Rs232Global:
    ser: serial.Serial | None = None


def _receive_char(sz: int, timeout: int = 1, debug: bool = False) -> bytes:
    if debug:
        print(f'receiving {sz} bytes')
    return Rs232Global.ser.read(sz)


def _send_char(char: bytes, timeout: int = 1, debug: bool = False) -> int | None:
    if debug:
        print(f'sending {len(char)} bytes')
    return Rs232Global.ser.write(char)


class Rs232Service:
    modem: YModem

    def __init__(self, com_port: str, baud_rate: int = 115200, timeout: int = 60):
        Rs232Global.ser = serial.Serial(com_port, baudrate=baud_rate, parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                                        timeout=timeout, write_timeout=timeout)

        # Close the serial port when finished
        self.modem = YModem(_receive_char, _send_char)

    def __del__(self):
        Rs232Global.ser.close()

    def send_file(self, filename: str):
        self.modem.send(filename)

    def recv_file(self, folder: str):
        r = self.modem.recv(folder)
        if r is not None:
            logger.debug(f'received: {r}')
        else:
            logger.error(f'received: DONE (NONE)')

    @staticmethod
    def list_com_ports() -> list[ListPortInfo]:
        return serial.tools.list_ports.comports()
