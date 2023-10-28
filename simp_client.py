"""Client implementation for the SIMP protocol."""
import socket
import sys
import typing

from message import Message
from enums import MessageType, Operation, SeqNum
from constants import EXIT_MESSAGES, MESSAGE_SIZE, TIMEOUT


class Client:
    """Client implementation for the SIMP protocol."""

    def __init__(self, host: str, port: int, timeout: int = TIMEOUT):
        self.host = host
        self.port = port
        self.name: str = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        self.connected = False

    @staticmethod
    def show_usage() -> None:
        """Shows the usage of the program."""
        print("Usage: py/python3 simp_client.py <host> <port>")

    def start(self) -> None:
        """Starts the client."""
        self.name = input("Enter your name: ")
        print("Hello ", self.name)
        self.three_way_handshake()
        while self.connected:
            self.chat()

    def three_way_handshake(self) -> None:
        """Performs the three way handshake."""
        self.send_message(
            Message(
                message_type=MessageType.CONTROL,
                message_operation=Operation.SYN,
                user=self.name,
            )
        )
        try:
            message = self.receive_message()
        except ConnectionResetError:
            print("Server not available!")
            sys.exit(1)
        except socket.timeout:
            pass
        self.handle_control_message(message)
        if self.connected:
            self.chat()

    def chat(self) -> None:
        """Performs the chat."""
        while self.connected:
            message = input("Enter your message: ")
            if message in EXIT_MESSAGES:
                self.close_connection()
            message = Message(
                message_type=MessageType.CHAT,
                message_operation=Operation.CONST,
                user=self.name,
                message_length=len(message),
                message=message,
            )
            self.send_chat_message(message)
            print("Waiting for response...")
            while True:
                try:
                    received_message = self.receive_message()
                    break
                except socket.timeout:
                    pass
            self._send_ack_message()
            if received_message.message_sequence == SeqNum.ERR:
                print(
                    "There was an error sending the message, but eventually it was sent"
                )
            if received_message.message_type == MessageType.CHAT:
                print(received_message)
            elif received_message.message_type == MessageType.CONTROL:
                self.handle_control_message(received_message)

    def close_connection(self) -> None:
        """Closes the connection."""
        self.send_message(
            Message(
                message_type=MessageType.CONTROL,
                message_operation=Operation.FIN,
                user=self.name,
            )
        )
        message = self.receive_message()
        if (
            message.message_type == MessageType.CONTROL
            and message.message_operation == Operation.ACK
        ):
            print("Closing connection")
            self.connected = False
            sys.exit(0)

    def receive_message(self) -> typing.Optional[Message]:
        """Receive a message from the server and unpacks it."""

        data, addr = self.socket.recvfrom(MESSAGE_SIZE)
        if addr != (self.host, self.port):
            print("Received a message from an unknown source")  # Unlikely to happen
            sys.exit(1)

        message = Message.unpack_message(data)
        return message

    def send_message(self, message: Message) -> None:
        """Send a message to the server."""
        self.socket.sendto(message.pack_simp_message(), (self.host, self.port))

    def send_chat_message(self, message: Message) -> None:
        """
        Sends a chat message to the server and waits for an ACK message.
        If no ACK message is recieved, resends the message.

        Args:
            message (Message): message object

        """
        self.send_message(message)
        try:
            ack_message = self.receive_message()
            if (
                ack_message.message_type == MessageType.CONTROL
                and ack_message.message_operation == Operation.ACK
            ):
                return True
        except socket.timeout:
            print("Server timed out, retrying...")
            message.message_sequence = SeqNum.ERR
            self.send_chat_message(message)

    def handle_control_message(self, message: Message) -> typing.Optional[bool]:
        """
        Handles the control messages.

        Args:
            message (Message): message object
        """
        if (
            message.message_type == MessageType.CONTROL
            and message.message_operation == Operation.FIN
        ):
            print("Server closed the connection")
            if self.connected:
                self._handle_fin_message()
                return False
        elif (
            message.message_type == MessageType.CONTROL
            and message.message_operation == Operation.SYN_ACK
        ):
            self._handle_syn_message()
            return True
        elif (
            message.message_type == MessageType.CONTROL
            and message.message_operation == Operation.ERR
        ):
            print("Server error:", message.message)
            sys.exit(1)
        elif (
            message.message_type == MessageType.CONTROL
            and message.message_operation == Operation.ACK
        ):
            return True

    def _send_ack_message(self) -> None:
        """Sends an ACK message to the server."""
        self.send_message(
            Message(
                message_type=MessageType.CONTROL,
                message_operation=Operation.ACK,
                user=self.name,
            )
        )

    def _handle_fin_message(self) -> None:
        """Handles the FIN message from the server."""
        self._send_ack_message()
        self.connected = False
        sys.exit(0)

    def _handle_syn_message(self) -> None:
        """Handles the SYN message from the server."""
        self._send_ack_message()
        self.connected = True
        print("Connection established")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        Client.show_usage()
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    client = Client(host, port)
    client.start()
