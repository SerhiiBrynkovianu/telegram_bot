import subprocess
import time
import xml.etree.ElementTree as ET
import logging
import tkinter as tk
import threading
from PIL import Image,ImageOps, ImageEnhance
import pytesseract
import os
import re
from telethon import TelegramClient
import asyncio
import json

logging.basicConfig(level=logging.INFO)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class TelegramBotUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Automatic")
        self.country_names = []
        self.api_list=[]
        self.right_bottom=0
        self.size = 0
        self.setting_step = 0
        self.between_len = 0.0
        self.flag_mode=True
        self.run_modeflag = ""
        self.create_widgets()

    def create_widgets(self):
        self.varRadioSelection = tk.StringVar(value="all")  # Default selection is "session"

        # Create radio buttons for "Phone" and "Session"
        self.radio_all = tk.Radiobutton(self.root, text="Session and Json", variable=self.varRadioSelection, value="all", command=self.onRadioSelectionChanged)
        self.radio_all.grid(row=1,column=1,padx=5,pady=5)
        self.radio_only = tk.Radiobutton(self.root, text="Only Session", variable=self.varRadioSelection, value="only", command=self.onRadioSelectionChanged)
        self.radio_only.grid(row=1,column=2,padx=5,pady=5)
        self.run_button = tk.Button(self.root,text="Run",command=self.run,width=10,height=5)
        self.run_button.grid(row=4,column=1,padx=5,pady=5)

        self.runmodeRadioSelection = tk.StringVar(value="both")
        self.copy_numberRadio = tk.Radiobutton(self.root,text="Copy Number",variable=self.runmodeRadioSelection,value="copy_num",command=self.run_mode)
        self.copy_numberRadio.grid(row=2,column=1,padx=5,pady=5)
        self.only_createRadio = tk.Radiobutton(self.root,text="Only Create",variable=self.runmodeRadioSelection,value="only_create",command=self.run_mode)
        self.only_createRadio.grid(row=2,column=2,padx=5,pady=5)
        self.run_bothRadio = tk.Radiobutton(self.root,text="Both",variable=self.runmodeRadioSelection,value="both",command=self.run_mode)
        self.run_bothRadio.grid(row=2,column=3,padx=5,pady=5)
        if not os.path.exists("acc"):
            os.mkdir("acc")
        if not os.path.exists("api.txt"):
            with open("api.txt", "a",encoding="utf-8") as fh:
                fh.close()
        if not os.path.exists("saved_phone_number.txt"):
            with open("saved_phone_number.txt", "a",encoding="utf-8") as fh:
                fh.close()
        if not os.path.exists("phone_list.txt"):
            with open("phone_list.txt", "a",encoding="utf-8") as fh:
                fh.close()

    def run_mode(self):
        """Callback function when a radio button is selected"""
        selected_option = self.varRadioSelection.get()
        if selected_option == "copy_num":
            self.run_modeflag = "copy_num"
        elif selected_option=="only_create":
            self.run_modeflag = "only_create"
        else:
            self.run_modeflag = "both"

    def onRadioSelectionChanged(self):
        selected_option = self.runmodeRadioSelection.get()
        if selected_option == "all":
            self.flag_mode = True
        else:
            self.flag_mode = False
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

    async def add_new_account(self, device="127.0.0.1:5555"):
        self.tap_screen(80, 80, device=device)
        time.sleep(1)
        self.dump_window_hierarchy(device)
        if self.run_modeflag =="only_create":
            print()
        else:
            self.right_bottom = self.get_first_bounds("window_dump.xml")
            resource_id = "org.thunderdog.challegram:id/btn_setting"
            setting_bounds = self.find_element_bounds("window_dump.xml", resource_id)
            resource_id = "org.thunderdog.challegram:id/account"
            bounds_list = self.find_element_bounds("window_dump.xml", resource_id)
            bottom = self.get_bottom(bounds_list[-1])
            top = self.get_top(bounds_list[0])
            self.between_len = self.get_bt_length(bounds_list[1],bounds_list[0])
            for bounds in bounds_list:
                self.tap_on_element(bounds, device)
                time.sleep(1)   
                # Tap again, capture the screen, and save the image locally
                self.tap_screen(80, 80, device=device)
                time.sleep(1)
                resource_id="org.thunderdog.challegram:id/btn_settings"
                temp = self.find_element_bounds("window_dump.xml", resource_id)
                while not temp:
                    self.setting_scroll_down(True,device)
                    self.dump_window_hierarchy(device)
                    resource_id="org.thunderdog.challegram:id/btn_settings"
                    temp = self.find_element_bounds("window_dump.xml", resource_id)
                    self.setting_step = self.setting_step+1
                if temp:
                    self.tap_on_element(temp[0],device)
                    time.sleep(1)
                    self.dump_window_hierarchy(device)
                    resource_id="org.thunderdog.challegram:id/btn_phone"
                    temp1 = self.find_element_bounds("window_dump.xml", resource_id)
                    left_top,right_top = self.find_position(temp1[0])
                    os.system(f'adb -s {device} shell screencap /sdcard/screen_1.png')
            
                    os.system(f'adb -s {device} pull /sdcard/screen_1.png')
                    print("Screenshot 'screen_1.png' captured and saved locally.")
                    
                    img = Image.open('screen_1.png')
                    cropped_img = img.crop((left_top[0],left_top[1],right_top[0],right_top[1]))
                    cropped_img.save("processed_crop.png")
                    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
                    
                    try:
                        text = pytesseract.image_to_string(cropped_img)
                        numbers = re.findall(r'\d+', text)
                        phone_num = ''(numbers)
                        
                        if not phone_num:
                            print("No phone number found.")
                            continue
                        print(f"Extracted phone number: {phone_num}")
                    except Exception as e:
                        print(f"Error during OCR: {e}")
                        continue
                if os.path.exists("api.txt"):
                    with open("api.txt","r",encoding="utf-8") as fp:
                        self.api_list = fp.readlines()
                self.tap_screen(80,80,device)
                if self.run_modeflag != "copy_num":
                    await self.create_session(phone_num,self.api_list[0])
                time.sleep(2)
                self.tap_screen(80,80,device)
                time.sleep(1)
                while self.setting_step!=0:
                    self.setting_scroll_down(False,device)
                    self.setting_step = self.setting_step-1
                    time.sleep(1)
                time.sleep(1)

            while not setting_bounds:
                time.sleep(2)
                self.first_scroll_down(bottom,top,device)
                time.sleep(2)
                self.dump_window_hierarchy(device)
                resource_id = "org.thunderdog.challegram:id/btn_settings"
                setting_bounds = self.find_element_bounds("window_dump.xml", resource_id)
                resource_id = "org.thunderdog.challegram:id/account"
                bounds_list = self.find_element_bounds("window_dump.xml", resource_id)
                if setting_bounds:
                    for bounds in bounds_list:
                        self.tap_on_element(bounds, device)
                        time.sleep(1) 
                        self.tap_screen(80, 80, device=device)
                        time.sleep(1)
                        self.tap_on_element(setting_bounds[0],device)
                        time.sleep(1)
                        self.dump_window_hierarchy(device)
                        resource_id="org.thunderdog.challegram:id/btn_phone"
                        temp1 = self.find_element_bounds("window_dump.xml", resource_id)
                        left_top,right_top = self.find_position(temp1[0])
                        os.system(f'adb -s {device} shell screencap /sdcard/screen_1.png')
                
                        os.system(f'adb -s {device} pull /sdcard/screen_1.png')
                        print("Screenshot 'screen_1.png' captured and saved locally.")
                        
                        img = Image.open('screen_1.png')
                        cropped_img = img.crop((left_top[0],left_top[1],right_top[0],right_top[1]))
                        cropped_img.save("processed_crop.png")
                        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
                        
                        try:
                            text = pytesseract.image_to_string(cropped_img)
                            numbers = re.findall(r'\d+', text)
                            phone_num = ''.join(numbers)
                            
                            if not phone_num:
                                print("No phone number found.")
                                continue
                            
                            print(f"Extracted phone number: {phone_num}")
                        except Exception as e:
                            print(f"Error during OCR: {e}")
                            continue
                        if os.path.exists("api.txt"):
                            with open("api.txt","r",encoding="utf-8") as fp:
                                self.api_list = fp.readlines()
                        self.tap_screen(80,80,device)
                        if self.run_modeflag != "copy_num":
                            await self.create_session(phone_num,self.api_list[0])
                        time.sleep(2)
                        self.tap_screen(80,80,device)
                        time.sleep(1)
                else:
                    for bounds in bounds_list:
                        self.tap_on_element(bounds, device)
                        time.sleep(1)   
                        # Tap again, capture the screen, and save the image locally
                        self.tap_screen(80, 80, device=device)
                        time.sleep(1)
                        resource_id="org.thunderdog.challegram:id/btn_settings"
                        temp = self.find_element_bounds("window_dump.xml", resource_id)
                        while not temp:
                            self.setting_scroll_down(True,device)
                            self.dump_window_hierarchy(device)
                            resource_id="org.thunderdog.challegram:id/btn_settings"
                            temp = self.find_element_bounds("window_dump.xml", resource_id)
                            self.setting_step = self.setting_step+1
                        if temp:
                            self.tap_on_element(temp[0],device)
                            time.sleep(1)
                            self.dump_window_hierarchy(device)
                            resource_id="org.thunderdog.challegram:id/btn_phone"
                            temp1 = self.find_element_bounds("window_dump.xml", resource_id)
                            left_top,right_top = self.find_position(temp1[0])
                            os.system(f'adb -s {device} shell screencap /sdcard/screen_1.png')
                    
                            os.system(f'adb -s {device} pull /sdcard/screen_1.png')
                            print("Screenshot 'screen_1.png' captured and saved locally.")
                            
                            img = Image.open('screen_1.png')
                            cropped_img = img.crop((left_top[0],left_top[1],right_top[0],right_top[1]))
                            cropped_img.save("processed_crop.png")
                            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
                            
                            try:
                                text = pytesseract.image_to_string(cropped_img)
                                numbers = re.findall(r'\d+', text)
                                phone_num = ''.join(numbers)
                                
                                if not phone_num:
                                    print("No phone number found.")
                                    continue
                                
                                print(f"Extracted phone number: {phone_num}")
                            except Exception as e:
                                print(f"Error during OCR: {e}")
                                continue
                        if os.path.exists("api.txt"):
                            with open("api.txt","r",encoding="utf-8") as fp:
                                self.api_list = fp.readlines()
                        self.tap_screen(80,80,device)
                        if self.run_modeflag != "copy_num":
                            await self.create_session(phone_num,self.api_list[0])
                        time.sleep(2)
                        self.tap_screen(80,80,device)
                        time.sleep(1)
                        while self.setting_step!=0:
                            self.setting_scroll_down(False,device)
                            self.setting_step = self.setting_step-1
                            time.sleep(1)
                        time.sleep(1)
                        self.scroll_down(device)
                        time.sleep(1)
                        self.dump_window_hierarchy(device)
                        resource_id="org.thunderdog.challegram:id/btn_addAccount"
                        temp = self.find_element_bounds("window_dump.xml", resource_id)
                        self.tap_on_element(bounds_list[-1], device)
                    
                        time.sleep(1)
                        
                        # Tap again, capture the screen, and save the image locally
                        self.tap_screen(80, 80, device=device)
                        time.sleep(1)
                        
                        # Capture screenshot
                        os.system(f'adb -s {device} shell screencap /sdcard/screen_1.png')
                        
                        os.system(f'adb -s {device} pull /sdcard/screen_1.png')
                        print("Screenshot 'screen_1.png' captured and saved locally.")
                        
                        img = Image.open('screen_1.png')
                        self.right_bottom = self.get_first_bounds("window_dump.xml")
                        if self.right_bottom==1920:
                            cropped_img = img.crop((0, 420, 600, 500))  # Adjust the coordinates as needed
                        elif self.right_bottom==1600 or self.right_bottom==1280:
                            cropped_img=img.crop((0,280,600,330))
                        elif self.right_bottom==960:
                            cropped_img = img.crop((0,210,600,250))
                        else:
                            cropped_img = img.crop((0,210,600,500))
                        # Set Tesseract command path (adjust if necessary)
                        cropped_img = cropped_img.convert('L')  # 'L' converts to grayscale

                        # Optional: Increase contrast
                        enhancer = ImageEnhance.Contrast(cropped_img)
                        cropped_img = enhancer.enhance(2)  # You can adjust this factor for contrast enhancement

                        # Invert colors if necessary (for white text on dark background)
                        cropped_img = ImageOps.invert(cropped_img)

                        # Apply a threshold to binarize the image
                        cropped_img = cropped_img.point(lambda x: 0 if x < 128 else 255, '1')

                        # Save the processed image
                        cropped_img.save("processed_crop.png")
                        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
                        
                        try:
                            text = pytesseract.image_to_string(cropped_img)
                            numbers = re.findall(r'\d+', text)
                            phone_num = ''.join(numbers)
                            
                            if not phone_num:
                                print("No phone number found.")
                                continue
                            
                            print(f"Extracted phone number: {phone_num}")
                        except Exception as e:
                            print(f"Error during OCR: {e}")
                            continue
                        with open("api.txt","r",encoding="utf-8") as fp:
                            self.api_list = fp.readlines()
                        if self.run_modeflag != "copy_num":
                            await self.create_session(phone_num,self.api_list[0])
                        time.sleep(2)
                        self.tap_screen(80,80,device)
                        time.sleep(1)
                

    async def create_session(self, phone_number,api_list):
        # Initialize TelegramClient
        api = api_list.replace("\n","")
        api_id = api.split("-")[0]
        api_hash = api.split("-")[1]
        if os.path.exists(f"acc/{phone_number}"):
            return
        client = TelegramClient(f"acc/{phone_number}", api_id, api_hash)
        self.api_list.remove(api_list)
        with open("api.txt","w") as fp:
            fp.write("".join(self.api_list))
            fp.close()

        # Connect to Telegram
        await client.connect()

        # Check if the client is already authorized
        if not await client.is_user_authorized():
            # If not authorized, send the code request
            try:
                await client.send_code_request(phone_number)
                time.sleep(2)
            except Exception as e:
                print(e)
                await client.disconnect()
                if os.path.exists(f"acc{phone_number}"):
                    os.remove(f"acc/{phone_number}"+".session")
                time.sleep(2)
                return

            device = "127.0.0.1:5555"
            os.system(f'adb -s {device} shell screencap /sdcard/screen_2.png')
            
            # Pull screenshot to local machine
            os.system(f'adb -s {device} pull /sdcard/screen_2.png')
            print("Screenshot 'screen_2.png' captured and saved locally.")
            
            # Open the screenshot and crop the region
            img = Image.open('screen_2.png')
            cropped_img = img.crop((50, 50, 600, 300))
            if self.right_bottom==1920:
                cropped_img = img.crop((100, 100, 600, 300))  # Adjust the coordinates as needed
            elif self.right_bottom==1600 or self.right_bottom==1280:
                cropped_img=img.crop((50,50,600,250))
            elif self.right_bottom==960:
                cropped_img = img.crop((50,50,600,200))
            else:
                cropped_img = img.crop((50,50,600,300))
        
            cropped_img.save("crop.png")
            
            # Apply OCR to extract numbers
            try:
                text = pytesseract.image_to_string(cropped_img)
                numbers = re.findall(r'\d+', text)
                if numbers:
                    phone_num = numbers[-1]
                
                    if not phone_num:
                        print("No login code found.")
                        await client.disconnect()
                        if os.path.exists(f"acc/{phone_number}.session"):
                            os.remove(f"acc/{phone_number}.session")
                        time.sleep(2)
                        return
                
                print(f"Extracted login code: {phone_num}")
            except Exception as e:
                print(f"Error during OCR: {e}")
                await client.disconnect()
                if os.path.exists(f"acc/{phone_number}.session"):
                    os.remove(f"acc/{phone_number}.session")
                time.sleep(2)
                return
            code = int(phone_num)
            print(code)
            # Sign in the user with the provided code
            try:
                await client.sign_in(phone_number, code)
                if self.flag_mode:
                    with open(f"acc/{phone_number}.session", "rb") as session_file:
                        session_string = session_file.read().hex()  # Convert binary data to a hex string for JSON

                    session_data = {
                        "session": session_string,
                        "api_id": api_id,
                        "api_hash": api_hash,
                        "phone_number": phone_number
                    }

                    with open(f"acc/{phone_number}.json", "w") as json_file:
                        json.dump(session_data, json_file, indent=4)
                    print(f"Session data saved to '{phone_number}.json'.")
            except Exception as e:
                print(e)
                await client.disconnect()
                if os.path.exists(f"acc/{phone_number}.session"):
                    os.remove(f"acc/{phone_number}.session")
                time.sleep(2)
                return

        # Once logged in, the session is saved automatically in a session file
        string = []
        with open("saved_phone_number.txt","r") as fp:
            string = fp.readlines()
        save_string = f"{phone_number}\t{api_id}\t{api_hash}\n"
        string.append(save_string)
        with open("saved_phone_number.txt","w") as fp:
            fp.write("".join(string))
        print(f"Session created and saved as '{phone_number}.session'.")
        # You can use the client here to interact with the Telegram account
        await client.disconnect()
        time.sleep(3)

    def dump_window_hierarchy(self,device="127.0.0.1:5555"):
        """Dump the current UI hierarchy to a window_dump.xml file."""

        self.run_adb_command("shell uiautomator dump /sdcard/window_dump.xml", device)
        self.run_adb_command("pull /sdcard/window_dump.xml", device)

    def find_element_bounds(self,xml_file, resource_id=None):
        """Find the bounds of an element based on its resource_id."""

        tree = ET.parse(xml_file)
        root = tree.getroot()
        bounds_list = []
        for node in root.iter('node'):
            node_id = node.attrib.get('resource-id')
            bounds = node.attrib.get('bounds')

            # Find the element with the matching resource_id
            if resource_id and resource_id == node_id:
                print(f"Found element with resource_id: {node_id}, bounds: {bounds}")
                bounds_list.append(bounds)
        return bounds_list
    
    def find_position(self,bounds):
        left_top, right_bottom = self.parse_bounds(bounds)
        return left_top,right_bottom
    
    def get_bottom(self,bounds):
        left_top, right_bottom = self.parse_bounds(bounds)
        return left_top[1]

    def get_top(self,bounds):
        left_top, right_bottom = self.parse_bounds(bounds)
        return left_top[1]

    def get_bt_length(self,bound1,bound2):
        left_top1, right_bottom1 = self.parse_bounds(bound1)
        left_top2, right_bottom2 = self.parse_bounds(bound2)
        return left_top1[1]-left_top2[1]

    def get_first_bounds(self,xml_file):
        tree = ET.parse(xml_file)  # Replace 'your_file.xml' with your actual XML file path
        root = tree.getroot()

        # Find the first 'node' element and retrieve its 'bounds' attribute
        first_node = root.find('.//node')
        if first_node is not None:
            bounds = first_node.get('bounds')
            print(f"First bounds: {bounds}")
            left_top, right_bottom = self.parse_bounds(bounds)
            return right_bottom[1]
        else:
            print("No node found.")
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
        temp = 900-self.size
        print(f"shell input swipe 100 900 100 {temp} 500")
        self.run_adb_command(f"shell input swipe 100 900 100 {temp} 500", device)

    def first_scroll_down(self,bottom,top,device="127.0.0.1:5555"):
        self.run_adb_command(f"shell input swipe 100 {bottom} 100 {top} 500", device)

    def setting_scroll_down(self,flag,device="127.0.0.1:5555"):
        """Simulate scrolling down on the screen."""
        # Coordinates for scrolling: swipe from the bottom to the top of the screen
        print("Setting Scrolling down...")
        if flag:
            self.run_adb_command(f"shell input swipe 100 {self.right_bottom-5} 100 {self.right_bottom-self.between_len*3-5} 500", device)
        else:
            self.run_adb_command(f"shell input swipe 100 {self.right_bottom-self.between_len*3-5} 100 {self.right_bottom-5} 500", device)

    def tap_on_element(self,bounds, device="127.0.0.1:5555"):
        """Tap on the center of an element's bounds."""

        left_top, right_bottom = self.parse_bounds(bounds)
        x_center = (left_top[0] + right_bottom[0]) // 2
        y_center = (left_top[1] + right_bottom[1]) // 2
        self.size = right_bottom[1]-left_top[1]
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
