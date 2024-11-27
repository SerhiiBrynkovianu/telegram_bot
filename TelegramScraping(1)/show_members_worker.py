# show_members_worker.py
import asyncio
import random
from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch, ChannelParticipantsAdmins

class ShowMembersWorker:
    def __init__(self, api_keys, group_url, proxies, clients, update_status, update_members_listbox, update_members_count):
        self.api_keys = api_keys
        self.group_url = group_url
        self.proxies = proxies
        self.clients = clients
        self.update_status = update_status
        self.update_members_listbox = update_members_listbox
        self.update_members_count = update_members_count

    async def get_group_entity(self, client, group_url):
        try:
            return await client.get_entity(group_url)
        except Exception as e:
            self.update_status(f"Error fetching group entity: {e}")
            return None

    async def fetch_members(self, client, group_url):
        members = []
        try:
            group_entity = await self.get_group_entity(client, group_url)
            if not group_entity:
                self.update_status(f"Failed to get entity for group: {group_url}. Please check join state.")
                return members

            # Fetch all members
            offset = 0
            limit = 100  # Adjust limit as needed

            while True:
                participants = await client(GetParticipantsRequest(
                    group_entity, ChannelParticipantsSearch(''), offset, limit, hash=0
                ))

                members.extend(participants.users)

                if len(participants.users) < limit:
                    break

                offset += len(participants.users)

            # Fetch all admins
            participants_admin = await client(GetParticipantsRequest(
                group_entity, ChannelParticipantsAdmins(), 0, 100, hash=0
            ))

            members.extend(participants_admin.users)
        except Exception as e:
            self.update_status(f"Error fetching members: {e}")

        return members

    async def connect_client(self, client):
        try:
            await client.connect()
            if not await client.is_user_authorized():
                self.update_status("Client is not authorized. Please authorize the client.")
                return False
        except Exception as e:
            self.update_status(f"Failed to connect client with proxy : {e}")
            return False
        return True

    async def disconnect_client(self, client):
        if client.is_connected():
            await client.disconnect()

    async def initial(self):
        try:
            if len(self.clients) == 0:
                self.update_status("Please load sessions.")
                return

            all_members = []

            _client = self.clients[0]
            proxy = random.choice(self.proxies) if self.proxies else None
            api_key = random.choice(self.api_keys) if  self.api_keys else None
            values = api_key.split('-')
            api_id = int(values[0])
            api_hash = values[1]
            client = TelegramClient(_client.session.filename, api_id, api_hash, proxy=proxy)
            if await self.connect_client(client):
                members = await self.fetch_members(client, self.group_url)
                all_members.extend(members)
                await self.disconnect_client(client)

            # Process members to display their usernames
            unique_members = {}
            for member in all_members:
                username = member.username if member.username else f"{member.first_name or ''} {member.last_name or ''}".strip()
                if not username:
                    username = f"User_{member.id}"  # Fallback to a placeholder if no username or name is available
                if member.id not in unique_members:
                    unique_members[member.id] = username
            self.update_status(f"Loading finished")
            sorted_members = sorted(unique_members.values())

            self.update_members_listbox(sorted_members)
            self.update_members_count(len(unique_members))

        except Exception as e:
            self.update_status(f"Error showing members: {e}")

    def run(self):
        try:
            asyncio.run(self.initial())
        except Exception as e:
            self.update_status(f"Exception in Showmember.run: {e}")