import struct
SIMP_HEADER_FORMAT = '!BBB32sI'


def pack_simp_header(msg_type: int, msg_op:int, msg_seq:int, user:str, msg_len:int) -> bytes:
    return struct.pack(SIMP_HEADER_FORMAT, msg_type, msg_op, msg_seq, user.encode('ascii'), msg_len)


def unpack_simp_header(data: bytes) -> dict:
    data = struct.unpack(SIMP_HEADER_FORMAT, data)
    return {'msg_type': data[0], 'msg_op': data[1], 'msg_seq': data[2], 'user': (data[3].decode('ascii')).replace('\x00',''), 'msg_len': data[4]}

