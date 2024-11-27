import asyncio
import os
import sys
import tkinter as tk

import pygubu
from pygubu import builder  # noqa # type:ignore
# from pygubu.builder import tkstdwidgets, ttkstdwidgets  # noqa # type:ignore

import GV
from CONST import LOG_TAG


# Define function to import external files when using PyInstaller.
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS  # type:ignore
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


GUI_FILE_NAME = resource_path("main.ui")


class Myapp:
    def __init__(self):
        self.builder = builder = pygubu.Builder()  # noqa
        builder.add_from_file(GUI_FILE_NAME)

        # gets GUI elements
        self.root = builder.get_object("window")
        self.root.protocol("WM_DELETE_WINDOW", self._onClosing)

        # scroll logs
        self.scLogs = builder.get_object("scLogs")
        self.scLogs["state"] = tk.DISABLED
        self.scLogs.tag_config(GV.LOG_TAG["CONTROL"], foreground="green")
        self.scLogs.tag_config(GV.LOG_TAG["SYSTEM"], foreground="blue")
        self.scLogs.tag_config(GV.LOG_TAG["SYSTEM"], foreground="red")

        # window
        self.main_window = builder.get_object("window")

        # # input field (2fa & code)
        self.inputCode = builder.get_object("inputCode")
        self.varInputCode = builder.get_variable("varInputCode")
        self.inputCode.bind("<Return>", self.onUserInputEnded)

        self.lblInputCode = builder.get_object("lblInputCode")
        self.frmInputCode = builder.get_object("frmInputCode")
        self.setVisibleInputCode(False)

        # # input field for delay
        self.varInputDelay = builder.get_variable("varInputDelay")
        self.varInputDelay.set(GV.Delay)
        self.varInputDelay.trace("w", lambda name, index, mode, sv=self.varInputDelay: self.onInputDelayChanged(sv))
        self.inpDelay = builder.get_object("inpDelay")

        # check box for showing typing status
        self.varShowTyping = builder.get_variable("varShowTyping")
        self.varShowTyping.set(str(GV.ShowTyping))
        self.varShowTyping.trace("w", lambda name, index, mode, sv=self.varShowTyping: self.onShowTypingChanged(sv))

        self.var_enable_human_reply = builder.get_variable("varEnableHumanReply")
        self.var_enable_human_reply.set(str(GV.enable_human_reply))
        self.var_enable_human_reply.trace(
            "w", lambda name, index, mode, sv=self.var_enable_human_reply: self.on_enable_human_reply_changed(sv)
        )
        self.varRadioSelection = tk.StringVar(value="session")  # Default selection is "session"

        # Create radio buttons for "Phone" and "Session"
        self.radio_phone = tk.Radiobutton(self.root, text="Phone", variable=self.varRadioSelection, value="phone", command=self.onRadioSelectionChanged)
        self.radio_session = tk.Radiobutton(self.root, text="Session", variable=self.varRadioSelection, value="session", command=self.onRadioSelectionChanged)

        self.radio_phone.pack(side=tk.TOP, padx=10, pady=5)
        self.radio_session.pack(side=tk.TOP, padx=10, pady=5)
        # buttons
        self.btnStart = builder.get_object("btnStart")
        self.btnPause = builder.get_object("btnPause")
        self.btnPause["state"] = tk.DISABLED

        self.addLog("Press start to start the program", GV.LOG_TAG["CONTROL"])
        builder.connect_callbacks(self)

    def onRadioSelectionChanged(self):
        """Callback function when a radio button is selected"""
        selected_option = self.varRadioSelection.get()
        if selected_option == "phone":
            GV.flag = True
            self.addLog("Phone selected. Flag set to True.", GV.LOG_TAG["CONTROL"])
        else:
            GV.flag = False
            self.addLog("Session selected. Flag set to False.", GV.LOG_TAG["CONTROL"])

    def _onClosing(self):
        GV.ProgramStatus = GV.PROGRAM_STATUS["STOP"]

    def getRoot(self):
        return self.root

    def update_title(self, str_to_add: str):
        self.main_window.title(self.main_window.title() + " " + str_to_add)

    # adds a log messages to the scrolled text
    # system logs is colored
    def addLog(self, logs, tag=GV.LOG_TAG["NORMAL"]):
        GV.info("addLog: " + logs)
        self.scLogs["state"] = tk.NORMAL

        self.scLogs.insert(tk.END, logs + "\n", tag)
        self.scLogs.see(tk.END)
        self.scLogs["state"] = tk.DISABLED

    def setVisibleInputCode(self, visible):
        if visible:
            self.frmInputCode.pack()
        else:
            self.frmInputCode.pack_forget()

    def getDelay(self):
        return self.varInputDelay.get()

    # prompts user input
    async def getInput2fa(self):
        GV.IsGettingInput = True

        self.addLog("Please enter 2fa below", GV.LOG_TAG["CONTROl"])
        self.setVisibleInputCode(True)
        self.varInputCode.delete(0, tk.END)

        while GV.IsGettingInput:
            if GV.ProgramStatus == GV.PROGRAM_STATUS["STOP"]:
                break
            await asyncio.sleep(GV.UPDATE_RATE)

        self.setVisibleInputCode(False)

        return self.varInputCode.get()

    async def getInputCode(self):
        GV.IsGettingInput = True

        self.addLog("Please enter code below", GV.LOG_TAG["CONTROL"])
        self.setVisibleInputCode(True)
        self.inputCode.delete(0, tk.END)

        while GV.IsGettingInput:
            if GV.ProgramStatus == GV.PROGRAM_STATUS["STOP"]:
                break
            await asyncio.sleep(GV.UPDATE_RATE)

        self.setVisibleInputCode(False)

        return self.varInputCode.get()

    # ======================
    # UI callbacks functions
    # ======================

    # gets called when btn start is clicked
    def onBtnStartTouched(self):
        GV.ProgramStatus = GV.PROGRAM_STATUS["RUNNING"]
        self.addLog("The program is running", LOG_TAG["SYSTEM"])
        self.btnPause["state"] = tk.NORMAL
        self.btnStart["state"] = tk.DISABLED

    # gets called when btn pause is clicked
    def onBtnPauseTouched(self):
        GV.ProgramStatus = GV.PROGRAM_STATUS["IDLE"]
        self.addLog("The program is paused", LOG_TAG["SYSTEM"])
        self.btnStart["state"] = tk.NORMAL
        self.btnPause["state"] = tk.DISABLED

    # gets called when user ended input code
    def onUserInputEnded(self, args):
        GV.debug("onUserInputEnded: '" + self.varInputCode.get() + "'")
        GV.IsGettingInput = False

    # gets called when user change the delay
    def onInputDelayChanged(self, var):
        try:
            GV.debug("onvarInputDelayChanged: '" + str(var.get()) + "'")
            self.addLog("Changed delay to " + str(var.get()), GV.LOG_TAG["SYSTEM"])
            GV.Delay = var.get()
        except Exception as e:
            GV.error("onInputDelayChanged: " + str(e) + " - " + str(type(e)))
            var.set(GV.Delay)

    # gets called when user change the show typing status
    def onShowTypingChanged(self, var):
        try:
            GV.debug("onShowTypingChanged: '" + str(var.get()) + "'")
            GV.ShowTyping = int(var.get())
        except Exception as e:
            GV.error("onInputDelayChanged: " + str(e) + " - " + str(type(e)))

    # gets called when user change the show typing status
    def on_enable_human_reply_changed(self, var):
        try:
            GV.debug("on_enable_human_reply_changed: '" + str(var.get()) + "'")
            GV.enable_human_reply = int(var.get())
        except Exception as e:
            GV.error("on_enable_human_reply_changed: " + str(e) + " - " + str(type(e)))


async def update(window):
    while True:
        window.update_idletasks()
        window.update()

        if GV.ProgramStatus == GV.PROGRAM_STATUS["STOP"]:
            break

        if GV.ProgramStatus == GV.PROGRAM_STATUS["IDLE"]:
            await asyncio.sleep(GV.UPDATE_RATE)
            continue

        # ===========================
        # core control code goes here
        # ===========================
        await asyncio.sleep(GV.UPDATE_RATE)
