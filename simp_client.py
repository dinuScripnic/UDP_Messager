import socket
import sys
from header import *


class Client:
    def __init__(self, host: str, port: int, timeout: int = 5):
        self.host = host
        self.port = port
        self.name = None
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.settimeout(timeout)
        self.connected = False

    def recieve_message(self) -> tuple[dict, str]:
        """
        Recieves the message and structures it into a tuple with the header and the message
        :param self:
        :return: tuple[dict, str], touple with the header data as a dictioanry and the message as a string
        """
        try:
            data, addr = self.s.recvfrom(1024)
            if addr != (self.host, self.port):
                print(
                    "Recieved a message from an unknown source"
                )  # just in case, that will never happen
                exit(1)  # exits the program with error code
            header = data[:39]  # 39 is the size of the header
            message = data[39:].decode("ascii")
            header = unpack_simp_header(header)
            return (header, message)
        except socket.timeout:
            pass

    def send_control_message(self, msg_op: int, message: str = "") -> None:
        """
        Sends a control message to the server
        Args:
            msg_op (int): message operation, 1 for error, 2 for syn, 4 for acknowledgement, 8 for ending
            message (str, optional): in case of error, it will be an error message. Defaults to ''.
        """
        header = pack_simp_header(
            msg_type=1, msg_op=msg_op, msg_seq=0, user=self.name, msg_len=len(message)
        )  # creates the header
        message = header + message.encode("ascii")  # creates the whole message
        self.s.sendto(message, (self.host, self.port))  # sends the message

    def send_chat_message(self, message: str, sequence: int = 0) -> None:
        """
        Sends a chat message to the server
        Args:
            message (str): message to be sent
            sequence (int, optional): Sequence number, in case the server doesnt recieve and respond with an ACK, seq will be changed to 1. Defaults to 0.
        """
        header = pack_simp_header(
            msg_type=2, msg_op=1, msg_seq=sequence, user=self.name, msg_len=len(message)
        )  # creates the header
        self.s.sendto(header + message.encode("ascii"), (self.host, self.port))  # sends the message
        try:
            header, message = self.recieve_message()  # waits for the acknowledgement
            if (
                header["msg_type"] == 1 and header["msg_op"] == 4
            ):  # if the server sends an ACK
                return  # message got to the server
        except socket.timeout:  # if timeout occures
            print("Server timed out, retrying...")  # informs the user
            self.send_chat_message(message, 1)  # resends the message

    def handle_control_message(self, header: dict, message: str) -> None:
        """
        Handles the control messages
        Args:
            header (dict): header of the message
            message (str): message itself
        """
        if (
            header["msg_type"] == 1 and header["msg_op"] == 8
        ):  # if the server wants to close the connection
            print("Server closed the connection")
            if self.connected:  # if the client is connected
                self.send_control_message(4)  # sends the ACK
            quit(0)  # exits the program
        elif header["msg_type"] == 1 and header["msg_op"] == 6:  # if the server SYN+ACK
            self.send_control_message(4)  # sends the ACK
            self.connected = True  # sets the connected flag to true
            print("Connection established")
        elif (
            header["msg_type"] == 1 and header["msg_op"] == 1
        ):  # if the server sends an error message, like server busy
            quit(1)  # exits the program with an error code
        elif (
            header["msg_type"] == 1 and header["msg_op"] == 4
        ):  # if the server sends an ACK
            pass  # server got the message

    def three_way_handshake(self) -> None:
        """
        Implementation of the 3 way handshake
        """
        self.send_control_message(msg_op=2)  # sends the syn message
        header, message = self.recieve_message()  # waits for the acknowledgement
        self.handle_control_message(header, message)
        if self.connected:
            self.chat()

    def chat(self) -> None:
        """
        Chating functionality
        """
        while self.connected:
            message = input("Enter your message: ")
            if message in ["exit", "quit", "close", "bye"]:
                self.send_control_message(msg_op=8)  # sends the FIN message
                (
                    header,
                    message,
                ) = self.recieve_message()  # waits for the acknowledgement
                if header["msg_type"] == 1 and header["msg_op"] == 4:
                    print("Closing connection")  # informs the user
                    self.connected = False  # sets the connected flag to false
                    quit(0)  # exits the program
            self.send_chat_message(message)  # sends the message
            header, message = self.recieve_message()  # waits for the message
            # If you want to check Stop and Wait, comment the next line
            self.send_control_message(4)  # sends the ACK 
            if header["msg_type"] == 2:
                print(f'[{header["user"]}] {message}')  # prints the message
            elif header["msg_type"] == 1:
                self.handle_control_message(header, message)

    def start(self) -> None:
        """
        Holds the main loop of the client
        """
        self.name = input("Enter your name: ")
        print("Hello ", self.name)
        self.three_way_handshake()
        while self.connected:
            self.chat()


def show_usage() -> None:
    print("Usage: py/python3 simp_client.py <host> <port>")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        show_usage()
        exit(1)

    client = Client(sys.argv[1], int(sys.argv[2]))
    client.start()
