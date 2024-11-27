import asyncio
from logging import error
from typing import List

import emoji
import telethon
import random
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, SetTypingRequest
from telethon.tl.types import Message, SendMessageCancelAction, SendMessageTypingAction

import GV
from utils import *

api_list=[]
def read_api_key():
    global api_list
    with open("api.txt","r",encoding="utf-8") as file:
        api_list=file.read().split("\n")

# login in telegram 1 account by phone number

async def loginByPhoneNumber(phoneNumber):
    
    while GV.IsGettingInput:
        await asyncio.sleep(GV.UPDATE_RATE)

    try:
        api_key = random.choice(api_list) if  api_list else None
        api_list.remove(api_key)
        API_ID = int(api_key.split("-")[0])
        API_HASH = api_key.split("-")[1]
        client = telethon.TelegramClient("sessions/" + phoneNumber,API_ID, API_HASH)
        await client.start(phoneNumber, GV.app.getInput2fa, code_callback=GV.app.getInputCode)

        if await client.is_user_authorized():
            me = await client.get_me()

        GV.debug("loginByPhoneNumber: " + str(me) + " logged in")
        GV.app.addLog(str(phoneNumber) + " logged in as " + str(me.first_name), GV.LOG_TAG["SYSTEM"])
        return {
            USER_OBJ_CLIENT_KEY: client,
            USER_OBJ_ME_KEY: me,
        }
    except Exception as e:
        GV.error("loginByPhoneNumber(" + phoneNumber + "): " + str(e) + " - " + str(type(e)))
        GV.app.addLog("Error: Cannot logged " + phoneNumber + " in: " + str(e), LOG_TAG["ERROR"])
        return None
    

async def adminLogin(phoneNumber):
    while GV.IsGettingInput:
        await asyncio.sleep(GV.UPDATE_RATE)

    try:
        api_key = random.choice(api_list) if  api_list else None
        api_list.remove(api_key)
        API_ID = int(api_key.split("-")[0])
        API_HASH = api_key.split("-")[1]
        client = telethon.TelegramClient("admin_sessions/" + phoneNumber,API_ID, API_HASH)
        await client.start(phoneNumber, GV.app.getInput2fa, code_callback=GV.app.getInputCode)

        if await client.is_user_authorized():
            me = await client.get_me()

        GV.debug("loginByPhoneNumber: " + str(me) + " logged in")
        GV.app.addLog(str(phoneNumber) + " logged in as " + str(me.first_name), GV.LOG_TAG["SYSTEM"])
        return {
            USER_OBJ_CLIENT_KEY: client,
            USER_OBJ_ME_KEY: me,
        }
    except Exception as e:
        GV.error("loginByPhoneNumber(" + phoneNumber + "): " + str(e) + " - " + str(type(e)))
        GV.app.addLog("Error: Cannot logged " + phoneNumber + " in: " + str(e), LOG_TAG["ERROR"])
        return None

async def loginAllAccounts():
    while True:
        if GV.ProgramStatus == PROGRAM_STATUS["STOP"]:
            break

        if GV.ProgramStatus == PROGRAM_STATUS["IDLE"]:
            await asyncio.sleep(GV.UPDATE_RATE)
            continue

        if GV.Phase < GV.Phase < PHASE["LOGGING_ACCOUNTS_IN"]:
            await asyncio.sleep(GV.UPDATE_RATE)
            continue

        if GV.Phase > PHASE["LOGGING_ACCOUNTS_IN"]:
            break

        # gets all phone numbers
        phonesList = getPhoneNumbers()
        GV.app.addLog("Got " + str(len(phonesList)) + " phone numbers", LOG_TAG["SYSTEM"])

        # logins in all accounts
        GV.UserObjects = []
        GV.AdminObjects = []
        read_api_key()
        admin_session_files = [f for f in os.listdir("admin_sessions/") if f.endswith('.session')]
        for admin_session in admin_session_files:
            phoneNumber = admin_session.split(".")[0]
            GV.app.addLog("Logging in " + str(phoneNumber) + "...", LOG_TAG["SYSTEM"])
            account = await adminLogin(phoneNumber)
            if account != None:
                GV.AdminObjects.append(account)
        client_session_files = [f for f in os.listdir("sessions/") if f.endswith(".session")]
        if GV.flag:
            for phoneNumber in phonesList:
                GV.app.addLog("Logging in " + str(phoneNumber) + "...", LOG_TAG["SYSTEM"])
                account = await loginByPhoneNumber(phoneNumber)
                if account != None:
                    GV.UserObjects.append(account)
        else:
            for session in client_session_files:
                phoneNumber = session.split(".")[0]
                GV.app.addLog("Logging in " + str(phoneNumber) + "...", LOG_TAG["SYSTEM"])
                account = await loginByPhoneNumber(phoneNumber)
                if account != None:
                    GV.UserObjects.append(account)

        GV.completePhase(PHASE["LOGGING_ACCOUNTS_IN"])


# try to join the groups with all the accounts
async def joinGroup():
    while True:
        if GV.ProgramStatus == PROGRAM_STATUS["STOP"]:
            break

        if GV.ProgramStatus == PROGRAM_STATUS["IDLE"] or GV.Phase < PHASE["JOINING_GROUPS"]:
            await asyncio.sleep(GV.UPDATE_RATE)
            continue

        if GV.Phase > PHASE["JOINING_GROUPS"]:
            break

        GV.app.addLog("Checking group...", LOG_TAG["CONTROL"])
        groupObj = getGroup()
        # await Accounts[i]["client"](ImportChatInviteRequest(desGroup))
        for user in GV.UserObjects:
            try:
                if groupObj[GROUP_OBJ_IS_INVITE_LINK]:
                    await user[USER_OBJ_CLIENT_KEY](ImportChatInviteRequest(groupObj[GROUP_OBJ_INVITE_KEY]))
                else:
                    await user[USER_OBJ_CLIENT_KEY](JoinChannelRequest(groupObj[GROUP_OBJ_LINK_KEY]))
                user[USER_OBJ_GROUP_KEY] = await user[USER_OBJ_CLIENT_KEY].get_entity(groupObj[GROUP_OBJ_LINK_KEY])

                GV.app.addLog(userObjToString(user) + " joined the group", LOG_TAG["CONTROL"])
                GV.debug("joinGroup: " + userObjToString(user) + " got group " + str(user[USER_OBJ_GROUP_KEY]))
            except Exception as e:
                if type(e) == telethon.errors.rpcerrorlist.UserAlreadyParticipantError:
                    user[USER_OBJ_GROUP_KEY] = await user[USER_OBJ_CLIENT_KEY].get_entity(groupObj[GROUP_OBJ_LINK_KEY])

                    GV.app.addLog(userObjToString(user) + " joined the group", LOG_TAG["CONTROL"])
                    GV.debug(
                        "joinGroup: "
                        + userObjToString(user)
                        + " joined the group and got "
                        + str(user[USER_OBJ_GROUP_KEY])
                    )
                else:
                    GV.app.addLog(userObjToString(user) + " cannot join the group. Reason: " + str(e), LOG_TAG["ERROR"])
                    GV.error(
                        "joinGroup - "
                        + userObjToString(user)
                        + " cannot join the group - "
                        + str(e)
                        + " - "
                        + str(type(e))
                    )
        for user in GV.AdminObjects:
            try:
                if groupObj[GROUP_OBJ_IS_INVITE_LINK]:
                    await user[USER_OBJ_CLIENT_KEY](ImportChatInviteRequest(groupObj[GROUP_OBJ_INVITE_KEY]))
                else:
                    await user[USER_OBJ_CLIENT_KEY](JoinChannelRequest(groupObj[GROUP_OBJ_LINK_KEY]))
                user[USER_OBJ_GROUP_KEY] = await user[USER_OBJ_CLIENT_KEY].get_entity(groupObj[GROUP_OBJ_LINK_KEY])

                GV.app.addLog(userObjToString(user) + " joined the group", LOG_TAG["CONTROL"])
                GV.debug("joinGroup: " + userObjToString(user) + " got group " + str(user[USER_OBJ_GROUP_KEY]))
            except Exception as e:
                if type(e) == telethon.errors.rpcerrorlist.UserAlreadyParticipantError:
                    user[USER_OBJ_GROUP_KEY] = await user[USER_OBJ_CLIENT_KEY].get_entity(groupObj[GROUP_OBJ_LINK_KEY])

                    GV.app.addLog(userObjToString(user) + " joined the group", LOG_TAG["CONTROL"])
                    GV.debug(
                        "joinGroup: "
                        + userObjToString(user)
                        + " joined the group and got "
                        + str(user[USER_OBJ_GROUP_KEY])
                    )
                else:
                    GV.app.addLog(userObjToString(user) + " cannot join the group. Reason: " + str(e), LOG_TAG["ERROR"])
                    GV.error(
                        "joinGroup - "
                        + userObjToString(user)
                        + " cannot join the group - "
                        + str(e)
                        + " - "
                        + str(type(e))
                    )
        GV.completePhase(PHASE["JOINING_GROUPS"])


# send typing status to the group for a number of seconds
async def sendTypingStatus(client, group, nSeconds):
    GV.app.addLog("Typing for " + str(int(nSeconds)) + " seconds...", LOG_TAG["CONTROL"])

    try:
        await client(SetTypingRequest(peer=group, action=SendMessageTypingAction()))
        await asyncio.sleep(nSeconds)
        GV.info("sendTypingStatus - " + str(nSeconds))
    except Exception as e:
        GV.error("sendTypingStatus - " + str(e) + " - " + str(type(e)))
        GV.app.addLog("Error: Cannot send typing status - " + str(e), LOG_TAG["ERROR"])

    try:
        await client(SetTypingRequest(peer=group, action=SendMessageCancelAction()))
        GV.info("cancelTypingStatus")
    except Exception as e:
        GV.error("cancelTypingStatus - " + str(e) + " - " + str(type(e)))
        GV.app.addLog("Error: Cannot cancel typing status - " + str(e), LOG_TAG["ERROR"])


def get_max_message_id(messages: List[telethon.types.Message]):
    return max([msg.id for msg in messages])

async def adminReply(adminObj):
    admin = adminObj[USER_OBJ_CLIENT_KEY]
    group = adminObj[USER_OBJ_GROUP_KEY]
    replylen = len(GV.AdminMsgObjects)
    curmessagelen = len(GV.SentMessages)
    emojilist =  random.choice(GV.EMOJI_LIST) if  GV.EMOJI_LIST else None
    for i in range(replylen):
        adminMsg = GV.AdminMsgObjects[i]
        replyList = adminMsg[MSG_OBJ_REPLY_TO_KEY]
        if curmessagelen in replyList:
            adminContent = adminMsg[MSG_OBJ_CONTENT_KEY]
            adminReplyTo = GV.SentMessages[curmessagelen-1]
            try:
                sendMessage = await admin.send_message(group,message=emoji.emojize(str(adminContent+emojilist),language="alias"),reply_to=adminReplyTo.id if adminReplyTo else None)
                GV.MessageMemory.append(sendMessage)
            except Exception as e:
                GV.error(str(e) + " - " + str(type(e)))
                GV.app.addLog(str(e), LOG_TAG["ERROR"])

# sends a message
async def sendMessage(userObj, msgObj):
    GV.IsSendingMsg = True

    client = userObj[USER_OBJ_CLIENT_KEY]
    group = userObj[USER_OBJ_GROUP_KEY]
    message = msgObj[MSG_OBJ_CONTENT_KEY]
    file = msgObj[MSG_OBJ_IMG_KEY]
    sticker_path = msgObj[MSG_OBJ_STICKER]
    # finds the message to reply to
    delay = msgObj[MSG_OBJ_DELAY_KEY]
    replyTo = None
    adminReply = None
    if message=="":
        print(message)
    try:
        replyTo = GV.SentMessages[msgObj[MSG_OBJ_REPLY_TO_KEY] - 1]
    except Exception as e:
        error("sendMessage reply to: " + str(msgObj) + str(e) + " - " + str(type(e)))

    if msgObj[MSG_OBJ_REPLY_PIN_KEY]:
        try:
            replyTo = await client.get_messages(group, ids=GV.PinId)
        except Exception as e:
            error("sendMessage reply to pin: " + str(msgObj) + str(e) + " - " + str(type(e)))
            GV.app.addLog("Error: Cannot find pin message. Reason: " + str(e), LOG_TAG["ERROR"])

    user = msgObj[MSG_OBJ_USER_KEY]
    if user:
        try:
            user = GV.UserObjects[user - 1]
            if user is not userObj:
                GV.UserIndex -= 1
            userObj = user
            client = userObj[USER_OBJ_CLIENT_KEY]
            group = userObj[USER_OBJ_GROUP_KEY]
        except Exception as e:
            error("sendMessage user: " + str(userObj) + str(e) + " - " + str(type(e)))

    if GV.ShowTyping:
        await sendTypingStatus(client, group, TYPING_STATUS_BASE_DURATION)
    try:
        if file!=None or message!='':
            sentMessage = await client.send_message(
                group, message=emoji.emojize(message, language="alias"), reply_to=replyTo.id if replyTo else None, file=file
            )
            GV.SentMessages.append(sentMessage)
            GV.MessageMemory.append(sentMessage)
            GV.app.addLog(
                userObjToString(userObj, False) + " sent a message: " + msgObj[MSG_OBJ_CONTENT_KEY], LOG_TAG["SYSTEM"]
            )
        if sticker_path:
            sentSticker = await client.send_file(group, sticker_path, caption="Here is a sticker!")
    except Exception as e:
        GV.error("sendMessage(" + str(userObj) + ", " + str(msgObj) + "): " + str(e) + " - " + str(type(e)))
        GV.app.addLog("Error: " + userObjToString(userObj) + " cannot send message. Reason:" + str(e), LOG_TAG["ERROR"])

    if not delay:
        delay = GV.app.getDelay()
        GV.app.addLog("The program will send the next message in " + str(delay) + " seconds...", LOG_TAG["CONTROL"])
    await asyncio.sleep(delay)

    GV.IsSendingMsg = False


async def human_bot_reply():
    if GV.enable_human_reply:
        for user_obj in GV.UserObjects:
            human_msg_obj = GV.human_msg_objects[GV.human_msg_index]
            message = human_msg_obj[MSG_OBJ_CONTENT_KEY]
            file = human_msg_obj[MSG_OBJ_IMG_KEY]
            client: telethon.TelegramClient = user_obj[USER_OBJ_CLIENT_KEY]
            group = user_obj[USER_OBJ_GROUP_KEY]
            # messges = await client.get_messages(group, limit=50, offset_id=0, from_user="me")
            message_ids = [msg.id for msg in GV.MessageMemory if msg.sender_id == user_obj["me"].id]
            total_messages = []
            self_ids = [clientobj["me"].id for clientobj in GV.AdminObjects]
            admins = await client.get_participants(group, filter=telethon.tl.types.ChannelParticipantsAdmins)
    
            admin_ids = [admin.id for admin in admins]
            self_ids = self_ids+admin_ids
            messges = await client.get_messages(
                entity=group,
                limit=50,
                min_id=GV.last_offset_per_client[client] if client in GV.last_offset_per_client.keys() else 0,
            )
            try:
                total_messages = [
                    msg for msg in messges if msg.reply_to_msg_id in message_ids and msg.sender_id in self_ids
                ]
            except Exception as e:
                print(str(e))
            if total_messages:
                # for msg in total_messages:
                sent_message = await client.send_message(
                    group, message=emoji.emojize(message, language="alias"), reply_to=total_messages[0]
                )
                await total_messages[0].mark_read()
                GV.last_offset_per_client[client] = total_messages[0].id
                GV.human_msg_index = (GV.human_msg_index + 1) % len(GV.human_msg_objects)


# sends a message
async def sendMessageReplyTo():
    GV.IsSendingMsg = True
    userObj = GV.UserObjects[0]
    client: telethon.TelegramClient = userObj[USER_OBJ_CLIENT_KEY]
    group = userObj[USER_OBJ_GROUP_KEY]

    # finds the message to reply to
    replyTo = None
    try:
        replyTo: Message = GV.SentMessages[-1]
    except Exception as e:
        error("sendMessage reply to: " + str(type(e)))
    if not replyTo:
        GV.IsSendingMsg = False
        return None
    if replyTo.reply_to_msg_id:
        message_original = await client.get_messages(group, ids=replyTo.reply_to_msg_id)
        try:
            clientobj = [clientobj for clientobj in GV.UserObjects if clientobj["me"].id == message_original.sender_id][
                0
            ]
        except:
            return None
    else:
        GV.IsSendingMsg = False
        return None
    # reassign
    client: telethon.TelegramClient = clientobj[USER_OBJ_CLIENT_KEY]
    group = clientobj[USER_OBJ_GROUP_KEY]

    try:
        bot_msg_obj = GV.bot_msg_objects[GV.bot_msg_index]
        message = bot_msg_obj[MSG_OBJ_CONTENT_KEY]
        file = bot_msg_obj[MSG_OBJ_IMG_KEY]
        sentMessage = await client.send_message(
            group,
            message=emoji.emojize(message, language="alias"),
            reply_to=replyTo,
        )
        GV.app.addLog(
            userObjToString(userObj, False) + " sent a message: " + bot_msg_obj[MSG_OBJ_CONTENT_KEY], LOG_TAG["SYSTEM"]
        )
        GV.bot_msg_index = (GV.bot_msg_index + 1) % len(GV.bot_msg_objects)

    except Exception as e:
        GV.error("sendMessage(" + str(userObj) + ", " + str(bot_msg_obj) + "): " + str(e) + " - " + str(type(e)))
        GV.app.addLog("Error: " + userObjToString(userObj) + " cannot send message. Reason:" + str(e), LOG_TAG["ERROR"])

    GV.IsSendingMsg = False

# Send a message, mention group members, and pin the message
async def adminSendAndPinMessage(adminObj, msgObj):
    GV.IsPinedMsg = True
    admin = adminObj[USER_OBJ_CLIENT_KEY]
    group = adminObj[USER_OBJ_GROUP_KEY]
    message = msgObj[MSG_OBJ_CONTENT_KEY]
    delay = int(msgObj[MSG_OBJ_DELAY_KEY])
    pin_number = int(msgObj[MSG_OBJ_REPLY_TO_KEY])
    try:
        # Retrieve group participants
        participants = await admin.get_participants(group)
        if pin_number:
            temp = GV.index+pin_number
            if temp>len(participants):
                temp=len(participants)
            members_to_mention = participants[GV.index:temp]
            GV.index = temp
            if GV.index>=len(participants):
                GV.index=0
        mentions = ""
        for member in members_to_mention:
            if member.username:
                mentions += f"@{member.username} "
            else:
                mentions += f"[{member.first_name}](tg://user?id={member.id}) "

        # Append mentions to the message
        message_with_mentions = f"{message}\n\n{mentions}"

        # Admin sends the message with mentions
        sentMessage = await admin.send_message(
            group, message=emoji.emojize(message_with_mentions, language="alias"))
        # Pin the message after it is successfully sent
        await admin.pin_message(group, sentMessage.id, notify=False)
        GV.app.addLog(
            userObjToString(adminObj, False) + " pinned the message: " + msgObj[MSG_OBJ_CONTENT_KEY], LOG_TAG["SYSTEM"]
        )
    except Exception as e:
        GV.error("adminSendAndPinMessage(" + str(adminObj) + ", " + str(msgObj) + "): " + str(e) + " - " + str(type(e)))
        GV.app.addLog("Error: " + userObjToString(adminObj) + " cannot send and pin the message. Reason:" + str(e), LOG_TAG["ERROR"])

    await asyncio.sleep(delay)
    GV.IsPinedMsg=False

# actually autochat
async def startChatting():
    GV.EMOJI_LIST = getEmojiList()
    while True:
        if GV.ProgramStatus == PROGRAM_STATUS["STOP"]:
            break

        if GV.ProgramStatus == PROGRAM_STATUS["IDLE"] or GV.Phase < PHASE["CHATTING"] or GV.IsSendingMsg:
            await asyncio.sleep(GV.UPDATE_RATE)
            continue

        if GV.Phase > PHASE["CHATTING"]:
            break

        if GV.MsgObjects is None:
            GV.MsgObjects = getMessages(MESSAGES_FILE_NAME)
        
        if GV.AdminMsgObjects is None:
            GV.AdminMsgObjects = getAdminMessages(MESSAGE_FILE_NAME_ADMIN_REPLY)

        if GV.human_msg_objects is None:
            GV.human_msg_objects = getMessages(MESSAGES_FILE_NAME_HUMAN_TO_BOT)

        if GV.bot_msg_objects is None:
            GV.bot_msg_objects = getMessages(MESSAGES_FILE_NAME_BOT_TO_BOT)

        if GV.MsgIndex == 0:
            GV.SentMessages = []

        if len(GV.MessageMemory) > 200:
            del GV.MessageMemory[0]

        userObj = GV.UserObjects[GV.UserIndex]
        msgObj = GV.MsgObjects[GV.MsgIndex]
        adminObj = GV.AdminObjects[GV.AdminIndex]
        pinadmin = GV.AdminObjects[(GV.AdminIndex+2)% len(GV.AdminObjects)]
        pinMsglist = getPinMessages(PIN_MESSAGE_FILE_NAME)
        pinMsg = pinMsglist[0]
        await asyncio.gather(sendMessage(userObj, msgObj), sendMessageReplyTo(), human_bot_reply(),adminReply(adminObj))
        if not GV.IsPinedMsg:
            asyncio.create_task(adminSendAndPinMessage(adminObj, pinMsg))
        GV.UserIndex = (GV.UserIndex + 1) % len(GV.UserObjects)
        GV.MsgIndex = (GV.MsgIndex + 1) % len(GV.MsgObjects)
        GV.AdminIndex = (GV.AdminIndex+1) % len(GV.AdminObjects)
        GV.AdminMsgIndex = (GV.AdminIndex+1) % len(GV.AdminMsgObjects)
