# rnsm-client
Client part of my rnsm programming project.

The server can be found here: https://github.com/TheForcer/rnsm-server

# Setup
Make sure that you are using Python 3.8 and have pip available to install the requirements:
This is a Windows-only script, I cannot guarantee for any of this to work on Linux.

1. Clone the source code with `git clone https://github.com/TheForcer/rnsm-client`

2. Install the Python requirements using pip with `pip3 install -r requirements.txt`

3. Create a local folder called "toencrypt". All files in the folder will be encrypted. You can change the target directories in the script via the target_paths variable. If no path is available, nothing will be encrypted.

4. Make sure an instance of the rnsm-Server is running and reachable. If required, edit the c2_url variable in the script.

5. Run the script with `python3 rnsm.py`

# Obfuscating & Packing
A simple script is provided, which obfuscates & packs the script as a user-friendly single .exe-binary for easy sharing. This is achieved by the `pyarmor pack` command, which obfuscates the source code and then builds everything by calling `pyinstaller` afterwards. Execute the obfuscate+pack.ps1 PowerShell script while in the pack directory, and after a few seconds a Blocky.exe should have appeared.
