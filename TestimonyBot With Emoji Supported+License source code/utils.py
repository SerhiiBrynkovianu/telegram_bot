import json
import os
import re
import GV
from CONST import *


# gets the content of the markers
def getContentOfMarkers(string, open, close):
    try:
        openIndex = string.index(open)
        closeIndex = string.index(close)
        return string[openIndex + 1 : closeIndex]
    except Exception as e:
        if type(e) is not ValueError:
            GV.error(
                "getContentOfMarkers(" + string + ", " + open + ", " + close + "): " + str(e) + " - " + str(type(e))
            )
    return ""

def getAdminOfMarkers(string, open, close):
    matches1 = re.finditer(open, string)
    openIndexs = [match.start() for match in matches1]
    matches2 = re.finditer(close,string)
    closeIndexs = [match.start() for match in matches2]
    stringlist=[]
    for i,index in enumerate(openIndexs):
        text=string[index+1:closeIndexs[i]]
        stringlist.append(int(text))
    return stringlist


# removes all markers from string including the content betweens them
def removeMarkers(string, open, close):
    try:
        openIndex = string.index(open)
        closeIndex = string.index(close)
        return string[:openIndex]
    except Exception as e:
        if type(e) is not ValueError:
            GV.error("removeMarkers(" + string + ", " + open + ", " + close + "): " + str(e) + " - " + str(type(e)))
    return ""

def getAdminMessages(filename:str):
    originMessagesList = []

    try:
        with open(filename, "r", encoding="utf-8") as messagesFile:
            originMessagesList = messagesFile.read().split("\n")
        GV.info("getMessages: " + str(originMessagesList))
    except Exception as e:
        GV.error("getMessages - openning file: " + str(e) + " - " + str(type(e)))

    msgObjs = []
    msgIndex = 0
    for msg in originMessagesList:
        msgIndex += 1
        msgObj = {MSG_OBJ_CONTENT_KEY: msg, MSG_OBJ_DELAY_KEY: None, MSG_OBJ_REPLY_TO_KEY: None, MSG_OBJ_USER_KEY: None}

        # finds reply
        replyTo = []
        try:
            content = getAdminOfMarkers(msgObj[MSG_OBJ_CONTENT_KEY], "\\(", "\\)")
            if len(content)!=0:
                replyTo = content
                msgObj[MSG_OBJ_CONTENT_KEY] = removeMarkers(
                    msgObj[MSG_OBJ_CONTENT_KEY], REPLY_OPEN_MARKER, REPLY_CLOSE_MARKER
                )
        except Exception as e:
            GV.error("getMessages finds reply - '" + msg + "': " + str(e) + " - " + str(type(e)))

        msgObj[MSG_OBJ_REPLY_TO_KEY] = replyTo
        msgObjs.append(msgObj)

    # strips all messages & logs them
    infoStr = ""
    for msgObj in msgObjs:
        msgObj[MSG_OBJ_CONTENT_KEY] = msgObj[MSG_OBJ_CONTENT_KEY].strip()
        infoStr += json.dumps(msgObj, sort_keys=True, indent=4, separators=(",", ": ")) + ",\n"
    GV.info("getMessages: \n" + infoStr)
    GV.app.addLog("Got " + str(len(msgObjs)) + " messages", LOG_TAG["CONTROL"])

    return msgObjs

def getPinMessages(filename:str):
    originMessagesList = []

    try:
        with open(filename, "r",encoding="utf-8") as messagesFile:
            msg = messagesFile.read()
        GV.info("getMessages: " + str(originMessagesList))
    except Exception as e:
        GV.error("getMessages - openning file: " + str(e) + " - " + str(type(e)))

    msgObjs = []
    msgObj = {MSG_OBJ_CONTENT_KEY: msg, MSG_OBJ_DELAY_KEY: None, MSG_OBJ_REPLY_TO_KEY: None, MSG_OBJ_USER_KEY: None}

    # finds reply
    replyTo = None
    try:
        content = getContentOfMarkers(msgObj[MSG_OBJ_CONTENT_KEY], REPLY_OPEN_MARKER, REPLY_CLOSE_MARKER)
        if content != "":
            replyTo = int(content)
            msgObj[MSG_OBJ_CONTENT_KEY] = removeMarkers(
                msgObj[MSG_OBJ_CONTENT_KEY], REPLY_OPEN_MARKER, REPLY_CLOSE_MARKER
            )
    except Exception as e:
        GV.error("getMessages finds reply - '" + msg + "': " + str(e) + " - " + str(type(e)))

    # finds delay
    delay = None
    try:
        content = getContentOfMarkers(msgObj[MSG_OBJ_CONTENT_KEY], DELAY_OPEN_MARKER, DELAY_CLOSE_MARKER)
        if content != "":
            delay = int(content)
            msgObj[MSG_OBJ_CONTENT_KEY] = removeMarkers(
                msgObj[MSG_OBJ_CONTENT_KEY], DELAY_OPEN_MARKER, DELAY_CLOSE_MARKER
            )
    except Exception as e:
        GV.error("getMessages finds delay - '" + msg + "': " + str(e) + " - " + str(type(e)))

    # finds user

    msgObj[MSG_OBJ_REPLY_TO_KEY] = replyTo
    msgObj[MSG_OBJ_DELAY_KEY] = delay

    msgObjs.append(msgObj)

    return msgObjs

def getMessages(filename: str):
    GV.app.addLog("Getting messages...", GV.LOG_TAG["CONTROL"])
    originMessagesList = []

    try:
        with open(filename, "r",encoding="utf-8") as messagesFile:
            originMessagesList = messagesFile.read().split("\n")
        GV.info("getMessages: " + str(originMessagesList))
    except Exception as e:
        GV.error("getMessages - openning file: " + str(e) + " - " + str(type(e)))

    msgObjs = []
    msgIndex = 0
    for msg in originMessagesList:
        msgIndex += 1
        msgObj = {MSG_OBJ_CONTENT_KEY: msg, MSG_OBJ_DELAY_KEY: None, MSG_OBJ_REPLY_TO_KEY: None, MSG_OBJ_USER_KEY: None}

        # finds reply
        replyTo = None
        try:
            content = getContentOfMarkers(msgObj[MSG_OBJ_CONTENT_KEY], REPLY_OPEN_MARKER, REPLY_CLOSE_MARKER)
            if content != "":
                replyTo = int(content)
                msgObj[MSG_OBJ_CONTENT_KEY] = removeMarkers(
                    msgObj[MSG_OBJ_CONTENT_KEY], REPLY_OPEN_MARKER, REPLY_CLOSE_MARKER
                )
        except Exception as e:
            GV.error("getMessages finds reply - '" + msg + "': " + str(e) + " - " + str(type(e)))

        # finds delay
        delay = None
        try:
            content = getContentOfMarkers(msgObj[MSG_OBJ_CONTENT_KEY], DELAY_OPEN_MARKER, DELAY_CLOSE_MARKER)
            if content != "":
                delay = int(content)
                msgObj[MSG_OBJ_CONTENT_KEY] = removeMarkers(
                    msgObj[MSG_OBJ_CONTENT_KEY], DELAY_OPEN_MARKER, DELAY_CLOSE_MARKER
                )
        except Exception as e:
            GV.error("getMessages finds delay - '" + msg + "': " + str(e) + " - " + str(type(e)))

        # finds user
        user = None
        try:
            content = getContentOfMarkers(msgObj[MSG_OBJ_CONTENT_KEY], USER_OPEN_MARKER, USER_CLOSE_MARKER)
            if content != "":
                user = int(content)
                msgObj[MSG_OBJ_CONTENT_KEY] = removeMarkers(
                    msgObj[MSG_OBJ_CONTENT_KEY], USER_OPEN_MARKER, USER_CLOSE_MARKER
                )
        except Exception as e:
            GV.error("getMessages finds user - '" + msg + "': " + str(e) + " - " + str(type(e)))

        # finds reply pin
        isReplyPin = False
        try:
            content = getContentOfMarkers(msgObj[MSG_OBJ_CONTENT_KEY], PIN_OPEN_MARKER, PIN_CLOSE_MARKER)
            if content == "pin":
                isReplyPin = True
                msgObj[MSG_OBJ_CONTENT_KEY] = removeMarkers(
                    msgObj[MSG_OBJ_CONTENT_KEY], PIN_OPEN_MARKER, PIN_CLOSE_MARKER
                )
        except Exception as e:
            GV.error("getMessages find pin - '" + msg + "': " + str(e) + " - " + str(type(e)))

        # finds in folder images to see if there's any png/jpg/gif with the name msgIndex
        imgPath = None
        for extension in ACCEPTED_FILE_EXTENSIONS:
            path = "images/" + str(msgIndex) + extension
            if os.path.isfile(path):
                imgPath = path
                break
        stickerPath = None
        path1 = "images/" + str(msgIndex) + ".tgs"
        if os.path.isfile(path1):
            stickerPath = path1
        msgObj[MSG_OBJ_REPLY_TO_KEY] = replyTo
        msgObj[MSG_OBJ_DELAY_KEY] = delay
        msgObj[MSG_OBJ_USER_KEY] = user
        msgObj[MSG_OBJ_IMG_KEY] = imgPath
        msgObj[MSG_OBJ_REPLY_PIN_KEY] = isReplyPin
        msgObj[MSG_OBJ_STICKER] = stickerPath

        msgObjs.append(msgObj)

    # strips all messages & logs them
    infoStr = ""
    for msgObj in msgObjs:
        msgObj[MSG_OBJ_CONTENT_KEY] = msgObj[MSG_OBJ_CONTENT_KEY].strip()
        infoStr += json.dumps(msgObj, sort_keys=True, indent=4, separators=(",", ": ")) + ",\n"
    GV.info("getMessages: \n" + infoStr)
    GV.app.addLog("Got " + str(len(msgObjs)) + " messages", LOG_TAG["CONTROL"])

    return msgObjs


def getMessagesHumanReply():
    GV.app.addLog("Getting messages...", GV.LOG_TAG["CONTROL"])
    originMessagesList = []

    try:
        with open(MESSAGES_FILE_NAME_HUMAN_TO_BOT, "r",encoding="utf-8") as messagesFile:
            originMessagesList = messagesFile.read().split("\n")
        GV.info("getMessages: " + str(originMessagesList))
    except Exception as e:
        GV.error("getMessages - openning file: " + str(e) + " - " + str(type(e)))

    return originMessagesList


# gets all phone numbers
def getEmojiList():
    with open(EMOJI_LIST,'r',encoding="utf-8") as f:
        emojiList = f.read().split("\n")
        return emojiList

def getPhoneNumbers() -> list:
    try:
        with open(PHONES_FILENAME, "r",encoding="utf-8") as phoneFile:
            phonesList = phoneFile.read().split("\n")
            GV.info("getPhoneNumbers: " + str(phonesList))
            return phonesList
    except Exception as e:
        GV.error("getPhoneNumbers: " + str(e) + " - " + str(type(e)))


# gets the group
def getGroup() -> str:
    try:
        with open(GROUP_FILENAME, "r",encoding="utf-8") as groupFile:
            group = groupFile.read().strip()
            # Replace the specific part of the string
            new_string = group.replace("https://t.me/+", "https://t.me/joinchat/")
            groupObj = {
                GROUP_OBJ_LINK_KEY: new_string,
                GROUP_OBJ_INVITE_KEY: new_string.split("joinchat/")[-1],
                GROUP_OBJ_IS_INVITE_LINK: new_string.index("joinchat/") != -1,
            }
            GV.debug("getGroup: " + str(groupObj))
            return groupObj
    except Exception as e:
        GV.error("getGroup: " + str(e) + " - " + str(type(e)))


# returns a string represents of a userObject
def userObjToString(userObj, showPhone=True):
    string = userObj[USER_OBJ_ME_KEY].first_name
    if showPhone:
        string += " (" + userObj[USER_OBJ_ME_KEY].phone + ")"
    return string


# gets the id of the pin message
def getPinId():
    try:
        with open(PIN_FILENAME, "r",encoding="utf-8") as pinFile:
            pinLink = pinFile.read()
            pinId = pinLink.split("/")[-1]
            GV.debug("getPinId: " + str(pinLink) + " - " + str(pinId))
            GV.app.addLog("Got pin link: " + str(pinLink), LOG_TAG["CONTROL"])
            return int(pinId)
    except Exception as e:
        GV.app.addLog("Cannot get pin link. Reason: " + str(e), LOG_TAG["ERROR"])
        GV.error("getPinId: " + str(e) + " - " + str(type(e)))
