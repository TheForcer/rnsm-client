# rnsm-client

Client part of my rnsm programming project.

The server can be found here: https://github.com/TheForcer/rnsm-server

# Setup
Make sure you are using Python 3.8 and have pip available to install the requirements:

This is a Windows only script, I cannot guarantee that it will work on Linux.

1. Clone the source with `git clone https://github.com/TheForcer/rnsm-client`.

2. Install the Python requirements using pip with `pip3 install -r requirements.txt`.

3. Create a local folder called "toencrypt". All files in this folder will be encrypted. You can change the target directories in the script using the target_paths variable. If there is no path, nothing will be encrypted.

4. Ensure that an instance of the rnsm server is running and accessible. If necessary, edit the c2_url variable in the script.

5. Run the script with `python3 rnsm.py'.

# Obfuscation & packing
A simple script is provided that obfuscates and packs the script as a user-friendly single .exe binary for easy distribution. This is done using the `pyarmor pack` command, which obfuscates the source code and then builds everything by calling `pyinstaller`. Run the obfuscate+pack.ps1 PowerShell script in the pack directory and after a few seconds you should have a Blocky.exe.
