"""
Binary protocol packet encoder, decoder, and compressor for MAX mobile API.
"""
import struct
from typing import Any, Optional, Tuple
import msgpack

from .constants import (
    API_VERSION,
    CMD_REQUEST,
    HEADER_SIZE,
    HEADER_STRUCT,
    MAX_DECOMPRESSED_SIZE,
    MIN_COMPRESS_LENGTH,
)

# Optional compression backends
try:
    import lz4.block as _lz4_block
except ImportError:
    _lz4_block = None

try:
    import zstandard as _zstandard
    _zstd_compressor = _zstandard.ZstdCompressor(level=3)
    _zstd_decompressor = _zstandard.ZstdDecompressor()
except ImportError:
    _zstandard = None
    _zstd_compressor = None
    _zstd_decompressor = None


def compress_payload(raw: bytes, method: str = "lz4") -> Tuple[bytes, int]:
    """
    Compresses raw payload using LZ4 (default) or ZSTD if available and beneficial.
    Returns (compressed_bytes, flag_value). Flag 0 means uncompressed.
    """
    if len(raw) < MIN_COMPRESS_LENGTH:
        return raw, 0

    if method == "lz4" and _lz4_block is not None:
        try:
            compressed = _lz4_block.compress(raw, store_size=False)
            if len(compressed) < len(raw):
                # Calculate compression ratio flag (matches official Android MAX client protocol)
                flag = (len(raw) // len(compressed)) + 1
                return compressed, min(flag, 0xFF)
        except Exception:
            pass

    elif method == "zstd" and _zstd_compressor is not None:
        try:
            compressed = _zstd_compressor.compress(raw)
            if len(compressed) < len(raw):
                flag = (len(raw) // len(compressed)) + 1
                return compressed, min(flag, 0xFF)
        except Exception:
            pass

    return raw, 0


def decompress_payload(body: bytes, uncompressed_size_hint: Optional[int] = None) -> bytes:
    """
    Decompresses LZ4 or Zstandard compressed payload buffer.
    """
    if not body:
        return body

    # Try LZ4 block decompression
    if _lz4_block is not None:
        try:
            # We try uncompressed sizes starting from reasonable buffer up to MAX_DECOMPRESSED_SIZE
            hint = uncompressed_size_hint or (len(body) * 16)
            hint = min(max(hint, 65536), MAX_DECOMPRESSED_SIZE)
            return _lz4_block.decompress(body, uncompressed_size=hint)
        except Exception:
            pass

    # Try Zstandard decompression
    if _zstd_decompressor is not None:
        try:
            return _zstd_decompressor.decompress(body, max_output_size=MAX_DECOMPRESSED_SIZE)
        except Exception:
            pass

    return body


def pack_packet(
    opcode: int,
    payload: Any = None,
    *,
    seq: int = 0,
    cmd: int = CMD_REQUEST,
    api_version: int = API_VERSION,
    compress: bool = True,
) -> bytes:
    """
    Packs an opcode and payload into binary MAX protocol wire format:
    Header: >BBHHI (10 bytes)
    Body: msgpack-encoded payload (optionally LZ4-compressed)
    """
    raw_payload = msgpack.packb(payload if payload is not None else {}, use_bin_type=True)
    body = raw_payload
    flag = 0

    if compress and len(raw_payload) >= MIN_COMPRESS_LENGTH:
        body, flag = compress_payload(raw_payload, method="lz4")

    body_len = len(body)
    packed_len = ((flag & 0xFF) << 24) | (body_len & 0xFFFFFF)
    header = struct.pack(HEADER_STRUCT, api_version, cmd, seq & 0xFFFF, int(opcode) & 0xFFFF, packed_len)
    return header + body


def unpack_packet_header(header_bytes: bytes) -> Tuple[int, int, int, int, int, int]:
    """
    Unpacks 10-byte packet header.
    Returns: (api_version, cmd, seq, opcode, comp_flag, payload_len)
    """
    if len(header_bytes) < HEADER_SIZE:
        raise ValueError(f"Packet header too short ({len(header_bytes)} < {HEADER_SIZE})")

    api, cmd, seq, opcode, packed_len = struct.unpack(HEADER_STRUCT, header_bytes[:HEADER_SIZE])
    comp_flag = (packed_len >> 24) & 0xFF
    payload_len = packed_len & 0xFFFFFF
    return api, cmd, seq, opcode, comp_flag, payload_len


def unpack_packet_payload(body_bytes: bytes, comp_flag: int = 0) -> Any:
    """
    Decompresses and deserializes msgpack payload from body bytes.
    """
    if not body_bytes:
        return {}

    body = body_bytes
    if comp_flag != 0:
        body = decompress_payload(body_bytes)

    try:
        return msgpack.unpackb(body, raw=False, strict_map_key=False)
    except Exception:
        # Fallback raw decoding if msgpack fails
        return msgpack.unpackb(body, raw=True, strict_map_key=False)
