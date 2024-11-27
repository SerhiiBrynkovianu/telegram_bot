from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import *
from tkinter.messagebox import *
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import InputPeerEmpty
import os
import sys
import shutil
from subprocess import Popen
import telebot
import time
import threading
import asyncio
import json

pin_message_flag = True
delete_message_flag = True
show_group_flag = True
group_id = ""
delay_time = 0
mention_member = 0
bot_token = ""
phone_number = ""
api_id = 0
api_hash = ""

with open("setting.json","r") as openFile:
    setting_data = json.load(openFile)    

api_id = setting_data["api_id"]
api_hash = setting_data["api_hash"]
bot_token = setting_data["bot_token"]
phone_number = setting_data["phonenumber"]

client = TelegramClient(phone_number, api_id, api_hash)
bot = telebot.TeleBot(bot_token)
bot_id = bot.get_me().id
msg_text = ""
stop_flag = 1
my_thread = ""
pill2kill = ""
all_participants = []
all_messages = []

group_list = ["Select group or channel"]
channels = []
groups = []
group_members = []
def connect():
    client.connect()
    if not client.is_user_authorized():
        client.send_code_request(phone_number)
        client.sign_in("session_file", input('Enter verification code: '))
    print("Connect!!!")

    # Join Groups
    group_link_list = setting_data["group_link_list"]
    for group_link in group_link_list:
        group_id = group_link.split("/")[-1].replace("+","")
        try:
            client(ImportChatInviteRequest(group_id))
        except:
            pass
    chats = []
    last_date = None
    chunk_size = 200
    result = client(GetDialogsRequest(
                offset_date=last_date,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=chunk_size,
                hash = 0
            ))
    chats.extend(result.chats)
    
    
    for chat in chats:
        groups.append(chat)

    for i,g in enumerate(groups):
        group_list.append(g.title)
        try:
            participants = client.get_participants(g)
            participant_data = {}
            participant_data["group_title"] = g.title
            participant_data["group_data"] = participants
            all_participants.append(participant_data)
        except:
            pass
    
def pin_radio_selected():
    global pin_message_flag
    value = pin_message_var.get()
    if value == "pin_message_yes":
        pin_message_flag = True
    else:
        pin_message_flag = False

def delete_message_radio_selected():
    global delete_message_flag
    value = delete_message_var.get()
    if value == "delete_previous_message_yes":
        delete_message_flag = True
    else:
        delete_message_flag = False

def group_or_channel_radio_selected():
    
    value = pin_message_var.get()
    if value == "show_group":
        show_group_flag = True
    else:
        show_group_flag = False

def send_message_thread(stop_event):
    global stop_flag,all_messages
    target_group = ""
    target_group_participants = []

    for i,group in enumerate(groups):
        if group.title == group_var.get():
            target_group = group
    print(target_group)
    for participant in all_participants:
        if participant["group_title"] == target_group.title:
            target_group_participants = participant["group_data"]
            
    print(len(target_group_participants))
    mention_member = member_widget.get("1.0",END)
    delay_time = delay_widget.get("1.0",END)

    message_index = 0
    chat_message = ""
    while not stop_event.wait(1):
        try:
            index = 0
            while index < len(target_group_participants) and not stop_event.wait(1):
                msg_text = message_widget.get("1.0",END)+"\n"
                members = target_group_participants[index:index+int(mention_member)]
                for member in members:
                    if member.first_name: first_name= member.first_name
                    else: first_name= ""
                    if member.last_name: last_name= member.last_name
                    else: last_name= ""
                    username = first_name + last_name
                    if username == "":
                        username = "None"
                    msg_text+=f'<a href="tg://user?id={member.id}">{username}</a> '
                
                if delete_message_flag == True and message_index > 0:
                    if pin_message_flag == True:
                        print("PIN_MSG")
                        try:
                            if target_group.megagroup == True:
                                last_msg = bot.get_chat(f"-100{target_group.id}")
                        except:
                            last_msg = bot.get_chat(f"-{target_group.id}")
                        pin_msg_id = last_msg.pinned_message.id+1
                        try:
                            if target_group.megagroup == True:
                                last_msg = bot.delete_message(f"-100{target_group.id}",pin_msg_id)
                        except:
                            last_msg = bot.delete_message(f"-{target_group.id}",pin_msg_id)
                    try:
                        if target_group.megagroup == True:
                            bot.unpin_chat_message(f"-100{target_group.id}",chat_message.id)
                            bot.delete_message(f"-100{target_group.id}",chat_message.id)
                            
                        else:
                            bot.unpin_chat_message(f"-{target_group.id}",chat_message.id) 
                            bot.delete_message(f"-{target_group.id}",chat_message.id)
                            
                    except:
                        bot.unpin_chat_message(f"-{target_group.id}",chat_message.id) 
                        bot.delete_message(f"-{target_group.id}",chat_message.id)
                        
                try:
                    if target_group.megagroup == True:                
                        chat_message=bot.send_message(f"-100{target_group.id}", msg_text,parse_mode='HTML')
                    else:
                        chat_message=bot.send_message(f"-100{target_group.id}", msg_text,parse_mode='HTML')
                except:
                    chat_message=bot.send_message(f"-{target_group.id}", msg_text,parse_mode='HTML')
                
                if pin_message_flag == True:
                    try:
                        if target_group.megagroup == True:   
                            pin_message = bot.pin_chat_message(f"-100{target_group.id}",chat_message.id)
                        else:
                            pin_message = bot.pin_chat_message(f"-{target_group.id}",chat_message.id)
                    except:
                        bot.pin_chat_message(f"-{target_group.id}",chat_message.id)

                index = index + int(mention_member)
                message_index = message_index + 1
                time.sleep(int(delay_time))
        except:
            pass
def send_message():
    global my_thread, pill2kill,all_messages, groups

    pill2kill = threading.Event()
    my_thread = threading.Thread(target=send_message_thread,args=(pill2kill,))
    my_thread.start()

def stop_posting():
    global my_thread, pill2kill
    pill2kill.set()
    my_thread.join()
if __name__ == '__main__':
    connect()
    root = Tk()
    root.title("Geosoft")
    root.geometry('600x600')
    root.rowconfigure(0, weight=1)
    root.columnconfigure(tuple(range(10)), weight=1)

    left = Frame(root)
    left.rowconfigure(tuple(range(1)), weight=1)
    left.columnconfigure(0, weight=1)
    left.grid(row=0, column=0, sticky='news', padx=8, pady=8)

    settings = LabelFrame(left, text="Settings")
    settings.rowconfigure(tuple(range(20)), weight=1)
    settings.columnconfigure(tuple(range(1)), weight=1)
    settings.grid(row=0,column=0, sticky="news")
    pin_frame = LabelFrame(settings, text="Pin message")
    pin_frame.rowconfigure(tuple(range(2)),weight=1)
    pin_frame.grid(row=0, column=0, sticky="news")
    pin_message_var = StringVar()
    Radiobutton(pin_frame, text='Yes:', variable=pin_message_var, value="pin_message_yes", command=pin_radio_selected).grid(row = 0, column = 0, sticky='news', pady=10)
    Radiobutton(pin_frame, text='No:', variable=pin_message_var, value="pin_message_no", command=pin_radio_selected).grid(row = 1, column = 0, sticky='news', pady=10)


    
    delete_message_frame = LabelFrame(settings, text = "Delete Previous Message")
    delete_message_frame.rowconfigure(tuple(range(2)),weight=1)
    delete_message_frame.grid(row=5, column=0, sticky='news', pady=10)
    delete_message_var = StringVar()
    Radiobutton(delete_message_frame, variable=delete_message_var, text='Delete previous, Yes:', value="delete_previous_message_yes", command=delete_message_radio_selected).grid(row = 0, column = 0, sticky='news', pady=10)
    Radiobutton(delete_message_frame, variable=delete_message_var, text='No:', value="delete_previous_message_no", command=delete_message_radio_selected).grid(row = 1, column = 0, sticky='news', pady=10)

    other_options = LabelFrame(settings, text = "Other Options")
    other_options.rowconfigure(tuple(range(10)),weight=1)
    other_options.grid(row=10,column=0,sticky="news", pady=10)
    group_or_channel_var = StringVar()
    group_var = StringVar()
    group_option_menu = OptionMenu(other_options, group_var, *group_list).grid(row = 3, column = 0, sticky='news', pady=10)
    Label(other_options,text="Delay(in seconds):").grid(row = 4, column = 0, sticky='news', pady=10)
    delay_widget = Text(other_options, width=10, height=1)
    delay_widget.grid(row = 5, column = 0, sticky='news', pady=10)
    Label(other_options,text="Mentions each time").grid(row = 7, column = 0, sticky='news', pady=10)
    member_widget = Text(other_options, width=10, height=1)
    member_widget.grid(row = 8, column = 0, sticky='news', pady=10)
    message_widget = Text(root, width=50,height=75)
    message_widget.grid(row=0,column=1, sticky="news")
    Button(root, text = "Send", width=50, command=send_message).grid(row=1,column=1,sticky="news")
    Button(root, text = "Stop Repeating", width=50, command = stop_posting).grid(row=2,column=1,sticky="news")
    root.mainloop()
bot.polling()
