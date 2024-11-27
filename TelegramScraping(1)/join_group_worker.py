import asyncio
import random
import os
import shutil
from telethon import TelegramClient, errors
from telethon.errors.rpcerrorlist import InviteHashExpiredError
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest

class JoinGroupWorker:
    def __init__(self, group_url, clients, update_status_callback, is_stop_requested, update_progress_bar, proxies, api_keys,temp):
        self.group_url = group_url
        self.clients = clients
        self.update_status = update_status_callback
        self.is_stop_requested = is_stop_requested
        self.update_progress_bar = update_progress_bar
        self.semaphore = asyncio.Semaphore(20)
        self.proxies = proxies
        self.api_keys = api_keys
        self.temp = temp

    async def ensure_connected(self, client):
        if not client.is_connected():
            try:
                await client.connect()
                if not await client.is_user_authorized():
                    if self.temp:
                        self.update_status("Client is not authorized. Please authorize the client.")
                    return False
            except Exception as e:
                if self.temp:
                    self.update_status(f"Failed to connect client with proxy : {e}")
                return False
        return True

    async def join_group(self, _client):
        async with self.semaphore:
            proxy = random.choice(self.proxies) if self.proxies else None
            api_key = random.choice(self.api_keys) if  self.api_keys else None
            values = api_key.split('-')
            api_id = int(values[0])
            api_hash = values[1]
            client = TelegramClient(_client.session.filename, api_id, api_hash, proxy=proxy)
            await self.ensure_connected(client)

            try:
                if 'joinchat' in self.group_url or '+' in self.group_url:
                    invite_hash = self.group_url.split('/+')[-1]
                    ss=await client(ImportChatInviteRequest(invite_hash))
                else:
                    await client(JoinChannelRequest(self.group_url))
                if self.temp:
                    self.update_status(f"Client {client.session.filename} joined group {self.group_url}.")
            except errors.UserAlreadyParticipantError:
                if self.temp:
                    self.update_status(f"Client {client.session.filename} is already a member of the group {self.group_url}.")
                
            except InviteHashExpiredError:
                if self.temp:
                    self.update_status(f"Invite link for group {self.group_url} has expired or is invalid.")
                await self.move_current_session(client)
            except Exception as e:
                if self.temp:
                    self.update_status(f"Failed to join group {self.group_url} with client {client.session.filename}: {e}")
                await self.move_current_session(client)
            finally:
                if client.is_connected():
                    await client.disconnect()

    async def move_current_session(self, client: TelegramClient):
        if client.is_connected():
            client_me = await client.get_me()
            phone = client_me.phone
            await client.disconnect()
    
        session = f"sessions\\{phone}.session"
        if not os.path.exists(session):
            session = f"sessions\\{phone}.session"
        if os.path.exists(session):
            shutil.move(session, f"no-sign\\{phone}.session")
        else:
            raise Exception(f"Session file not found {session}. So it cannot be moved.")
    async def join_groups(self):
        tasks = [self.join_group(client) for client in self.clients]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                if self.temp:
                    self.update_status(f"Error joining group with client {self.clients[i].session.filename}: {result}")
            self.update_progress_bar(i + 1)

    def run(self):
        try:
            asyncio.run(self.join_groups())
        except Exception as e:
            if self.temp:
                self.update_status(f"Exception in JoinGroupWorker.run: {e}")