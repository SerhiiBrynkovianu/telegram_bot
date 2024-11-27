import asyncio
import ctypes
import datetime
import os
import time
import tkinter.messagebox as tkmb
import winreg
from typing import List

from pwinput import pwinput

import GV
from core import joinGroup, loginAllAccounts, startChatting
from gui import Myapp, update
from utils import getPinId

REG_PATH = r"SOFTWARE\WinTgCb\Settings"


def set_license(name, value):
    try:
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(registry_key, name, 0, winreg.REG_SZ, value)
        winreg.CloseKey(registry_key)
        return True
    except WindowsError:
        return False


def get_license(name):
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        value, regtype = winreg.QueryValueEx(registry_key, name)
        winreg.CloseKey(registry_key)
        return value
    except WindowsError:
        return 0


def GenerateLicense(input, output, len):
    t1 = 0
    t2 = 0
    t3 = 0
    t4 = 0
    vartemp = 0
    data1 = (ctypes.c_ubyte * 512)()
    data2 = (ctypes.c_ubyte * 512)()

    licenseGen = bytearray(b"passy")
    input = bytearray(input, "utf-8")
    Length = 5

    t1 = 0
    t2 = 0
    while t1 <= 255:
        data1[t1] = t1
        data2[t1] = licenseGen[t2]
        t2 += 1
        t2 = t2 % Length
        t1 += 1

    t1 = 0
    t2 = 0
    while t1 <= 255:
        t2 = t2 + data1[t1] + data2[t1]
        t2 = t2 % 256
        vartemp = data1[t1]
        data1[t1] = data1[t2]
        data1[t2] = vartemp
        t1 += 1

    t1 = 0
    t2 = 0
    t4 = 0
    while t4 < len:
        t1 = t1 + 1
        t1 = t1 % 256
        t2 = t2 + data1[t1]
        t2 = t2 % 256

        vartemp = data1[t1]
        data1[t1] = data1[t2]
        data1[t2] = vartemp

        t3 = data1[t1] + (data1[t2] % 256)
        t3 = t3 % 256
        output[t4] = input[t4] ^ data1[t3]
        t4 += 1


def GetCodeFromName(Name):
    idx = 0
    code = ""
    temp = ""
    output = (ctypes.c_ubyte * 512)()

    Length = len(Name)
    GenerateLicense(Name, output, Length)

    code = ""
    idx = 0
    while idx < Length:
        temp = f"{output[idx]:02X}"
        code += temp
        idx += 1
    return code


UserName = get_license("UserName")
licenseCode = get_license("LicenseCode")
validity = get_license("Validity")
InstallDate = get_license("InstallDate")
LicenseType = get_license("LicenseType")
LicenseCount = get_license("LicenseCount")
MinutesUsed = 0
DaysUsed = 0
LicenseCount = int(LicenseCount) + 1


if InstallDate != False:
    date_format = "%Y-%m-%d %H:%M:%S"
    From = datetime.datetime.strptime(str(InstallDate), date_format)
    To = datetime.datetime.strptime(str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), date_format)
    MinutesUsed = (To - From).total_seconds() / 60
    DaysUsed = (MinutesUsed / 60) / 24
    if int(LicenseType) == 1:
        if int(MinutesUsed) >= int(validity):
            print("License expired. Please activate new license")
            licenseCode = 0
    elif int(LicenseType) == 2:
        if int(DaysUsed) >= int(validity):
            print("License expired. Please activate new license")
            licenseCode = 0


if (
    (UserName == 0)
    or ((int(LicenseType) == 1) and (int(MinutesUsed) >= int(validity)))
    or ((int(LicenseType) == 2) and (int(DaysUsed) >= int(validity)))
):
    if LicenseCount > 1 and len(UserName) > 0:  # type:ignore
        print("User Name: " + UserName)  # type:ignore
    else:
        UserName = input("Enter UserName: ")


if (
    (int(LicenseType) < 1)
    or (int(LicenseType) > 2)
    or ((int(LicenseType) == 1) and (int(MinutesUsed) >= int(validity)))
    or ((int(LicenseType) == 2) and (int(DaysUsed) >= int(validity)))
    or (licenseCode == 0)
):
    print("License Options:")
    print("1: Based on Minutes")
    print("2: Based on Days")
    LicenseType = input("Enter license option:")
    if (int(LicenseType) < 1) or (int(LicenseType) > 2):
        print("Please run again and Enter valid License Option")
        exit()
    else:
        set_license("LicenseType", LicenseType)

if (
    (int(validity) <= 0)
    or (int(LicenseType) > 2)
    or ((int(LicenseType) == 1) and (int(MinutesUsed) >= int(validity)))
    or ((int(LicenseType) == 2) and (int(DaysUsed) >= int(validity)))
    or (licenseCode == 0)
):
    if int(LicenseType) == 1:
        validity = input("Enter the Minutes for this software license to be applicable: ")
    elif int(LicenseType) == 2:
        validity = input("Enter the Days for this software license to be applicable: ")
    if int(validity) <= 0:
        print("You have entered 0. Please run again and Enter valid number for license")
        exit()
    else:
        set_license("Validity", validity)


if (
    ((int(LicenseType) == 1) and (int(MinutesUsed) >= int(validity)))
    or ((int(LicenseType) == 2) and (int(DaysUsed) >= int(validity)))
    or (licenseCode == 0)
):
    licenseCode = pwinput(prompt="Enter your " + str(LicenseCount) + " time license code: ", mask="*")
    tmpusername = str((int(LicenseCount) * 55 - 23)) + UserName + str((int(LicenseCount) * 55 - 23))  # type:ignore
    if licenseCode != GetCodeFromName(tmpusername):
        print("Invalid license code")
        exit()
    else:
        set_license("UserName", UserName)
        set_license("LicenseCode", licenseCode)
        set_license("InstallDate", str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        # set_license("LicenseType", "0")
        # set_license("Validity", "0")
        set_license("LicenseCount", str(LicenseCount))

    if int(LicenseType) == 1:
        print(
            "License successfully activated for "  # type:ignore
            + validity
            + " minutes!!! at "
            + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
    elif int(LicenseType) == 2:
        print(
            "License successfully activated for "  # type:ignore
            + validity
            + " days!!! at"
            + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )


FILENAMES = ["group.txt", "messages.txt", "bot_to_bot_reply.txt", "human_to_bot_reply.txt", "phones.txt", "admin_reply.txt","emoji reaction.txt","pin.txt","pin_message.txt"]
PATHS = ["sessions","admin_sessions","images"]

if LicenseType == "1":
    license_string = (
        str(int((int(validity) - MinutesUsed))) + "m" + str(int(round((int(validity) - MinutesUsed) % 1, 2) * 60)) + "s"
    )
else:
    left_days = int(validity) - DaysUsed
    left_hours = left_days % 1 * 24
    left_minutes = left_hours % 1 * 60
    left_seconds = left_minutes % 1 * 60

    license_string = (
        str(int(left_days))
        + "d"
        + str(int(left_hours))
        + "h"
        + str(int(left_minutes))
        + "m"
        + str(int(left_seconds))
        + "s"
    )


async def check_license_validity():
    while True:
        if InstallDate != False:
            date_format = "%Y-%m-%d %H:%M:%S"
            From = datetime.datetime.strptime(str(InstallDate), date_format)
            To = datetime.datetime.strptime(str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), date_format)
            MinutesUsed = (To - From).total_seconds() / 60
            DaysUsed = (MinutesUsed / 60) / 24
            if int(LicenseType) == 1:
                if int(MinutesUsed) >= int(validity):
                    tkmb.showerror("License expired", "License expired. Please activate new license")
                    exit()
            elif int(LicenseType) == 2:
                if int(DaysUsed) >= int(validity):
                    tkmb.showerror("License expired", "License expired. Please activate new license")
                    exit()

        await asyncio.sleep(5)


def initial_start(filenames: List[str], paths: List[str]):
    for path_ in paths:
        if not os.path.exists(path_):
            os.mkdir(path_)
    for file_name in filenames:
        if not os.path.exists(file_name):
            with open(file_name, "a",encoding="utf-8") as fh:
                fh.close()

    if not os.path.exists("emoji_list.txt"):
        with open("emoji_list.txt", "a",encoding="utf-8") as fh:
            fh.writelines("https://carpedm20.github.io/emoji/")
            fh.close()


initial_start(filenames=FILENAMES, paths=PATHS)


async def main():
    GV.init()

    GV.app = Myapp()
    GV.root = GV.app.getRoot()
    GV.PinId = getPinId()
    GV.app.update_title("| License Left: " + license_string)
    await asyncio.gather(update(GV.root), loginAllAccounts(), joinGroup(), startChatting(), check_license_validity())


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
