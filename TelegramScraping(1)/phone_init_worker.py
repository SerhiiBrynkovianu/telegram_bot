import os
import random
import asyncio
from telegram_client_utils import telegram_login
from proxy_utils import parse_proxy

SESSION_FOLDER = "sessions"
BANNED_FOLDER = "banned_sessions"
NONE_CODE_FOLDER = "no-sign"
PHONES_FILENAME = "phones.txt"

class PhoneInitWorker:
    def __init__(self, api_keys, phones_list, update_status_callback, finished_callback, proxies, stop_callback, update_progress_callback, clients, root, max_concurrent_connections=10):
        self.api_keys = api_keys
        self.phones_list = phones_list
        self.clients = clients
        self.code = None
        self.update_status_callback = update_status_callback
        self.finished_callback = finished_callback
        self.stop_callback = stop_callback
        self.update_progress_callback = update_progress_callback
        self.root = root
        self.proxies = proxies
        self.semaphore = asyncio.Semaphore(1)

    def validate_proxy(self, proxy):
        try:
            parse_proxy(proxy)
            return True
        except ValueError as e:
            self.update_status_callback(f"Proxy validation error: {e}")
            return False

    async def initialize_clients(self):
        total_phones = int(len(self.phones_list))
        for i in range(total_phones):
            if self.stop_callback():
                self.update_status_callback("Initialization stopped by user.")
                return
            proxy = random.choice(self.proxies) if self.proxies else None
            api_key = random.choice(self.api_keys) if  self.api_keys else None
            values = api_key.split('-')
            api_id = int(values[0])
            api_hash = values[1]
            self.update_status_callback(f"Initializing client for phone {self.phones_list[i]} ({i + 1}/{total_phones})")
            try:
                client = await telegram_login(api_id, api_hash, self.phones_list[i], self.root, proxy, self.stop_callback, self.update_status_callback)
                if isinstance(client, Exception):
                    self.update_status_callback(f"Failed to initialize client for phone {self.phones_list[i-1]}: {client}")
                elif client:
                    self.update_status_callback(f"Client for phone {self.phones_list[i-1]} initialized successfully.")
                    self.update_progress_callback(i)
                    self.phones_list.remove(self.phones_list[i])
                    try:
                        with open(PHONES_FILENAME, "w") as file:
                            file.write("\n".join(self.phones_list))
                    except Exception as e:
                        self.update_status(f"Failed to remove invalid phone : {self.phones_list[i]} from phones.txt: {e}")
                    client.disconnect()
                else:
                    self.update_status_callback(f"Client for phone {self.phones_list[i-1]} not initialized.")
            except Exception as e:
                self.update_status_callback(f"Exception during task execution for phone {self.phones_list[i-1]}: {e}")
        
        self.update_status_callback(f"Initialized {len(self.clients)} clients")
        self.finished_callback()

    def run(self):
        try:
            asyncio.run(self.initialize_clients())
        except Exception as e:
            self.update_status_callback(f"Exception in PhoneInitWorker.run: {e}")
