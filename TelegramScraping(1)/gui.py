import os
import asyncio
import threading
import atexit
import tkinter as tk
from tkinter import Tk, Text, Scrollbar, END, messagebox, Frame, Listbox, SINGLE, VERTICAL, W, Checkbutton, IntVar, Canvas, BOTH
from tkinter import ttk
from phone_init_worker import PhoneInitWorker
from session_init_worker import SessionInitWorker
from add_members_worker import AddMembersWorker
from join_group_worker import JoinGroupWorker
from show_members_worker import ShowMembersWorker
import concurrent.futures
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsAdmins, ChannelParticipantsSearch
from proxy_utils import parse_proxy
from tkinter import simpledialog
import logging
from tkcalendar import DateEntry

logging.basicConfig(level=logging.INFO, filename='telegram_add_members.log', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')

PHONES_FILENAME = "phones.txt"
HASH_FILENAME = "hash.txt"
PROXY_FILENAME = "proxies.txt"
SESSION_FOLDER = "sessions"
NONE_CODE_FOLDER = "no-sign"
BANNED_FOLDER = "banned_sessions"
GROUPS_FILENAME = "groups.txt"
FINISHED_FOLDER = "finished_sessions"
USERS_FILENAME = "users.txt"
SCRAPE_USERS = "scrape_users.txt"

class TelegramAdder:
    def __init__(self, root):
        self.clients = []
        self.API_KEYS = []
        self.sessions = []
        self.proxies = []
        self.groups = []
        self.client_phone=[]
        self.selected = ""
        self.run_mode = ""
        self.stop_requested = False
        self.root = root
        self.root.title("Telegram Member Adder")
        self.root.configure(bg="#F5F5F5")
        self.selected_clients=[]
        self.selected_clients2=[]
        # Apply the clam theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.create_styles()
        
        self.ensure_directories()
        self.ensure_files()
        self.gui_setup()
        self.load_api_credentials()
        self.load_proxies()
        self.load_sessions()
        # self.concurrent_sessions_slider.config(to=int(len(self.sessions)))
        
        atexit.register(self.cleanup)
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_styles(self):
        # Define custom styles
        self.style.configure("Accent.TButton", background="#4CAF50", foreground="white", font=("Helvetica", 10, "bold"))
        self.style.map("Accent.TButton",
                       background=[("active", "#45A049"), ("disabled", "#A5A5A5")],
                       foreground=[("disabled", "#D3D3D3")])

        self.style.configure("Warning.TButton", background="#FF9800", foreground="white", font=("Helvetica", 10, "bold"))
        self.style.map("Warning.TButton",
                       background=[("active", "#FB8C00"), ("disabled", "#FFC107")],
                       foreground=[("disabled", "#D3D3D3")])

        self.style.configure("Danger.TButton", background="#F44336", foreground="white", font=("Helvetica", 10, "bold"))
        self.style.map("Danger.TButton",
                       background=[("active", "#E53935"), ("disabled", "#FFCDD2")],
                       foreground=[("disabled", "#D3D3D3")])

        self.style.configure("Action.TButton", background="#2196F3", foreground="white", font=("Helvetica", 10, "bold"))
        self.style.map("Action.TButton",
                       background=[("active", "#1E88E5"), ("disabled", "#BBDEFB")],
                       foreground=[("disabled", "#D3D3D3")])
        
        self.style.configure('Custom.TRadiobutton',
                background='#f0f0f0',foreground='#000000',font=('Helvetica', 10,"bold"),
                indicatorcolor='#1e90ff',indicatordiameter=10,padding=5)
        self.style.map("Custom.TRadiobutton",
                       background=[("active", "#1E88E5"), ("disabled", "#BBDEFB")],
                       foreground=[("disabled", "#D3D3D3")])  

    def cleanup(self):
        asyncio.run(self._cleanup_async())
        self.executor.shutdown(wait=True)
        self.update_status("All clients disconnected and cleaned up.")

    async def _cleanup_async(self):
        tasks = [client.disconnect() for client in self.clients if client.is_connected()]
        await asyncio.gather(*tasks, return_exceptions=True)

    def ensure_directories(self):
        os.makedirs(SESSION_FOLDER, exist_ok=True)
        os.makedirs(BANNED_FOLDER, exist_ok=True)
        os.makedirs(NONE_CODE_FOLDER, exist_ok=True)
        os.makedirs(FINISHED_FOLDER, exist_ok=True)

    def ensure_files(self):
        for filename in [PHONES_FILENAME, HASH_FILENAME, PROXY_FILENAME,GROUPS_FILENAME,SCRAPE_USERS]:
            if not os.path.exists(filename):
                with open(filename, 'w') as f:
                    f.write("")

    def load_api_credentials(self):
        try:
            with open(HASH_FILENAME, "r") as api_file:
                self.API_KEYS = api_file.read().split("\n")
                self.update_status("API credentials loaded successfully.")
        except Exception as e:
            self.update_status(f"Error loading API credentials: {e}")

    def load_sessions(self):
        try:
            self.sessions = [
                os.path.join(SESSION_FOLDER, f) 
                for f in os.listdir(SESSION_FOLDER) 
                if os.path.isfile(os.path.join(SESSION_FOLDER, f)) and f.endswith(".session") and not f.endswith("-journal.session")
            ]
        except Exception as e:
            self.update_status(f"Error loading sessions: {e}")

    def load_none_code_sessions(self):
        try:
            sessions = [os.path.join(NONE_CODE_FOLDER, f) for f in os.listdir(NONE_CODE_FOLDER) if os.path.isfile(os.path.join(NONE_CODE_FOLDER, f))]
            self.update_status(f"Found {len(sessions)} no-sign session files.")
            return sessions
        except Exception as e:
            self.update_status(f"Error loading no-sign sessions: {e}")

    def validate_proxy(self, proxy):
        try:
            parse_proxy(proxy)
            return True
        except ValueError as e:
            self.update_status(f"Proxy validation error: {e}")
            return False
        
    def load_proxies(self):
        try:
            with open(PROXY_FILENAME, "r") as proxyFile:
                proxy_addr = proxyFile.read().split("\n")
                if proxy_addr[-1] == '':  # Ensure the list is not empty
                    proxy_addr.pop()
                self.proxies = [parse_proxy(proxy) for proxy in proxy_addr if self.validate_proxy(proxy)]
                self.update_status(f"Loaded {len(self.proxies)} proxies.")
        except Exception as e:
            self.update_status(f"Error loading proxies: {e}")

    def get_phone_numbers(self):
        try:
            with open(PHONES_FILENAME, "r") as phoneFile:
                phonesList = phoneFile.read().split("\n")
                formatted_phones = [phone.strip() for phone in phonesList if phone.strip()]
                self.update_status(f"Loaded {len(formatted_phones)} phone numbers.")
                return formatted_phones
        except Exception as e:
            self.show_toast(f"Error loading phone numbers: {e}")
            return []

    def start_phone_init(self):
        self.stop_requested = False
        self.phones_list = self.get_phone_numbers()
        self.progress_bar["maximum"] = len(self.phones_list)
        self.progress_bar["value"] = 0
        self.worker = PhoneInitWorker(self.API_KEYS, self.phones_list, self.update_status, self.thread_finished, self.proxies, self.is_stop_requested, self.update_progress_bar, self.clients, self.root)
        self.thread = threading.Thread(target=self.worker.run)
        self.thread.start()
        self.change_button_to_stop(self.phone_init_button)

    def start_session_init(self):
        self.stop_requested = False
        self.load_sessions()  # Reload sessions each time we initialize
        self.progress_bar["maximum"] = len(self.sessions)
        self.progress_bar["value"] = 0
        self.clients.clear()
        # con_count = self.concurrent_sessions_slider.get()  # Get the value from the slider
        self.worker = SessionInitWorker(self.API_KEYS, self.sessions, self.update_status, self.thread_finished, 
                                        self.proxies, self.is_stop_requested, self.update_progress_bar, self.clients)
        self.thread = threading.Thread(target=self.worker.run)
        self.thread.start()
        self.change_button_to_stop(self.session_init_button)

    def change_button_to_stop(self, button):
        self.current_button = button
        self.original_text = button.cget("text")
        self.original_command = button.cget("command")
        button.config(text="Running", command=self.stop_init, style="Danger.TButton", width=20)

    def revert_button(self, button, text, command):
        button.config(text=text, command=command, style="Accent.TButton", width=20)

    def stop_init(self):
        self.stop_requested = True

    def is_stop_requested(self):
        return self.stop_requested

    def show_toast(self, message, duration=3000):
        self.root.after(0, self._show_toast, message, duration)

    def _show_toast(self, message, duration):
        # Display the message using messagebox.showinfo (modal dialog, user closes it manually)
        messagebox.showinfo("Info", message)
        # Optionally log the message somewhere, for example, in the status text
        self.update_status(message)

    def update_status(self, message):
        logging.info(message)
        self.root.after(0, self._update_status, message)

    def _update_status(self, message):
        if self.status_text.winfo_exists():
            self.status_text.config(state="normal")
            self.status_text.insert(END, str(message) + "\n")
            self.status_text.config(state="disabled")
            self.status_text.yview(END)  # Scroll to the bottom

    def update_progress_bar(self, value):
        self.root.after(0, self._update_progress_bar, value)

    def _update_progress_bar(self, value):
        self.progress_bar["value"] = value

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def thread_finished(self):
        self.root.after(0, self._thread_finished)

    def _thread_finished(self):
        self.update_status("Operation completed.")
        self.populate_clients_listbox()  # Update clients listbox
          
        self.revert_button(self.current_button, self.original_text, self.original_command)
        # print(int(len(self.clients)))

    def close_all_connects(self):
        asyncio.run(self._close_all_connects_async())

    async def _close_all_connects_async(self):
        try:
            self.update_status("Closing all connections...")
            tasks = [client.disconnect() for client in self.clients if client.is_connected()]
            await asyncio.gather(*tasks, return_exceptions=True)
            self.clients.clear()  # Remove all clients from the list
            self.update_status("All clients disconnected successfully.")
            self.populate_clients_listbox()
        except Exception as e:
            self.update_status(f"Error closing connections: {e}")
            self.show_error_message(f"Error closing connections: {e}")

    def gui_setup(self):
        # Main frame
        main_frame = Frame(self.root, padx=10, pady=10, bg="#F5F5F5")
        main_frame.pack(fill=BOTH, expand=True)

        # Buttons frame
        buttons_frame = Frame(main_frame, bg="#F5F5F5")
        buttons_frame.pack(side="top", fill="x", pady=5)

        self.phone_init_button = ttk.Button(buttons_frame, text="Making with phone", command=self.start_phone_init, style="Accent.TButton")
        self.phone_init_button.grid(row=0, column=1, padx=5, pady=5)

        # Session Init Button
        self.session_init_button = ttk.Button(buttons_frame, text="Connect with Sessions", command=self.start_session_init, style="Accent.TButton")
        self.session_init_button.grid(row=0, column=2, padx=5, pady=5)

        selected_option1 = tk.StringVar(value="multi")
        selected_option2 = tk.StringVar(value="add_mode")
        # Function to handle radiobutton selection
        def on_select():
            self.selected = selected_option1.get()
            self.run_mode = selected_option2.get()
        # Create Radiobuttons with white text and a black background
        self.multi_option = ttk.Radiobutton(buttons_frame, text="multi_option", variable=selected_option1, value="multi", command=on_select,style="Custom.TRadiobutton")
        self.multi_option.grid(row=0,column=3,padx=5,pady=5)
        self.multi_option.invoke()
        self.single_option = ttk.Radiobutton(buttons_frame, text="single_option", variable=selected_option1, value="single",command=on_select,style="Custom.TRadiobutton")
        self.single_option.grid(row=0, column=4, padx=5, pady=5)

        self.add_mode = ttk.Radiobutton(buttons_frame, text="add", variable=selected_option2, value="add_mode",command=on_select,style="Custom.TRadiobutton")
        self.add_mode.grid(row = 1,column=2,padx=4,pady=4)
        self.add_mode.invoke()
        self.scrape_mode = ttk.Radiobutton(buttons_frame, text="scrape", variable=selected_option2, value="scrape_mode",command=on_select,style="Custom.TRadiobutton")
        self.scrape_mode.grid(row = 1,column=3,padx=4,pady=4)
        
        self.date_label = ttk.Label(buttons_frame,text="start date:", background="#F5F5F5")
        self.date_label.grid(row=1,column=4,padx=4,pady=4)
        self.start_date = DateEntry(buttons_frame,selectmode="day")
        self.start_date.grid(row=1,column=5,padx=4,pady=4)
        # Progress Bar
        self.progress_bar = ttk.Progressbar(main_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", padx=5, pady=10)

        # Inputs frame
        inputs_frame = Frame(main_frame, bg="#F5F5F5")
        inputs_frame.pack(side="top", fill="x", pady=10)

        # Delay
        self.delay_label = ttk.Label(inputs_frame, text="Delay (seconds):", anchor="w", background="#F5F5F5")
        self.delay_label.grid(row=0, column=0, padx=5, pady=5, sticky=W)
        
        self.delay_entry = ttk.Entry(inputs_frame, width=10)
        self.delay_entry.insert(0, "10")  # Set default value
        self.delay_entry.grid(row=0, column=1, padx=5, pady=5, sticky=W)
        
        # Count
        self.add_count_lb = ttk.Label(inputs_frame, text="Count:", anchor="w", background="#F5F5F5")
        self.add_count_lb.grid(row=0, column=2, padx=5, pady=5, sticky=W)
        
        self.add_count = ttk.Entry(inputs_frame, width=10)
        self.add_count.insert(0, "5")  # Set default value
        self.add_count.grid(row=0, column=3, padx=5, pady=5, sticky=W)

        # Join Group Button
        self.join_group_button = ttk.Button(inputs_frame, text="Join Group", command=self.join_group_button_clicked, style="Action.TButton")
        self.join_group_button.grid(row=0, column=4, padx=4, pady=5)

        # Add Members Button
        self.start_add_members_button = ttk.Button(inputs_frame, text="run", command=self.add_members_button, style="Action.TButton")
        self.start_add_members_button.grid(row=0, column=6, padx=5, pady=5, sticky=W)

        # Show Members Button
        show_members_button = ttk.Button(inputs_frame, text="Show Members", command=self.show_members, style="Action.TButton")
        show_members_button.grid(row=0, column=5, padx=5, pady=5, sticky=W)

        # Listboxes frame
        listboxes_frame = Frame(main_frame, bg="#F5F5F5")
        listboxes_frame.pack(side="top", fill=BOTH, expand=True, padx=5, pady=5)

        # Groups Listbox
        groups_frame = Frame(listboxes_frame, bg="#F5F5F5")
        groups_frame.pack(side="left", fill=BOTH, expand=True, padx=1, pady=5)
        groups_label = ttk.Label(groups_frame, text="Groups", background="#F5F5F5")
        groups_label.pack(side="top", anchor="w")
                
        self.groups_listbox = Listbox(groups_frame, selectmode=SINGLE, bd=2, relief="groove")
        self.groups_listbox.pack(side="left", fill=BOTH, expand=True)
        groups_scrollbar = Scrollbar(groups_frame, orient=VERTICAL, command=self.groups_listbox.yview)
        groups_scrollbar.pack(side="right", fill="y")
        self.groups_listbox.config(yscrollcommand=groups_scrollbar.set)

        clients_frame = Frame(listboxes_frame, bg="#F5F5F5", width=180)  # Adjust the width of the clients list
        clients_frame.pack(side="left", fill=BOTH, expand=False, padx=5, pady=5)

        clients_label = Frame(clients_frame, bg="#F5F5F5")
        clients_label.pack(side="top", anchor="w", fill="x")

        ttk.Label(clients_label, text="Clients", background="#F5F5F5").pack(side="left")
        self.select_all_var = IntVar()
        self.select_all_checkbutton = ttk.Checkbutton(clients_label, text="Select All", variable=self.select_all_var, command=self.toggle_select_all, style="TCheckbutton")
        self.select_all_checkbutton.pack(side="right", anchor="e")

        # Border container frame
        border_container = Frame(clients_frame, bd=2, relief="groove", bg="#F5F5F5")
        border_container.pack(side="left", fill=BOTH, expand=True)

        self.canvas = Canvas(border_container, bg="#F5F5F5")
        self.canvas.pack(side="left", fill=BOTH, expand=True)

        clients_scrollbar = Scrollbar(border_container, orient=VERTICAL, command=self.canvas.yview)
        clients_scrollbar.pack(side="right", fill="y")
        self.canvas.config(yscrollcommand=clients_scrollbar.set)

        self.clients_listbox_frame = Frame(self.canvas, bg="#F5F5F5")
        self.canvas.create_window((0, 0), window=self.clients_listbox_frame, anchor="nw")
        self.clients_listbox_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        # Members Listbox
        members_frame = Frame(listboxes_frame, bg="#F5F5F5")
        members_frame.pack(side="left", fill=BOTH, expand=True, padx=5, pady=5)
        self.members_count_label = ttk.Label(members_frame, text="Members Count: 0", anchor="w", background="#F5F5F5")
        self.members_count_label.pack(side="top", anchor="w")
        self.members_listbox = Listbox(members_frame, selectmode=SINGLE, bd=2, relief="groove")
        self.members_listbox.pack(side="left", fill=BOTH, expand=True)
        members_scrollbar = Scrollbar(members_frame, orient=VERTICAL, command=self.members_listbox.yview)
        members_scrollbar.pack(side="right", fill="y")
        self.members_listbox.config(yscrollcommand=members_scrollbar.set)


        # Status Text with Scrollbar
        status_frame = Frame(main_frame, bg="#F5F5F5")
        status_frame.pack(side="top", fill=BOTH, expand=True, pady=10)

        self.status_text = Text(status_frame, wrap="word", height=15, state="disabled", bd=2, relief="groove", bg="#FFFFFF", fg="#333333")
        self.status_text.pack(side="left", fill=BOTH, expand=True)

        scrollbar = Scrollbar(status_frame, command=self.status_text.yview)
        scrollbar.pack(side="right", fill="y")

        self.status_text.config(yscrollcommand=scrollbar.set)

        # Bind listbox select event
        self.groups_listbox.bind('<<ListboxSelect>>', self.on_group_select)
        self.populate_groups_listbox()
        self.populate_clients_listbox()

    def add_group(self):
        # Open a dialog to input the group URL
        group_url = simpledialog.askstring("Enter Group", f"Enter the new group url:")
        if group_url:
            self.groups.append(group_url)
            with open(GROUPS_FILENAME, "a") as file:
                file.write(group_url + "\n")
            self.populate_groups_listbox()
            self.update_status(f"Group URL added: {group_url}")                

    # def update_concurrent_sessions_label(self, value):
    #     self.concurrent_sessions_value.config(text=str(int(float(value))))

    def toggle_select_all(self):
        select_all = self.select_all_var.get()
        for var in self.client_vars:
            var.set(select_all)

    def join_group_button_clicked(self):
        try:
            selected_index = self.groups_listbox.curselection()
            if not selected_index:
                self.show_toast("Please select a group first.")
                return

            group_index = int(selected_index[0])
            self.selected_clients = [self.clients[i] for i, var in enumerate(self.client_vars) if var.get() == 1]
            if not self.selected_clients:
                self.show_toast("Please select at least one client.")
                return
            self.progress_bar["maximum"] = len(self.clients)
            self.progress_bar["value"] = 0
            group_url = self.groups[group_index]
            self.worker = JoinGroupWorker(group_url, self.selected_clients, self.update_status, self.is_stop_requested, self.update_progress_bar, self.proxies,  self.API_KEYS,True)
            self.thread = threading.Thread(target=self.worker.run)
            self.thread.start()
        except Exception as e:
            self.update_status(f"Error joining group: {e}")

    def add_members_button(self):
        print("Add Members button clicked")
        selected_index = self.groups_listbox.curselection()
        if not selected_index and self.run_mode=="add_mode":
            self.show_toast("Please select a group first.")
            return
        group_index=0
        if self.run_mode=="add_mode":
            group_index = int(selected_index[0])

        try:
            delay = float(self.delay_entry.get())
            print(delay)
        except ValueError:
            self.show_toast("Invalid delay value.")
            return

        self.start_add_members_worker(group_index, delay)

    def start_add_members_worker(self, group_index, delay):
        print("Starting AddMembersWorker")
        self.stop_requested = False
        try:
            with open("users.txt", "r") as file:
                usernames = file.read().splitlines()
                usernames = [username.strip() for username in usernames if username.strip()]
                self.progress_bar["maximum"] = len(usernames)
        except Exception as e:
            self.update_status(f"Error loading usernames: {e}")
        self.progress_bar["value"] = 0
        group_url=""
        if len(self.groups)!=0:
            group_url = self.groups[group_index]  # Get the rotation limit value
        add_count = self.add_count.get()
        date=self.start_date.get_date()
        self.selected_clients = [self.clients[i] for i, var in enumerate(self.client_vars) if var.get() == 1]
        self.selected_clients2 = [self.client_phone[i] for i, var in enumerate(self.client_vars) if var.get() == 1]
        # con_count = self.concurrent_sessions_slider.get()  # Get the value from the slider
        self.worker = AddMembersWorker(self.API_KEYS, group_url,self.root, self.update_status, self.thread_finished, 
                                        self.proxies, self.is_stop_requested, self.update_progress_bar, self.selected_clients,self.selected_clients2,
                                        delay, self.refresh_groups,add_count,mode=self.selected,start_date=date,run_mode =self.run_mode)
        self.thread = threading.Thread(target=self.worker.run)
        self.thread.start()
        self.change_button_to_stop(self.start_add_members_button)

    def refresh_groups(self):
        self.groups_listbox.delete(0, END)  # Clear the listbox
        try:
            with open(GROUPS_FILENAME, "r") as file:
                lines = file.read().splitlines()
                self.groups = [line.strip() for line in lines if line.strip()]

            self.update_status(f"Found {len(self.groups)} groups.")
            if not self.groups:
                self.update_status("No groups found.")
                return

            for i, group_name in enumerate(self.groups):
                self.groups_listbox.insert(END, f"{i}: {group_name}")

        except Exception as e:
            self.update_status(f"Error populating groups: {e}")

    def populate_clients_listbox(self):
        for widget in self.clients_listbox_frame.winfo_children():
            widget.destroy()
        self.client_vars = []  # Clear the checkbutton variables

        try:
            for i, client in enumerate(self.clients):
                var = IntVar()
                phone = os.path.splitext(os.path.basename(client.session.filename))[0]
                if '+' in phone:
                    phone = phone.replace('+', '')
                chk = Checkbutton(self.clients_listbox_frame, text=f"Client {i + 1}: ({phone})", variable=var, bg="#F5F5F5")
                chk.pack(anchor="w", padx=5, pady=5)
                self.client_vars.append(var)
                self.client_phone.append(phone)

            # self.update_status(f"Found {len(self.clients)} clients.")
        except Exception as e:
            self.update_status(f"Error populating clients: {e}")

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

    def show_members(self):
        selected_index = self.groups_listbox.curselection()
        if not selected_index:
            self.show_toast("Please select a group first.")
            return

        group_index = int(selected_index[0])
        group_url = self.groups[group_index]
        self.worker = ShowMembersWorker(self.API_KEYS, group_url, self.proxies, self.clients, 
                                        self.update_status, self.update_members_listbox, self.update_members_count)
        self.thread = threading.Thread(target=self.worker.run())
        self.thread.start()

    def update_members_listbox(self, members_list):
        self.root.after(0, self._update_members_listbox, members_list)

    def _update_members_listbox(self, members_list):
        self.members_listbox.delete(0, END)  # Clear the listbox
        for member in members_list:
            self.members_listbox.insert(END, member)

    def update_members_count(self, count):
        self.root.after(0, self._update_members_count, count)

    def _update_members_count(self, count):
        self.members_count_label.config(text=f"Members Count: {count}")

    def on_group_select(self, event):
        selected_index = self.groups_listbox.curselection()
        if selected_index:
            group_index = int(selected_index[0])
            # self.update_status(f"Group {group_index+1} selected.")

    def populate_groups_listbox(self):
        self.groups_listbox.delete(0, END)  # Clear the listbox
        try:
            with open(GROUPS_FILENAME, "r") as file:
                lines = file.read().splitlines()
                self.groups = [line.strip() for line in lines if line.strip()]

            self.update_status(f"Found {len(self.groups)} groups.")
            if not self.groups:
                self.update_status("No groups found.")
                return

            for i, group_name in enumerate(self.groups):
                self.groups_listbox.insert(END, f"Group_{i+1} : {group_name.split('/+')[-1]}")

        except Exception as e:
            self.update_status(f"Error populating groups: {e}")

    def show_error_message(self, message):
        self.show_toast(message)

    def show_info_message(self, message):
        messagebox.showinfo("Info", message)

    def on_closing(self):
        self.cleanup()
        self.root.destroy()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             

if __name__ == "__main__":
    root = Tk()
    app = TelegramAdder(root)
    root.mainloop()