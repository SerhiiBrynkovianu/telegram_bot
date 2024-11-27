import asyncio
import os
import shutil

import aiofiles
from time import sleep
import pytz
from typing import List
from datetime import datetime
from tkinter import Tk, simpledialog
import glob
from telethon import errors
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest, JoinChannelRequest,GetParticipantsRequest
from telethon.tl.functions.messages import CheckChatInviteRequest,ImportChatInviteRequest,GetDialogsRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import (
    ChannelParticipantsAdmins,
    ChannelParticipantsSearch,
    InputChannel,
    InputPeerChannel,
    InputPeerEmpty,
    InputUser,
    User,
    UserEmpty,
    UserStatusEmpty,
    UserStatusLastMonth,
    UserStatusLastWeek,
    UserStatusOffline,
    UserStatusOnline,
    UserStatusRecently,
)
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel, ChannelParticipantsAdmins
from telethon.tl.types import PeerChannel
from telethon_wrapper import TelethonWrapper
from telethon.tl.types import InputPeerEmpty


class AddMembersWorker():
    def __init__(self, api_keys, group_url,root, update_status_callback, 
                 thread_finished_callback, proxies, is_stop_requested, 
                 update_progress_bar_callback, clients, delay, 
                 refresh_groups_callback, addable_count, start_date,mode="multi",run_mode="add"):
        self.apis = api_keys
        self.groups = group_url
        self.root = root
        self.addable_count = int(addable_count)
        self.update_status = update_status_callback
        self.thread_finished = thread_finished_callback
        self.proxies = proxies
        self.is_stop_requested = is_stop_requested
        self.update_progress_bar = update_progress_bar_callback
        self.clients = clients
        self.delay = delay
        self.mode = mode 
        self.run_mode = run_mode
        self.refresh_groups_callback = refresh_groups_callback
        self.sessions = glob.glob("sessions/*.session")
        self.userlist = []
        self.all_users = []
        self.admin_ids = []
        self.start_date = start_date
    async def disconnect_all_clients(self, clients: List[TelegramClient]):
        for client in clients:
            try:
                if client.is_connected():
                    await client.disconnect()
            except Exception:
                pass

    async def join_groups(self, group, clients: List[TelegramClient]):
        cid = []
        ah = []
        for client in clients:
            if "/" in group:
                group_link = group.split("/+")[-1]
                try:
                    await client.connect()
                    try:
                        updates = await client(ImportChatInviteRequest(group_link))
                        cid.append(updates.chats[0].id)
                        ah.append(updates.chats[0].access_hash)
                    except Exception as e:
                        chatinvite = await client(CheckChatInviteRequest(group_link))
                        cid.append(chatinvite.chat.id)
                        ah.append(chatinvite.chat.access_hash)
                        print(e)
                        pass
                except Exception as e:
                    self.update_status(f"Error occured: {str(e)}")
            else:
                client_me = await client.get_me()
                print(client_me.phone, "joined group", group)
                group_entity_scrapped = await client.get_entity(group)
                updates = await client(JoinChannelRequest(group_entity_scrapped))
                cid.append(updates.chats[0].id)
                ah.append(updates.chats[0].access_hash)
        res = [cid, ah]
        return res

    def read_txt_proxy(self, proxy: str):
        splitted_line = proxy.split(":")
        proxy_dict = {}
        proxy_dict["addr"] = splitted_line[0]
        proxy_dict["port"] = int(splitted_line[1])
        proxy_dict["username"] = splitted_line[2]
        proxy_dict["password"] = splitted_line[3]
        proxy_dict["proxy_type"] = "socks5"
        proxy_dict["rdns"] = True

        return proxy_dict

    def get_clients_from_sessions(self):
        clients = []

        for session in self.sessions:
            try:
                # Move session
                self.phone = session.replace(".session", "")
                current_tg_api_id = None
                current_tg_hash = None
                if self.apis:
                    splitted_api_info = self.apis[0].split("-")
                    current_tg_api_id = splitted_api_info[0]
                    current_tg_hash = splitted_api_info[1]
                else:
                    raise self.update_status("No telegram api info found.")
                self.update_status(f"API_ID: {current_tg_api_id} | API_HASH: {current_tg_hash} Phone: {self.phone}")

                formatted_proxy = None
                current_proxy = None
                if self.proxies:
                    current_proxy = self.proxies[0]
                    formatted_proxy = self.read_txt_proxy(current_proxy)  # type: ignore
                    self.update_status(f"Proxy will be used: {formatted_proxy['addr']}")
                retry_count = 0
                while retry_count < 5:
                    try:
                        telegram_client = TelegramClient(
                            session=session,
                            api_id=current_tg_api_id,
                            api_hash=current_tg_hash,
                            base_logger=self.update_status,
                            proxy=formatted_proxy if formatted_proxy else {},
                        )
                        self.tw_instance = TelethonWrapper(
                            client=telegram_client,
                            phone=self.phone,
                        )

                        if not self.tw_instance.check_client_authorized():
                            self.delete_unsuccessful_session(self.phone)
                            raise self.update_status("Client not authorized")
                        break
                    finally:
                        retry_count += 1

                self.tw_instance.client.flood_sleep_threshold = 0
                clients.append(self.tw_instance.client)

                # Remove api
                self.apis.remove(self.apis[0])
                self.write_list_to_file(filename="api", new_list=self.apis)

                # Remove proxy
                if current_proxy and self.proxies:
                    self.proxies.remove(current_proxy)
                    self.write_list_to_file(filename="proxies", new_list=self.proxies)
            except Exception as e:
                self.update_status(f"Exception occured with {str(e)}")

        return clients

    def write_list_to_file(self, filename: str, new_list: List[str]):
        new_list = [elem + "\n" for elem in new_list]  # type: ignore
        if new_list:
            new_list[-1] = new_list[-1].replace("\n", "")  # last element no new line
        with open(f"{filename}.txt", "w") as fh:
            fh.writelines(new_list)

    def delete_unsuccessful_session(self, phone: str):
        if self.tw_instance and self.tw_instance.client:
            self.tw_instance.client.disconnect()
            if os.path.isfile(f"sessions\\{phone}.session"):
                os.remove(f"sessions\\{phone}.session")

    async def move_current_session(self, client: TelegramClient):
        if client.is_connected():
            client_me = await client.get_me()
            phone = client_me.phone
            await client.disconnect()
    
        session = f"sessions\\{phone}.session"
        if not os.path.exists(session):
            session = f"sessions\\{phone}.session"
        if os.path.exists(session):
            shutil.move(session, f"finished_sessions\\{phone}.session")
        else:
            raise Exception(f"Session file not found {session}. So it cannot be moved.")

    def save_scrape(self):
        with open("scrape_users.txt","w") as file:
            for users in self.all_users:
                file.write(f"{users}\n")

    def remove_username(self, username):
        if username in self.userlist:
            self.userlist.remove(username)
            try:
                with open("users.txt", "w") as file:
                    file.write("\n".join(self.userlist))
                self.update_status(f"Removed username {username} from users.txt.")
            except Exception as e:
                self.update_status(f"Failed to remove username {username} from users.txt: {e}")

    async def get_admins(self,client:TelegramClient):
        # Get the list of admins in the group
        group = await client.get_entity(self.groups)
        admins = await client.get_participants(group, filter=ChannelParticipantsAdmins)
        return {admin.id for admin in admins}  # Set of admin IDs
    
    async def scrape_users_to_group(self,client:TelegramClient,start_offset,end_offset):
        limit = 1000  # Number of messages to fetch per request
        offset_id = end_offset  # ID of the last message to continue fetching
        group = await client.get_entity(self.groups)

        while True:
            # Fetch the message history starting from the specific date
            history = await client(GetHistoryRequest(
                peer=PeerChannel(group.id),
                limit=limit,
                offset_date=self.start_date,
                offset_id=offset_id,
                min_id=start_offset-1,
                max_id=end_offset if end_offset else 0,
                add_offset=0,
                hash=0
            ))

            if not history.messages:  # No more messages to fetch
                break

            # Filter for text messages only and get sender's username
            for message in history.messages:
                try:
                    # Fetch the user details of the sender
                    sender = await client.get_entity(message.sender_id)
                    # Check if the user has a username; otherwise, use full name
                    if sender.id not in self.admin_ids and sender.username:
                        username = sender.username
                    if not username in self.all_users:
                        self.all_users.append(username)
                        self.update_status(f"{username} is scraped from group")
                        with open("scrape_users.txt","w") as file:
                            for users in self.all_users:
                                file.write(f"{users}\n")
                except Exception as e:
                    print(f"Error fetching user for message {message.id}: {e}")

            # Update the offset_id to fetch the next batch
            offset_id = history.messages[-1].id
        return self.all_users
    async def add_users_to_groups(self, client: TelegramClient, userlist: List, group_info: List, counter: int):
        peer_flooded = []
        too_many_request = []
        wait_seconds = []
        other_exceptions = []
        try:
            [cid, ah] = group_info
        except Exception as e:
            print(str(e))
            await self.move_current_session(client)
            return (userlist, {client: False})
        client_reusable = True
        client_me = await client.get_me()
        phone = client_me.phone
        for index, user in enumerate(userlist, 1):
            try:
                __user = await client.get_entity(user)

                self.update_status(f"Adding user : {user} by {str(phone)}")
                self.remove_username(user)
                await client(
                    InviteToChannelRequest(
                        InputChannel(cid[counter], ah[counter]),
                        [__user],
                    )
                )
                peer_flooded = []
                too_many_request = []
                wait_seconds = []
                other_exceptions = []
                await asyncio.sleep(self.delay)
            except errors.FloodWaitError as e:
                if e.seconds > 100:
                    print("Flood for", e.seconds)
                    try:
                        await self.move_current_session(client)
                    except Exception:
                        self.update_status("Cannot move to session.")
                    await self.disconnect_all_clients(clients=[client])
                    client_reusable = False
                    break
                await asyncio.sleep(e.seconds)
            except errors.UserPrivacyRestrictedError as e:
                await asyncio.sleep(self.delay)
                self.update_status(str(e))
                continue
            except errors.UserIdInvalidError as e:
                await asyncio.sleep(self.delay)
                self.update_status(str(e))
                continue
            except Exception as e:
                await asyncio.sleep(self.delay)
                if "PEER_FLOOD" in str(e):
                    peer_flooded.append(user)
                    if len(peer_flooded) > 7:
                        self.update_status(f"Account {str(phone)} peer flooded {str(len(peer_flooded))} times")
                        client_reusable = False
                        try:
                            await self.move_current_session(client)
                        except Exception:
                            self.update_status("Cannot move to session.")
                        peer_flooded = []
                        await self.disconnect_all_clients(clients=[client])
                        break
                elif "privacy" in str(e):
                    await asyncio.sleep(self.delay)
                elif "Too many requests" in str(e):
                    await asyncio.sleep(self.delay)
                    too_many_request.append(user)
                    if len(too_many_request) > 7:
                        self.update_status(f"Account {str(phone)} Too many request {str(len(too_many_request))} times")
                        try:
                            await self.move_current_session(client)
                        except Exception:
                            self.update_status("Cannot move to session.")
                        too_many_request = []
                        await self.disconnect_all_clients(clients=[client])
                        client_reusable = False
                        break
                elif "wait" in str(e):
                    await asyncio.sleep(self.delay)
                    wait_seconds.append(user)
                    if len(wait_seconds) > 7:
                        self.update_status(
                            f"Account {str(phone)} after wait seconds is required {str(len(wait_seconds))} times"
                        )
                        try:
                            await self.move_current_session(client)
                        except Exception:
                            self.update_status("Cannot move to session.")
                        await self.disconnect_all_clients(clients=[client])
                        client_reusable = False
                        break
                elif "entity for PeerUser" in str(e):
                    await asyncio.sleep(self.delay)
                elif "privacy" not in str(e):
                    await asyncio.sleep(self.delay)
                    other_exceptions.append(user)
                    if len(other_exceptions) > 7:
                        self.update_status(f"Account {str(phone)} after other errors {str(len(other_exceptions))} times")
                        try:
                            await self.move_current_session(client)
                        except Exception:
                            self.update_status("Cannot move to session.")
                        other_exceptions = []
                        await self.disconnect_all_clients(clients=[client])
                        self.update_status("all accounts other error occurs")
                        client_reusable = False
                        break
                elif "Keyboard" in str(e):
                    await asyncio.sleep(self.delay)
                    try:
                        await self.move_current_session(client)
                    except Exception:
                        self.update_status("Cannot move to session.")
                    client_reusable = False
                    break
                self.update_status(e)
                pass

        self.update_status(f"Adding Completed for #{str(index)} users.")
        self.thread_finished()
        return (userlist[index:] if index != (len(userlist) - 1) else [], {client: client_reusable}, userlist[:index])
    
    async def get_message_id_range(self,client:TelegramClient):

        # Get the group by its link or ID
        group = await client.get_entity(self.groups)

        # Fetch the latest (newest) message to get the highest message ID
        latest_history = await client(GetHistoryRequest(
            peer=PeerChannel(group.id),
            limit=1,  # Fetch only one message
            offset_date=self.start_date,
            offset_id=0,  # No offset; get the most recent message
            min_id=0,
            max_id=0,
            add_offset=0,
            hash=0
        ))
        latest_message_id = latest_history.messages[0].id if latest_history.messages else None

        # Fetch the first (oldest) message to get the lowest message ID
        oldest_history = await client(GetHistoryRequest(
            peer=PeerChannel(group.id),
            limit=1,  # Fetch only one message
            offset_date=self.start_date,
            offset_id=999999999,  # A very high number to ensure we get the first message
            min_id=0,
            max_id=0,
            add_offset=0,
            hash=0
        ))
        oldest_message_id = oldest_history.messages[0].id if oldest_history.messages else None
        return (latest_message_id,oldest_message_id)

    def get_group_to_scrape(self, list_of_groups: List[str]):
        text = r"Please enter number of group to scrape users: \n"
        i = 0
        for g in list_of_groups:
            text += f"{str(i)} -  {g.title} \n"
            i += 1

        new_win = Tk()
        new_win.withdraw()
        group_no = simpledialog.askinteger(
            "Group to Scrape", text, parent=new_win, minvalue=0, maxvalue=(len(list_of_groups) - 1)
        )

        new_win.destroy()

        return list_of_groups[group_no]

    def get_necessary_info(self, client: TelegramClient):
        chats = []
        last_date = None
        chunk_size = 100
        i = 0
        groups = []
        targets = []
        while True:
            if i >= 1:
                break
            result = client(
                GetDialogsRequest(
                    offset_date=last_date, offset_id=0, offset_peer=InputPeerEmpty(), limit=chunk_size, hash=0
                )
            )
            chats.extend(result.chats)
            if not result.messages:
                break
            for msg in chats:
                try:
                    mgg = msg.megagroup  # type: ignore # noqa
                except Exception:
                    continue
                if msg.megagroup == True:
                    groups.append(msg)
                try:
                    if msg.access_hash is not None:
                        targets.append(msg)
                except Exception:
                    pass
            i += 1
            sleep(1)

        return groups

    async def scrape_users_from_groups(self, client: TelegramClient, group):
        all_participants = []
        limit = 1000

        admins = await client(
            GetParticipantsRequest(
                channel=InputPeerChannel(group.id, group.access_hash),
                filter=ChannelParticipantsAdmins(),
                offset=0,
                limit=limit,
                hash=0,
            )
        )
        client.flood_sleep_threshold = 100
        try:
            async for participant in client.iter_participants(group, aggressive=True):
                all_participants.append(participant)

        except Exception as e:
            self.update_status(f"Cannot extract users due to : {str(e)}")

        # all_participants.extend(list(participants))
        await asyncio.sleep(1)
        self.update_status(len(all_participants))
        self.update_status(
            f"{str(client._self_id)} extracted length of groups - {str(len(all_participants))}",
        )
        # Filter out admins
        self.update_status("Filtering out admin accounts...")
        all_participants = [participant for participant in all_participants if participant not in admins.users]

        return all_participants

    async def save_scraped_list(self, all_participants: List):
        try:
            self.update_status("Saving user list...")
            async with aiofiles.open(
                    rf"scrape_users.txt", "a", encoding="utf-8", errors="ignore"
                ) as f:
                    for item in all_participants:
                        if item.username is not None:
                            await f.write("%s\n" % (item.username))

            self.update_status("Saving Done...")
        except Exception as e:
            self.update_status("Error occured during saving...")
            self.update_status(e)

    def run(self):
        self.running = True
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        clients = []
        try:
            clients = self.get_clients_from_sessions()
            if not self.groups:
                raise Exception("No group given for adding users.")
            
            if self.run_mode == "add_mode":
                group_info = loop.run_until_complete(self.join_groups(self.groups, clients))

                with open("users.txt", "r", encoding="utf-8", errors="ignore") as f:
                    _temp = f.read()
                    userlist = _temp.split("\n")
                    userlist = userlist[:-1]
                    self.userlist = userlist
                if self.mode == "multi":
                    tasks = []
                    counter = 0
                    # total_divider = int(len(userlist) / len(clients))
                    total_divider = self.addable_count
                    # append tasks for each client
                    for client in clients:
                        if counter == (len(clients) - 1) and len(userlist)-counter*total_divider<total_divider:
                            tasks.append(
                                self.add_users_to_groups(
                                    client=client,
                                    userlist=userlist[counter * total_divider :],
                                    group_info=group_info,
                                    counter=counter,
                                )
                            )
                            break

                        tasks.append(
                            self.add_users_to_groups(
                                client=client,
                                userlist=userlist[
                                    counter * total_divider : (counter * total_divider + total_divider)
                                ],
                                group_info=group_info,
                                counter=counter,
                            )
                        )
                        counter += 1

                    result = loop.run_until_complete(asyncio.gather(*tasks))
                    self.update_status("Complete!")
                    userlist = []
                    clients = []

                    for user, client_stat, added_users in result:
                        userlist.extend(user)
                        for key, value in client_stat.items():
                            if value:
                                clients.append(key)

                    # self.write_users(userlist=userlist)
                elif self.mode == "single":
                    counter = 0
                    total_divider = self.addable_count
                    for client in clients:
                        # to stop processing further
                        if len(userlist) == 0:
                            self.update_status("No users found to add. Please first scrape users.")
                            break
                        # append tasks for each client
                        result = loop.run_until_complete(
                            self.add_users_to_groups(
                                client=client,
                                userlist=userlist[counter * total_divider : (counter * total_divider + total_divider)],
                                group_info=group_info,
                                counter=counter,
                            )
                        )

                        userlist.extend(result[0])

                        # self.write_users(userlist=userlist)
                        counter += 1
            else:
                tasks = []
                groups = self.get_necessary_info(clients[0])
                group1 = self.get_group_to_scrape(groups)
                # for client in clients:
                #     groups = self.get_necessary_info(client)
                #     group = [group for group in groups if group.id == group1.id][0]
                #     tasks.append(self.scrape_users_from_groups(client, group=group))
                # results = loop.run_until_complete(asyncio.gather(*tasks))

                group = [group for group in groups if group.id == group1.id][0]
                result = loop.run_until_complete(self.scrape_users_from_groups(clients[0],group=group))

                self.clean_up_duplicates_from_files("scrape_users")
                # for result in results:
                self.update_status("Filter out added users.")
                local = pytz.timezone("UTC")
                last_month_date = local.localize(datetime.utcnow())
                last_week_date = local.localize(datetime.utcnow())
                total_participants = []
                user_recent = [user for user in result if isinstance(user.status, UserStatusRecently)]
                user_online = [user for user in result if isinstance(user.status, UserStatusOnline)]
                user_lastmonth = []
                if (datetime.now().date() - self.start_date).days > 30:
                    user_lastmonth = [user for user in result if isinstance(user.status, UserStatusLastMonth)]
                user_lastweek = []
                if (datetime.now().date() - self.start_date).days > 7:
                    user_lastweek = [user for user in result if isinstance(user.status, UserStatusLastWeek)]

                user_offline = [user for user in result if isinstance(user.status, UserStatusOffline)]
                # Filter with main date
                user_offline = list(
                    filter(
                        lambda user: (user.status.was_online.date() >= self.start_date),
                        user_offline,
                    )
                )
                user_offline.sort(key=lambda user: user.status.was_online, reverse=True)

                user_offline_last_week = list(
                    filter(
                        lambda user: user.status.was_online >= last_week_date,
                        user_offline,
                    )
                )
                user_offline_last_month = list(
                    filter(
                        lambda user: (user.status.was_online >= last_month_date)
                        and (user.status.was_online < last_week_date),
                        user_offline,
                    )
                )
                user_older_than_a_month = list(
                    filter(
                        lambda user: user.status.was_online < last_month_date,
                        user_offline,
                    )
                )

                total_participants.extend(user_online)
                total_participants.extend(user_recent)
                total_participants.extend(user_offline_last_week)
                total_participants.extend(user_lastweek)
                total_participants.extend(user_offline_last_month)
                total_participants.extend(user_lastmonth)
                total_participants.extend(user_older_than_a_month)

                loop.run_until_complete(self.save_scraped_list(total_participants))

                self.update_status("Scraping Completed")

                self.clean_up_duplicates_from_files("scrape_users")
                self.update_status("Complete!!!")
                self.thread_finished()
        except Exception as e:
            self.update_status(f"Unexpected exception occured: {str(e)}")
            self.update_status("Complete!!!")
            self.thread_finished()

        for client in clients:
            try:
                client.disconnect()
            except Exception:
                continue
   
    def write_users(self, userlist):
        with open("users.txt", "w+") as f:
            n_userlist = ["{}\n".format(user) for user in userlist]
            f.writelines(n_userlist)

    def clean_up_duplicates_from_files(self, filename: str):
        with open(rf"{filename}.txt", "r", encoding="utf-8", errors="ignore") as f:
            extracted_users = f.readlines()

        # remove duplicates
        with open(rf"{filename}.txt", "w+", encoding="utf-8", errors="ignore") as f:
            extracted_users = list(set(extracted_users))
            f.writelines(extracted_users)
