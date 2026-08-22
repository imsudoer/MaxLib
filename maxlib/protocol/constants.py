"""
Protocol constants and default parameters for MAX messenger.
"""

API_VERSION = 11
CMD_REQUEST = 0
CMD_OK = 1
CMD_NOT_FOUND = 2
CMD_ERROR = 3

# Packet header struct format: >BBHHI
# > : Big-endian (network byte order)
# B : API Version (uint8)
# B : Command Type (uint8: 0=req/push, 1=ok, 2=not_found, 3=error)
# H : Sequence ID (uint16)
# H : Opcode (uint16)
# I : Packed Length (uint32: high byte = compression flag, low 24 bits = payload length)
HEADER_STRUCT = ">BBHHI"
HEADER_SIZE = 10

# Network endpoints
DEFAULT_HOST = "api.oneme.ru"
DEFAULT_PORT = 443
DEFAULT_WS_URL = "wss://ws-api.oneme.ru/websocket"
DEFAULT_WEB_ORIGIN = "https://web.max.ru"

# Compression settings
MIN_COMPRESS_LENGTH = 32
MAX_DECOMPRESSED_SIZE = 32 * 1024 * 1024  # 32 MB safety limit

# Timeouts
DEFAULT_CONNECT_TIMEOUT = 15.0
DEFAULT_REQUEST_TIMEOUT = 30.0
DEFAULT_PING_INTERVAL = 30.0
DEFAULT_RECONNECT_DELAY = 1.0
DEFAULT_MAX_RECONNECT_DELAY = 60.0
