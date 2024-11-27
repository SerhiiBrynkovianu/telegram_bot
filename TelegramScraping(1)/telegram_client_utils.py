import os
import shutil
from telethon import TelegramClient, errors
from tkinter import simpledialog
import asyncio

SESSION_FOLDER = "sessions"
BANNED_FOLDER = "banned_sessions"
NONE_CODE_FOLDER = "no-sign"

async def request_code(phone, root):
    loop = asyncio.get_event_loop()
    future = loop.create_future()

    def ask():
        try:
            result = simpledialog.askstring("Enter Code", f"Enter the code for {phone}:")
            loop.call_soon_threadsafe(future.set_result, result)
        except Exception as e:
            loop.call_soon_threadsafe(future.set_exception, e)

    root.after(0, ask)
    return await future

def move_to_folder(session_file, folder):
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
        shutil.move(session_file, os.path.join(folder, os.path.basename(session_file)))
    except Exception as e:
        raise RuntimeError(f"Failed to move {session_file} to {folder}: {e}")

async def telegram_login(api_id, api_hash, phone, root, proxy, stop_callback=None, update_status_callback=None):
    if stop_callback and stop_callback():
        return None
    if not phone.startswith('+'):
        phone = '+' + phone  # Ensure phone number starts with '+'
    
    session_file = os.path.join(SESSION_FOLDER, f"{phone}.session")
    client = TelegramClient(session_file, api_id, api_hash, proxy=proxy)    
    try:
        await client.connect()
        if stop_callback and stop_callback():
            await client.disconnect()
            return None

        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            if update_status_callback:
                update_status_callback(f"Sent code request for {phone}")
            
            code = await request_code(phone, root)
            if stop_callback and stop_callback():
                await client.disconnect()
                await move_to_folder(session_file, NONE_CODE_FOLDER)
                return None

            if code:
                try:
                    await client.sign_in(phone, code)
                except Exception as e:
                    if update_status_callback:
                        update_status_callback(f"Failed to login for phone {phone}: {e}")
                    await client.disconnect()
                    await move_to_folder(session_file, NONE_CODE_FOLDER)
                    return None
            else:
                if update_status_callback:
                    update_status_callback(f"Login cancelled for phone {phone}.")
                await client.disconnect()
                await move_to_folder(session_file, NONE_CODE_FOLDER)
                return None

        if update_status_callback:
            update_status_callback(f"Logged in {phone}")
        return client
    except (errors.RPCError, OSError) as e:
        if update_status_callback:
            update_status_callback(f"Network or Proxy error for phone {phone} with proxy {proxy}: {e}")
        await client.disconnect()
        await move_to_folder(session_file, NONE_CODE_FOLDER)
        return None
    except Exception as e:
        if update_status_callback:
            update_status_callback(f"Exception during login for phone {phone}: {e}")
        await client.disconnect()
        await move_to_folder(session_file, NONE_CODE_FOLDER)
        return None