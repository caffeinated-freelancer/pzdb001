import enum
import threading

from loguru import logger

from pz.config import PzProjectConfig
from services.rs232 import Rs232Service


class WorkerState(enum.Enum):
    IDLE = enum.auto()
    SENDING = enum.auto()
    RECEIVING = enum.auto()


workerState = WorkerState.IDLE


def receive_file_worker(rs232: Rs232Service, folder: str):
    global workerState
    workerState = WorkerState.RECEIVING
    rs232.recv_file(folder)
    workerState = WorkerState.IDLE
    logger.info('### 檔案接收完成 ###')


def sending_file_worker(rs232: Rs232Service, filename: str):
    global workerState
    workerState = WorkerState.SENDING
    rs232.send_file(filename)
    workerState = WorkerState.IDLE
    logger.info('### 檔案傳送完成 ###')


class FileTransferService:
    baud_rate = 115200

    config: PzProjectConfig
    workerThread: threading.Thread | None

    def __init__(self, cfg: PzProjectConfig):
        self.config = cfg
        self.workerThread = None

    def check_worker_thread_available(self) -> bool:
        if self.workerThread is not None:
            if self.workerThread.is_alive():
                logger.trace(f'目前檔案傳送接收工作仍在工作中')
                return False
            else:
                logger.trace(f'目前檔案接傳送接收工作已經完成')
                self.workerThread.join()
                self.workerThread = None

        return True

    def receive_file(self):
        if not self.check_worker_thread_available():
            return

        com_port = self.find_com_port()

        if com_port is None:
            logger.info(f'no communication port')
        else:
            rs232 = Rs232Service(com_port, baud_rate=self.baud_rate, timeout=60)
            self.workerThread = threading.Thread(target=receive_file_worker, args=(rs232, self.config.output_folder))
            self.workerThread.start()

    def send_file(self, filename: str):
        if not self.check_worker_thread_available():
            return

        com_port = self.find_com_port()

        if com_port is None:
            logger.info(f'no communication port')
        else:
            rs232 = Rs232Service(com_port, baud_rate=self.baud_rate, timeout=60)
            self.workerThread = threading.Thread(target=sending_file_worker, args=(rs232, filename))
            self.workerThread.start()

    @staticmethod
    def check_com_port() -> str | None:
        ports = Rs232Service.list_com_ports()

        for port in ports:
            if port.manufacturer == 'FTDI' and port.vid == 1027:
                if port.serial_number in ['AB0NEGHSA', 'AB0PQX2SA', 'A10NDAP3A', 'A10NDAP2A']:
                    return port.device
        return None

    @staticmethod
    def find_com_port() -> str:
        ports = Rs232Service.list_com_ports()
        com_port: str | None = None

        for port in ports:
            logger.info(f'{port.name}: [{port.hwid}] {port.description}, VID: {port.vid}, {port.manufacturer}')
            if com_port is None and port.description.startswith('USB Serial Port'):
                com_port = port.device
        return com_port
