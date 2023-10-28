"""Enums for the project."""
from enum import Enum


class MessageType(Enum):
    """Enum for message types."""

    CONTROL = 1
    CHAT = 2


class Operation(Enum):
    """Enum for message operations."""

    CONST = 1
    ERR = 1
    SYN = 2
    ACK = 4
    SYN_ACK = 6
    FIN = 8


class SeqNum(Enum):
    """Enum for sequence numbers."""

    OK = 0
    ERR = 1
