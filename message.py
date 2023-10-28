"""Models for the chat server."""
from dataclasses import dataclass
import struct

from constants import SIMP_HEADER_FORMAT
from enums import MessageType, Operation, SeqNum


@dataclass
class Message:
    """Message model."""

    message_type: MessageType
    message_operation: Operation
    message_sequence: SeqNum = SeqNum.OK
    user: str = ""
    message_length: int = 0
    message: str = ""

    def _pack_simp_header(self) -> bytes:
        """Packs the header."""
        return struct.pack(
            SIMP_HEADER_FORMAT,
            self.message_type.value,
            self.message_operation.value,
            self.message_sequence.value,
            self.user.encode("ascii"),
            self.message_length,
        )

    def pack_simp_message(self) -> bytes:
        """Packs the message."""
        return self._pack_simp_header() + self.message.encode("ascii")

    def __str__(self) -> str:
        """Prints the message."""
        return f"[{self.user}]: {self.message}"

    @classmethod
    def unpack_message(cls, data: bytes) -> "Message":
        """Unpacks the header."""

        def _unpack_data(data: bytes) -> tuple[bytes, bytes]:
            header = data[:39]
            message_text = data[39:]
            return header, message_text

        header, message_text = _unpack_data(data)
        header: tuple[int, int, int, str, int] = struct.unpack(
            SIMP_HEADER_FORMAT, header
        )
        return cls(
            message_type=MessageType(header[0]),
            message_operation=Operation(header[1]),
            message_sequence=SeqNum(header[2]),
            user=(header[3].decode("ascii")).replace("\x00", ""),
            message_length=header[4],
            message=message_text.decode("ascii"),
        )
