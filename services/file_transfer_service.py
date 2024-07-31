import threading

from loguru import logger

from pz.config import PzProjectConfig
from services.rs232 import Rs232Service


def receive_file_worker(rs232: Rs232Service, folder: str):
    print("Starting thread...")
    rs232.recv_file(folder)
    # time.sleep(120)
    print("Thread finished.")


def sending_file_worker(rs232: Rs232Service, filename: str):
    rs232.send_file(filename)


class FileTransferService:
    baud_rate = 115200

    config: PzProjectConfig
    receivingThread: threading.Thread | None
    sendingThread: threading.Thread | None

    def __init__(self, cfg: PzProjectConfig):
        self.config = cfg
        self.receivingThread = None
        self.sendingThread = None

    def receive_file(self):
        if self.receivingThread is not None:
            logger.error("receive_file already running")
            if self.receivingThread.is_alive():
                logger.info(f'目前檔案接收的程式仍在工作中')
                return
            else:
                logger.info(f'目前檔案接收的程式已經結束')
                self.receivingThread.join()
                self.receivingThread = None

        com_port = self.find_com_port()

        if com_port is None:
            logger.info(f'no communication port')
        else:
            rs232 = Rs232Service(com_port, baud_rate=self.baud_rate)
            self.receivingThread = threading.Thread(target=receive_file_worker, args=(rs232, self.config.output_folder))
            self.receivingThread.start()

    def send_file(self, filename: str):
        if self.sendingThread is not None:
            logger.error("send_file already running")
            if self.sendingThread.is_alive():
                logger.info(f'目前檔案傳送的程式仍在工作中')
                return
            else:
                logger.info(f'目前檔案傳送的程式已經結束')
                self.sendingThread.join()
                self.sendingThread = None
        com_port = self.find_com_port()

        if com_port is None:
            logger.info(f'no communication port')
        else:
            rs232 = Rs232Service(com_port, baud_rate=self.baud_rate)
            self.sendingThread = threading.Thread(target=sending_file_worker, args=(rs232, filename))
            self.sendingThread.start()

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
