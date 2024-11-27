PROGRAM_STATUS = {"RUNNING": 1, "IDLE": 2, "STOP": 3}

LOG_TAG = {"NORMAL": "nor", "CONTROL": "ctr", "SYSTEM": "sys", "ERROR": "err"}

PHASE = {
    "LOGGING_ACCOUNTS_IN": 0,
    "JOINING_GROUPS": 1,
    "CHATTING": 2,
}

MESSAGES_FILE_NAME = "messages.txt"
MESSAGES_FILE_NAME_BOT_TO_BOT = "bot_to_bot_reply.txt"
MESSAGES_FILE_NAME_HUMAN_TO_BOT = "human_to_bot_reply.txt"
MESSAGE_FILE_NAME_ADMIN_REPLY = "admin_reply.txt"
PHONES_FILENAME = "phones.txt"
GROUP_FILENAME = "group.txt"
PIN_FILENAME = "pin.txt"
EMOJI_LIST = "emoji reaction.txt"
PIN_MESSAGE_FILE_NAME = "pin_message.txt"

REPLY_OPEN_MARKER = "("
REPLY_CLOSE_MARKER = ")"
DELAY_OPEN_MARKER = "["
DELAY_CLOSE_MARKER = "]"
USER_OPEN_MARKER = "{"
USER_CLOSE_MARKER = "}"
PIN_OPEN_MARKER = "<"
PIN_CLOSE_MARKER = ">"

MSG_OBJ_CONTENT_KEY = "content"
MSG_OBJ_REPLY_TO_KEY = "replyTo"
MSG_OBJ_DELAY_KEY = "delay"
MSG_OBJ_USER_KEY = "user"
MSG_OBJ_IMG_KEY = "imgPath"
MSG_OBJ_REPLY_PIN_KEY = "replyPin"
MSG_OBJ_STICKER = "sticker"

USER_OBJ_ME_KEY = "me"
USER_OBJ_CLIENT_KEY = "client"

GROUP_OBJ_LINK_KEY = "link"
GROUP_OBJ_INVITE_KEY = "invite"
USER_OBJ_GROUP_KEY = "group"
GROUP_OBJ_IS_INVITE_LINK = "isInvite"

API_ID = 1611895
API_HASH = "864a1a4e317cbeb7565e5c3407aa10e3"

ACCEPTED_FILE_EXTENSIONS = [".png", ".PNG", ".jpg", ".JPG", ".gif", ".GIF", ".mp4", ".MP4"]
TYPING_STATUS_BASE_DURATION = 5
