import socket
import sys
from header import *


class Server:
    def __init__(self, host: str, port: int, timeout: int = 5) -> None:
        self.host = host
        self.port = port
        self.name = None
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.settimeout(timeout)
        self.allowed_address = None
        self.s.bind((self.host, self.port))

    def recieve_message(self) -> tuple[dict, str]:
        """
        Recieves the message and structures it into a tuple with the header and the message
        :param self:
        :return: tuple[dict, str], touple with the header data as a dictioanry and the message as a string
        """
        data, addr = self.s.recvfrom(1024)  # recieves the message
        if addr != self.allowed_address and addr != (
            self.host,
            self.port,
        ):  # checks if the message is from the allowed address
            self.busy(addr)  # rejects the connection
        else:
            header = data[:39]  # 39 is the size of the header
            message = data[39:].decode("ascii")  # decodes the message
            header = unpack_simp_header(header)  # unpacks the header
            return (header, message)

    def send_control_message(self, msg_op: int, message: str = "") -> None:
        """
        Sends a control message to the server
        Args:
            msg_op (int): message operation, 1 for error, 2 for syn, 4 for acknowledgement, 8 for ending
            message (str, optional): in case of error, it will be an error message. Defaults to ''.
        """
        header = pack_simp_header(
            msg_type=1, msg_op=msg_op, msg_seq=0, user=self.name, msg_len=len(message)
        )
        message = header + message.encode("ascii")
        self.s.sendto(message, self.allowed_address)

    def busy(self, addr: tuple[str, int]) -> None:
        """
        Rejects the connection
        Args:
            addr (tuple[str, int]): the address of the client
        """
        message = "Server is busy"
        header = pack_simp_header(
            msg_type=1, msg_op=1, msg_seq=0, user=self.name, msg_len=len(message)
        )
        message = header + message.encode("ascii")
        self.s.sendto(message, addr)

    def reject(self, addr: tuple[str, int]) -> None:
        """
        Rejects the connection
        Args:
            addr (tuple[str, int]): the address of the client
        """
        header = pack_simp_header(
            msg_type=1, msg_op=8, msg_seq=0, user=self.name, msg_len=0
        )
        self.s.sendto(header, addr)
    
    def quit(self) -> None:
        """
        Sends a quit message to the client
        """
        header = pack_simp_header(
            msg_type=1, msg_op=8, msg_seq=0, user=self.name, msg_len=0
        )
        self.s.sendto(header, self.allowed_address)
        header, _ = self.recieve_message()
        if header["msg_op"] == 4:
            print("Connection ended")
            quit(0)
    
    def send_chat_message(self, message: str, msg_seq: int = 0) -> None:
        """
        generates a chat message and sends it to the client, then waits for the ACK. if no ACK, resends the message
        Args:
            message (str): message that must be sent
            msg_seq (int, optional): sequence that indicates if it is the original message or not. Defaults to 0.
        """
        header = pack_simp_header(
            msg_type=2,
            msg_op=1,
            msg_seq=msg_seq,
            user=self.name,
            msg_len=len(message),
        )
        try:
            self.s.sendto(header + message.encode("ascii"), self.allowed_address)
            header, _ = self.recieve_message()
            if (
                header["msg_op"] == 4
            ):  # if ACK, confirm that the message get to the destination
                return
        except socket.timeout:
            print("No response from the server, resending the message")
            self.send_chat_message(message, 1)

    def handle_control_message(self, header: dict, message: str) -> None:
        """
        handles the control messages
        Args:
            header (dict): header of the message, holds the message type, operation, sequence, user and length
            message (str): 
        """
        if header["msg_op"] == 1:
            print("Error: ", message)
        if header["msg_op"] == 8:
            self.send_control_message(4)
            print("Connection ended")
            quit(0)

    def start(self) -> None:
        """
        Holds the main loop of the server
        """
        self.name = input("Enter your name: ")
        print("Hello ", self.name)
        print("Listening on ", self.host, ":", self.port)
        while not self.allowed_address:
            try:
                data, addr = self.s.recvfrom(1024)
                header = data[:39]
                header = unpack_simp_header(header)
                if (
                    header["msg_type"] == 1
                    and header["msg_op"] == 2
                    and self.allowed_address == None
                ):
                    self.connect(addr)
                else:
                    pass
            except socket.timeout:
                pass

    def connect(self, addr: tuple[str, int]) -> None:
        """
        Sends a syn message to the client
        Args:
            addr (tuple[str, int]): the address of the client
        """
        print(f"{addr} is trying to connect")
        accept = input("Do you want to accept the connection? (y/n): ")
        if accept == "y":
            self.allowed_address = addr
            self.connected = True
            self.send_control_message(6)  # SYN+ACK
            header, _ = self.recieve_message()  # waits for the ACK
            if header["msg_op"] == 4:  # if ACK, chat start
                self.chat()
        else:
            self.reject(addr)

    def chat(self) -> None:
        """
        chating funcitonality, chat starts with the message from client
        """
        print("Chatting with ", self.allowed_address)
        while True:
            try:

                message = self.recieve_message()
                while message is None:  # if the message was from an unallowed address, ignore it
                    message = self.recieve_message()
                header, message = message  # unpacks the message
                # if you want to check the Stop and Wait functionality, comment the next line
                self.send_control_message(4)  # sends the ACK
                if header["msg_type"] == 1:  # if the message is a control message, handle it
                    self.handle_control_message(header, message)
                elif header["msg_type"] == 2:  # if the message is a chat message, print it
                    print(f'[{header["user"]}] {message}')
                    message = input("Enter your message: ")  # get the message from the user
                    if message in ["exit", "quit", "close", "bye"]:  # if the user wants to quit, send the quit message
                        self.quit()
                    self.send_chat_message(message)  # send the message
            except socket.timeout:
                pass  # if there is no message, wait for the next one


def show_usage() -> None:
    print("Usage: py/python3 simp_server.py <host> <port>")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        show_usage()
        exit(1)

    server = Server(sys.argv[1], int(sys.argv[2]))
    server.start()
