"""Server module, holds the main functionality of the server"""
import socket
import sys
import typing


from constants import EXIT_MESSAGES, MESSAGE_SIZE, TIMEOUT
from message import Message
from enums import MessageType, Operation, SeqNum


class Server:
    """
    Server class, holds the main functionality of the server
    """

    busy_message_text = "Server is busy"
    reject_message_text = "Connection rejected"

    def __init__(self, host: str, port: int, timeout: int = TIMEOUT) -> None:
        self.host = host
        self.port = port
        self.name = ""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        self.allowed_address: typing.Tuple[str, int] = None
        self.socket.bind((self.host, self.port))
        self.connected = False

    @staticmethod
    def show_usage() -> None:
        """
        Shows the usage of the program
        """
        print("Usage: py/python3 simp_server.py <host> <port>")

    def recieve_message(self) -> Message:
        """
        Recieves the message from the client
        Unpacks the message and returns it

        Returns:
            Message: message object created from the recieved message
        """
        data, addr = self.socket.recvfrom(1024)
        if addr not in (self.allowed_address, (self.host, self.port)):
            self.busy(addr)
        else:
            return Message.unpack_message(data)

    def send_message(self, message: Message, address: typing.Tuple[str, int]) -> None:
        """Sends the message."""
        self.socket.sendto(message.pack_simp_message(), address)

    def busy(self, addr: typing.Tuple[str, int]) -> None:
        """
        Rejects the connection
        Args:
            addr (tuple[str, int]): the address of the client
        """
        self.send_message(
            Message(
                message_type=MessageType.CONTROL,
                message_operation=Operation.ERR,
                user=self.name,
                message_length=len(self.busy_message_text),
                message=self.busy_message_text,
            ),
            addr,
        )

    def reject(self, addr: typing.Tuple[str, int]) -> None:
        """
        Rejects the connection
        Args:
            addr (tuple[str, int]): the address of the client
        """
        reject_message = Message(
            message_type=MessageType.CONTROL,
            message_operation=Operation.ERR,
            user=self.name,
            message_length=len(self.reject_message_text),
            message=self.reject_message_text,
        )
        self.send_message(reject_message, addr)

    def quit(self) -> None:
        """
        Sends a quit message to the client
        """
        self.send_message(
            Message(
                message_type=MessageType.CONTROL,
                message_operation=Operation.FIN,
                user=self.name,
            ),
            self.allowed_address,
        )
        message = self.recieve_message()
        if (
            message.message_type == MessageType.CONTROL
            and message.message_operation == Operation.ACK
        ):
            print("Connection ended")
            sys.exit(0)

    def send_chat_message(self, message: Message) -> None:
        """
        Sends a chat message to the client
        Waits for the ACK message from the client
        If no ACK message is recieved, resends the message

        Args:
            message (Message): message object
        """
        try:
            self.send_message(message, self.allowed_address)

            message = self.recieve_message()
            if (
                message.message_type == MessageType.CONTROL
                and message.message_operation == Operation.ACK
            ):  # if ACK, confirm that the message get to the destination
                return
        except socket.timeout:
            print("No response from the server, resending the message")
            message.message_sequence = SeqNum.ERR
            self.send_chat_message(message)

    def _send_ack_message(self) -> None:
        """Creates and sends an ACK message to the client"""
        self.send_message(
            Message(
                message_type=MessageType.CONTROL,
                message_operation=Operation.ACK,
                user=self.name,
            ),
            self.allowed_address,
        )

    def handle_control_message(self, message: Message) -> None:
        """
        Handles the control messages

        Args:
            message (Message): message object
        """
        if message.message_operation == Operation.FIN:
            print("Client closed the connection")
            self._send_ack_message()
            sys.exit(0)
        elif message.message_operation == Operation.ERR:
            print(f"ERROR! {message.message}")
            sys.exit(1)

    def start(self) -> None:
        """
        Holds the main loop of the server
        """
        self.name = input("Enter your name: ")
        print(f"Welcome {self.name}")
        print(f"Listening on {self.host}:{self.port}")
        while self.allowed_address is None:
            try:
                data, addr = self.socket.recvfrom(MESSAGE_SIZE)
                message = Message.unpack_message(data)
                if (
                    message.message_type == MessageType.CONTROL
                    and message.message_operation == Operation.SYN
                ):
                    self.connect(addr)
                else:
                    pass
            except socket.timeout:
                pass

    def connect(self, addr: typing.Tuple[str, int]) -> None:
        """
        Performs the connection with the client
        Server can aslo reject the connection

        Args:
            addr (typing.Tuple[str, int]): _description_
        """
        print(f"{addr} is trying to connect")
        accept = input("Do you want to accept the connection? (y/n): ")
        if accept != "y":
            self.reject(addr)
        self.allowed_address = addr
        self.connected = True
        self.send_message(
            Message(
                message_type=MessageType.CONTROL,
                message_operation=Operation.SYN_ACK,
                user=self.name,
            ),
            self.allowed_address,
        )
        message = self.recieve_message()
        if message.message_operation == Operation.ACK:
            self.chat()

    def chat(self) -> None:
        """
        chating funcitonality, chat starts with the message from client
        """
        print("Chatting with ", self.allowed_address)
        while True:
            try:
                message = self.recieve_message()
                while (
                    message is None
                ):  # if the message was from an unallowed address, ignore it
                    message = self.recieve_message()
                self._send_ack_message()
                if (
                    message.message_type == MessageType.CONTROL
                ):  # if the message is a control message, handle it
                    self.handle_control_message(message)
                elif (
                    message.message_type == MessageType.CHAT
                ):  # if the message is a chat message, print it
                    print(message)
                    message = input(
                        "Enter your message: "
                    ).strip()  # get the message from the user
                    if (
                        message in EXIT_MESSAGES
                    ):  # if the user wants to quit, send the quit message
                        self.quit()
                    message = Message(
                        message_type=MessageType.CHAT,
                        message_operation=Operation.CONST,
                        user=self.name,
                        message_length=len(message),
                        message=message,
                    )
                    self.send_chat_message(message)  # send the message
            except socket.timeout:
                pass  # if there is no message, wait for the next one


if __name__ == "__main__":
    if len(sys.argv) != 3:
        Server.show_usage()
        sys.exit(1)

    server = Server(sys.argv[1], int(sys.argv[2]))
    server.start()
