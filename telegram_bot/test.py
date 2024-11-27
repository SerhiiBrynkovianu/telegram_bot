import subprocess
import time
import pycountry
import requests
import phonenumbers
import xml.etree.ElementTree as ET
import logging
import tkinter as tk
import threading
from tkinter import ttk
from PIL import Image
import pytesseract
import os
import re
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import asyncio

logging.basicConfig(level=logging.INFO)


class TelegramBotUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Automatic")
        self.country_names = []
        self.api_id="1149742"
        self.api_hash="51fcee2d03ef60ba96766c19a8e8b13b"
        self.right_bottom=0
        self.create_widgets()

    def load_country(self,file_path):
        with open(file_path, "r", encoding='utf-8') as file:
            for line in file.readlines():
                country_name = line.strip()
                self.country_names.append(country_name)

    def create_widgets(self):

        tk.Label(self.root,text="Input the Api key:").grid(row=1,column=0,padx=5,pady=5)
        self.api_key_item = tk.Entry(self.root,width=20)
        self.api_key_item.grid(row=1,column=1,padx=5,pady=5)

        tk.Label(self.root,text="Input the count:").grid(row=2,column=0,padx=5,pady=5)
        self.account_num_item = tk.Entry(self.root, width=5)
        self.account_num_item.grid(row=2,column=1,padx=5,pady=5)

        tk.Label(self.root,text="Add the country:").grid(row=3,column=0,padx=5,pady=5)
        self.add_country_item = tk.Entry(self.root,width=10)
        self.add_country_item.grid(row=3,column=1,padx=5,pady=5)


        self.run_button = tk.Button(self.root,text="Run",command=self.run,width=10,height=5)
        self.run_button.grid(row=4,column=1,padx=5,pady=5)

    def run_adb_command(self,command, device="127.0.0.1:5555"):
        """Function to run adb commands for a specific device using subprocess."""
        adb_command = f'adb -s {device} {command}'
        result = subprocess.run(adb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print(f"Success: {result.stdout}")
        else:
            print(f"Error: {result.stderr}")
        return result.stdout

    def connect_to_ldplayer(self):
        """Connect ADB to LDPlayer."""
        print("Connecting to LDPlayer...")
        self.run_adb_command("connect 127.0.0.1:5555", device="")

        devices = self.run_adb_command("devices", device="")
        print(f"ADB Devices: {devices}")
        if "127.0.0.1:5555" in devices:
            print("Successfully connected to LDPlayer on 127.0.0.1:5555.")
        else:
            print("Failed to connect to LDPlayer.")

    def launch_telegram_x(self,device="127.0.0.1:5555"):
        """Launch Telegram X app."""
        print("Launching Telegram X...")
        self.run_adb_command("shell monkey -p org.thunderdog.challegram -c android.intent.category.LAUNCHER 1", device)

    def tap_screen(self,x, y, device="127.0.0.1:5555"):
        """Simulate a tap at the specified coordinates."""
        print(f"Tapping on coordinates ({x}, {y})...")
        self.run_adb_command(f"shell input tap {x} {y}", device)


    def fetch_verification_code(self, request_number_url, max_retries=5):
        """Fetch verification code with retries on failure."""
        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(request_number_url)
                number_data = response.json()
                if number_data['msg'] == "error":
                    print(f"Error fetching code, retrying... ({retries + 1}/{max_retries})")
                    retries += 1
                    resource_id="org.thunderdog.challegram:id/btn_forgotPassword"
                    bounds = self.find_element_bounds("window_dump.xml", resource_id)
                    if bounds:
                        self.tap_on_element(bounds, device="127.0.0.1:5555")
                    time.sleep(5)  # Small delay before retrying
                else:
                    return number_data['result']['code']  # Return the verification code
            except Exception as e:
                print("error:"+str(e))
                break
        
        print("Failed to fetch verification code after retries.")
        return None

    def clear_input_field(self, device="127.0.0.1:5555", repeat=10):
        """Simulate pressing the backspace key multiple times to clear the input field."""
        print("Clearing input field...")
        for _ in range(repeat):
            self.run_adb_command(f"shell input keyevent 67", device)  # Keyevent 67 is the backspace key

    async def add_new_account(self, device="127.0.0.1:5555"):
        # Tap the screen to start
        self.tap_screen(80, 80, device=device)
        self.dump_window_hierarchy(device)
        
        # Find and tap on the 'account' resource
        resource_id = "org.thunderdog.challegram:id/account"
        bounds = self.find_element_bounds("window_dump.xml", resource_id)
        if bounds:
            self.tap_on_element(bounds, device)
        
        time.sleep(1)
        
        # Tap again, capture the screen, and save the image locally
        self.tap_screen(80, 80, device=device)
        time.sleep(1)
        
        # Capture screenshot
        os.system(f'adb -s {device} shell screencap /sdcard/screen_1.png')
        
        # Pull screenshot to local machine
        os.system(f'adb -s {device} pull /sdcard/screen_1.png')
        print("Screenshot 'screen_1.png' captured and saved locally.")
        
        # Optional: Scroll down the screen
        os.system(f'adb -s {device} shell input swipe 500 1500 500 500 500')
        
        # Open the screenshot and crop the region
        img = Image.open('screen_1.png')
        self.right_bottom = self.get_first_bounds("window_dump.xml")
        if self.right_bottom==1080:
            cropped_img = img.crop((0, 420, 600, 500))  # Adjust the coordinates as needed
        elif self.right_bottom==900 or self.right_bottom==720:
            cropped_img=img.crop((0,280,600,330))
        elif self.right_bottom==540:
            cropped_img = img.crop((0,210,600,250))
        else:
            cropped_img = img.crop((0,210,600,500))
        # Set Tesseract command path (adjust if necessary)
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
        
        # Save the cropped image
        cropped_img.save("crop.png")
        
        # Apply OCR to extract numbers
        try:
            text = pytesseract.image_to_string(cropped_img)
            numbers = re.findall(r'\d+', text)
            phone_num = ''.join(numbers)
            
            if not phone_num:
                print("No phone number found.")
                return
            
            print(f"Extracted phone number: {phone_num}")
        except Exception as e:
            print(f"Error during OCR: {e}")
            return
        await self.create_session(phone_num)

    async def create_session(self, phone_number):
        # Initialize TelegramClient
        client = TelegramClient(phone_number, self.api_id, self.api_hash)

        # Connect to Telegram
        await client.connect()

        # Check if the client is already authorized
        if not await client.is_user_authorized():
            # If not authorized, send the code request
            await client.send_code_request(phone_number)
            # Ask the user to enter the received code
            # self.tap_screen(self.right_bottom-200,400,device="127.0.0.1:5555")
            # time.sleep(1)
        
            # # Capture screenshot
            # device = "127.0.0.1:5555"
            # os.system(f'adb -s {device} shell screencap /sdcard/screen_2.png')
            
            # # Pull screenshot to local machine
            # os.system(f'adb -s {device} pull /sdcard/screen_2.png')
            # print("Screenshot 'screen_2.png' captured and saved locally.")
            
            # # Open the screenshot and crop the region
            # img = Image.open('screen_2.png')
            # cropped_img = img.crop((50, 50, 600, 200))
            # # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
        
            # # Save the cropped image
            # cropped_img.save("crop.png")
            
            # # Apply OCR to extract numbers
            # try:
            #     text = pytesseract.image_to_string(cropped_img)
            #     numbers = re.findall(r'\d+', text)
            #     phone_num = ''.join(numbers)
                
            #     if not phone_num:
            #         print("No phone number found.")
            #         return
                
            #     print(f"Extracted phone number: {phone_num}")
            # except Exception as e:
            #     print(f"Error during OCR: {e}")
            #     return
            code = 1231323
            # Sign in the user with the provided code
            await client.sign_in(phone_number, code)

        # Once logged in, the session is saved automatically in a session file
        print(f"Session created and saved as '{phone_number}.session'.")
        # You can use the client here to interact with the Telegram account
        await client.disconnect()

    def dump_window_hierarchy(self,device="127.0.0.1:5555"):
        """Dump the current UI hierarchy to a window_dump.xml file."""

        self.run_adb_command("shell uiautomator dump /sdcard/window_dump.xml", device)
        self.run_adb_command("pull /sdcard/window_dump.xml", device)

    def find_element_bounds(self,xml_file, resource_id=None):
        """Find the bounds of an element based on its resource-id."""

        tree = ET.parse(xml_file)
        root = tree.getroot()

        for node in root.iter('node'):
            node_id = node.attrib.get('resource-id')
            bounds = node.attrib.get('bounds')

            # Find the element with the matching resource-id
            if resource_id and resource_id == node_id:
                print(f"Found element with resource-id: {node_id}, bounds: {bounds}")
                return bounds
        return None
    
    def get_first_bounds(self,xml_file):
        tree = ET.parse(xml_file)  # Replace 'your_file.xml' with your actual XML file path
        root = tree.getroot()

        # Find the first 'node' element and retrieve its 'bounds' attribute
        first_node = root.find('.//node')
        if first_node is not None:
            bounds = first_node.get('bounds')
            print(f"First bounds: {bounds}")
            left_top, right_bottom = self.parse_bounds(bounds)
            return right_bottom[0]
        else:
            print("No node found.")
            return None

    def find_before_bounds(self,xml_file, resource_id=None):
        """Find the bounds of an element based on its resource-id."""

        tree = ET.parse(xml_file)
        root = tree.getroot()

        for elem in root.iter():
            if elem.attrib.get('class') == 'android.widget.TextView':
                parent_elem = elem.find('..')
                if parent_elem is not None:
                    bounds = parent_elem.attrib.get('bounds')
                    print(bounds)  # Output the bounds
                    return bounds
                return None

    def parse_bounds(self,bounds):
        """Parse the bounds string into coordinates."""

        bounds = bounds.strip('[]').split('][')
        left_top = list(map(int, bounds[0].split(',')))
        right_bottom = list(map(int, bounds[1].split(',')))
        return left_top, right_bottom

    def scroll_down(self,device="127.0.0.1:5555"):
        """Simulate scrolling down on the screen."""
        # Coordinates for scrolling: swipe from the bottom to the top of the screen
        print("Scrolling down...")
        self.run_adb_command(f"shell input swipe 100 900 100 300", device)
        time.sleep(5)  # Wait for the screen to settle after the scroll

    def tap_on_element(self,bounds, device="127.0.0.1:5555"):
        """Tap on the center of an element's bounds."""

        left_top, right_bottom = self.parse_bounds(bounds)
        x_center = (left_top[0] + right_bottom[0]) // 2
        y_center = (left_top[1] + right_bottom[1]) // 2
        self.tap_screen(x_center, y_center, device)

    def run(self):
        self.account = threading.Thread(target=self.start)
        self.account.start()
    def start(self):
        adb_command = f'adb connect 127.0.0.1:5555'
        result = subprocess.run(adb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.launch_telegram_x(device="127.0.0.1:5555")
        if result.returncode == 0:
            print(f"Success: {result.stdout}")
        else:
            print(f"Error: {result.stderr}")
        asyncio.run(self.add_new_account())

if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramBotUI(root)
    root.mainloop()
