import logging
import os
from asyncio.windows_events import NULL
from datetime import datetime

from CONST import *
from utils import getPinId


def init():
    global app
    global root
    global FPS
    global UPDATE_RATE
    global Log
    global Delay
    global Phase
    global ProgramStatus
    global UserObjects
    global AdminObjects
    global IsGettingInput
    global MsgObjects
    global AdminMsgObjects
    global MsgIndex
    global AdminMsgIndex
    global AdminIndex
    global UserIndex
    global SentMessages
    global IsSendingMsg
    global IsPinedMsg
    global PinId
    global ShowTyping
    global last_offset_per_client
    global human_msg_objects
    global admin_msg_object
    global human_msg_index
    global enable_human_reply
    global bot_msg_objects
    global bot_msg_index
    global MessageMemory
    global flag
    global emoji_list
    global index

    if not os.path.isdir("logs"):
        os.makedirs("logs")
    if not os.path.isdir("sessions"):
        os.makedirs("sessions")

    app = None
    root = None
    FPS = 60
    UPDATE_RATE = 1 / FPS

    ProgramStatus = PROGRAM_STATUS["IDLE"]

    logging.basicConfig(
        filename="logs/" + str(datetime.now().strftime("%m.%d.%Y..%H.%M.%S")) + ".log", level=logging.DEBUG
    )
    logging.getLogger("telethon").setLevel(logging.ERROR)

    ShowTyping = 1
    enable_human_reply = 1
    Delay = 4
    Phase = PHASE["LOGGING_ACCOUNTS_IN"]
    UserObjects = []
    AdminObjects = []
    UserIndex = 0
    AdminIndex = 0
    MsgObjects = None
    AdminMsgObjects = None
    human_msg_objects = None
    bot_msg_objects = None
    admin_msg_object = None
    MsgIndex = 0
    AdminMsgIndex = 0
    human_msg_index = 0
    bot_msg_index = 0
    IsGettingInput = False
    SentMessages = []
    MessageMemory = []
    IsSendingMsg = False
    IsPinedMsg = False
    last_offset_per_client = {}
    flag = False
    emoji_list=[]
    index = 0

def debug(log):
    print("debug: " + log)
    logging.debug(log)


def info(log):
    print("info: " + log)
    logging.info(log)


def error(log):
    print("error: " + log)
    logging.error(log)


def warn(log):
    print("warn: " + log)
    logging.warn(log)


def completePhase(phase):
    global Phase
    Phase = phase + 1
    info("Phase completed: " + str(phase))
