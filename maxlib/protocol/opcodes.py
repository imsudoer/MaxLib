"""
Complete enumeration of MAX messenger protocol opcodes.
"""
from enum import IntEnum


class Opcode(IntEnum):
    # System / Connection
    PING = 1
    DEBUG = 2
    RECONNECT = 3
    LOG = 5
    SESSION_INIT = 6

    # Auth & Profile
    PROFILE = 16
    AUTH_START = 17
    AUTH_CHECK_CODE = 18
    LOGIN = 19
    LOGOUT = 20
    SYNC = 21
    CONFIG = 22
    AUTH_CONFIRM = 23
    PRESET_AVATARS = 25

    # Assets / Stickers
    ASSETS_GET = 26
    ASSETS_UPDATE = 27
    ASSETS_GET_BY_IDS = 28
    ASSETS_ADD = 29

    # Contacts
    CONTACT_INFO = 32
    CONTACT_ADD = 33
    CONTACT_UPDATE = 34  # Add/Remove/Block/Unblock
    CONTACT_PRESENCE = 35
    CONTACT_LIST = 36
    CONTACT_SEARCH = 37
    CONTACT_MUTUAL = 38
    CONTACT_PHOTOS = 39
    CONTACT_SORT = 40
    CONTACT_VERIFY = 42
    REMOVE_CONTACT_PHOTO = 43
    CONTACT_INFO_BY_PHONE = 46

    # Chats & Messages
    CHAT_INFO = 48
    CHAT_HISTORY = 49
    CHAT_MARK = 50
    CHAT_MEDIA = 51
    CHAT_DELETE = 52
    CHATS_LIST = 53
    CHAT_CLEAR = 54
    CHAT_UPDATE = 55
    CHAT_CHECK_LINK = 56
    CHAT_JOIN = 57
    CHAT_LEAVE = 58
    CHAT_MEMBERS = 59
    PUBLIC_SEARCH = 60
    CHAT_PERSONAL_CONFIG = 61
    CHAT_CREATE = 63
    MSG_SEND = 64
    MSG_TYPING = 65
    MSG_DELETE = 66
    MSG_EDIT = 67
    CHAT_SEARCH = 68
    MSG_SHARE_PREVIEW = 70
    MSG_GET = 71
    MSG_SEARCH_TOUCH = 72
    MSG_SEARCH = 73
    MSG_GET_STAT = 74
    CHAT_SUBSCRIBE = 75

    # Video / Calls
    VIDEO_CHAT_START = 76
    CHAT_MEMBERS_UPDATE = 77
    VIDEO_CHAT_START_ACTIVE = 78
    VIDEO_CHAT_HISTORY = 79

    # Media / File Uploads
    PHOTO_UPLOAD = 80
    STICKER_UPLOAD = 81
    VIDEO_UPLOAD = 82
    AUDIO_UPLOAD = 83
    FILE_UPLOAD = 84

    # Push Notifications / Real-time events (server-to-client)
    PUSH_NEW_MESSAGE = 128
    PUSH_TYPING = 129
    PUSH_MESSAGE_EDIT = 130
    PUSH_MESSAGE_DELETE = 131
    PUSH_CHAT_UPDATE = 132
    PUSH_PRESENCE = 133
    PUSH_REACTION = 134
    PUSH_CALL = 135

    # Reactions
    SET_REACTION = 178
    REMOVE_REACTION = 179
    GET_REACTIONS = 180

    # Privacy & Admin
    ADMIN_PERMISSIONS = 190
    PRIVACY_SETTINGS = 191
    ACCOUNT_DELETE = 199
