import os
import random
import asyncio
import time
from telethon import TelegramClient
from telethon.errors import RPCError, FloodWaitError, SessionPasswordNeededError
from telegram_client_utils import move_to_folder
from asyncio import TimeoutError

SESSION_FOLDER = "sessions"
BANNED_FOLDER = "banned_sessions"
NONE_CODE_FOLDER = "no-sign"

class SessionInitWorker:
    def __init__(self, api_keys, sessions, update_status_callback, finished_callback, proxies, stop_callback, update_progress_callback, clients, con_count=10, connect_timeout=10, max_retries=2, base_backoff=1):
        self.api_keys = api_keys
        self.sessions = sessions
        self.clients = clients
        self.update_status_callback = update_status_callback
        self.finished_callback = finished_callback
        self.stop_callback = stop_callback
        self.update_progress_callback = update_progress_callback
        self.banned_numbers = clients
        self.con_count = con_count  # Maximum number of concurrent sessions
        self.semaphore = asyncio.Semaphore(10)
        self.proxies = proxies
        self.connect_timeout = connect_timeout  # Timeout for client.connect()
        self.max_retries = max_retries  # Maximum number of retry attempts
        self.base_backoff = base_backoff  # Base backoff time for retries

    async def telegram_login(self, session_file):
        async with self.semaphore:  # Limit concurrent sessions
            if self.stop_callback():
                return None
                
            phone = os.path.splitext(os.path.basename(session_file))[0]  # Extract phone number from session file name
            if not phone.startswith('+'):
                phone = '+' + phone  # Ensure phone number starts with '+'
            
            client = None
            for attempt in range(self.max_retries + 1):  # Allow for retries
                try:
                    proxy = random.choice(self.proxies) if self.proxies else None
                    api_key = random.choice(self.api_keys) if  self.api_keys else None
                    print(api_key)
                    values = api_key.split('-')
                    api_id = int(values[0])
                    api_hash = values[1]
                    client = TelegramClient(session_file, api_id, api_hash, proxy=proxy)
                    
                    await asyncio.wait_for(client.connect(), timeout=self.connect_timeout)
                    if self.stop_callback():
                        await client.disconnect()
                        return None
                    if not await client.is_user_authorized():
                        await client.disconnect()
                        self.update_status_callback(f"Failed to authorize session for phone {phone}. Moving to no-sign folder.")
                        await self.move_session_file(session_file, NONE_CODE_FOLDER)
                        return None
                    return client
                
                except TimeoutError:
                    self.update_status_callback(f"Connection timed out for {phone}. Attempt {attempt + 1}/{self.max_retries + 1}")
                    await client.disconnect()
                except (RPCError, OSError) as e:
                    err_str = str(e)
                    await client.disconnect()
                    if 'can no longer be used' in err_str:
                        await self.move_session_file(session_file, BANNED_FOLDER)
                    break  # Break on network errors without retrying
                except FloodWaitError as e:
                    self.update_status_callback(f"Flood wait error for session {session_file}: {e}")
                    break  # Break on flood wait error
                except SessionPasswordNeededError as e:
                    self.update_status_callback(f"Two-step verification needed for session {session_file}: {e}")
                    break  # Break on password needed error
                except Exception as e:
                    self.handle_unexpected_error(e, session_file, phone, client)
                    await client.disconnect()
                    break  # Break on unexpected errors

                # If we reach this point, we will retry
                if attempt < self.max_retries:
                    wait_time = self.base_backoff * (2 ** attempt)  # Exponential backoff
                    self.update_status_callback(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)  # Wait before retrying

            # After max retries, if client is still None, we handle it
            if client:
                await client.disconnect()
            return None

    async def move_session_file(self, session_file, target_folder):
        try:
            move_to_folder(session_file, target_folder)
        except Exception as e:
            self.update_status_callback(f"Failed to move {session_file} to {target_folder}: {e}")
            await asyncio.sleep(1)  # Wait before retrying

    def handle_unexpected_error(self, error, session_file, phone, client):
        error_str = str(error)
        if "database is locked" in error_str:
            self.update_status_callback(f"Database is locked for {session_file}. Retrying...")
            asyncio.sleep(2)  # Wait before retrying
        elif 'Server sent a very new message with ID' in error_str:
            self.update_status_callback(f"Server error for session {session_file}: {error}")
        elif 'banned' in error_str:
            self.update_status_callback(f"Phone {phone} has been banned. Moving to banned folder.")
            self.banned_numbers.append(phone)
            asyncio.run(self.move_session_file(session_file, BANNED_FOLDER))
        else:
            self.update_status_callback(f"Failed to initialize client for session {session_file}: {error}")

    async def initialize_clients(self):
        start_time = time.time()  # Record the start time
        tasks = [self.telegram_login(session_file) for session_file in self.sessions]

        for i, task in enumerate(asyncio.as_completed(tasks), start=1):
            try:
                client = await task
                if self.stop_callback():
                    self.update_status_callback("Initialization stopped by user.")
                    break

                session_file = self.sessions[i - 1]
                phone = os.path.splitext(os.path.basename(session_file))[0]
                if not phone.startswith('+'):
                    phone = '+' + phone  # Ensure phone number starts with '+'
                
                if client:
                    self.clients.append(client)
                    self.update_status_callback(f"{phone} initialized successfully.")
                else:
                    self.update_status_callback(f"Client for session {session_file} not initialized.")
                self.update_progress_callback(i)
            except Exception as e:
                self.update_status_callback(f"Exception during client initialization for session {self.sessions[i-1]}: {e}")

        end_time = time.time()  # Record the end time
        elapsed_time = end_time - start_time  # Calculate the elapsed time
        self.update_status_callback(f"Total time for initialization: {elapsed_time:.2f} seconds")
        self.update_status_callback(f"Initialized {len(self.clients)} clients")
        self.finished_callback()  # Ensure the callback is called to update the GUI state

        # Ensure all clients are disconnected on exit
        for client in self.clients:
            await client.disconnect()

    def run(self):
        try:
            asyncio.run(self.initialize_clients())
        except Exception as e:
            self.update_status_callback(f"Exception in SessionInitWorker.run: {e}")