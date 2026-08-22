"""
Unit tests for MAX binary protocol packing, unpacking, and compression.
"""
import unittest
from maxlib.protocol import (
    API_VERSION,
    CMD_REQUEST,
    HEADER_SIZE,
    Opcode,
    pack_packet,
    unpack_packet_header,
    unpack_packet_payload,
)


class TestProtocol(unittest.TestCase):
    def test_pack_unpack_small_packet(self):
        payload = {"text": "hello", "chatId": 12345}
        packed = pack_packet(Opcode.MSG_SEND, payload, seq=42)

        self.assertGreater(len(packed), HEADER_SIZE)

        api, cmd, seq, opcode, comp_flag, payload_len = unpack_packet_header(packed[:HEADER_SIZE])
        self.assertEqual(api, API_VERSION)
        self.assertEqual(cmd, CMD_REQUEST)
        self.assertEqual(seq, 42)
        self.assertEqual(opcode, int(Opcode.MSG_SEND))
        self.assertEqual(comp_flag, 0)
        self.assertEqual(payload_len, len(packed) - HEADER_SIZE)

        unpacked = unpack_packet_payload(packed[HEADER_SIZE:], comp_flag=comp_flag)
        self.assertEqual(unpacked, payload)

    def test_pack_unpack_compressed_packet(self):
        # Large repeated payload to trigger compression (> 32 bytes)
        payload = {"data": "A" * 1000, "numbers": list(range(200))}
        packed = pack_packet(Opcode.PROFILE, payload, seq=99, compress=True)

        api, cmd, seq, opcode, comp_flag, payload_len = unpack_packet_header(packed[:HEADER_SIZE])
        self.assertEqual(seq, 99)
        self.assertEqual(opcode, int(Opcode.PROFILE))

        unpacked = unpack_packet_payload(packed[HEADER_SIZE:], comp_flag=comp_flag)
        self.assertEqual(unpacked, payload)

    def test_empty_payload(self):
        packed = pack_packet(Opcode.PING, None, seq=1)
        api, cmd, seq, opcode, comp_flag, payload_len = unpack_packet_header(packed[:HEADER_SIZE])
        self.assertEqual(opcode, int(Opcode.PING))
        unpacked = unpack_packet_payload(packed[HEADER_SIZE:], comp_flag=comp_flag)
        self.assertEqual(unpacked, {})


if __name__ == "__main__":
    unittest.main()
