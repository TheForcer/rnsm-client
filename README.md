# rnsm-client
Updated Client part of my rnsm programming project for Incident Response & Malware Defense.

The server can be found here: https://github.com/TheForcer/rnsm-server

# Setup
Make sure that you are using Python >3.7 and have pip available to install the requirements:
This is a Windows-only script, I cannot guarantee for any of this to work on Linux.

1. Clone the source code with `git clone https://github.com/TheForcer/rnsm-client`

2. Checkout the correct branch with `git checkout incidentresponse`

3. Install the Python requirements using pip with `pip3 install -r requirements.txt`

4. Create a local folder called "toencrypt". All files in the folder will be encrypted/exfiltrated. You can change the target directories in the scripts via the target_paths variable. If no path is available, nothing will be encrypted/sent away.

5. Make sure an instance of the rnsm-Server is running and reachable. If required, edit the c2_url variable in the script.

6. Run the scripts with `python3 rnsm.py` / `python3 rnsm_ransomware.py` / `python3 rnsm_exfiltration.py`

# Obfuscating & Packing
A simple script is provided, which obfuscates & packs the scripts as a user-friendly single .exe-binary for easy sharing. This is achieved by the `pyarmor pack` command, which obfuscates the source code and then builds everything by calling `pyinstaller` afterwards. Execute the obfuscate+pack.ps1 PowerShell script while in the `pack` directory, and after a few seconds the three .exes should have appeared.

- The main Blocky.exe will be shared with the victim.
- Depending on the action sent by the C2-Server, the Malware will download the ransom/exfil stage via HTTP from the C2-Server directly. So exfil.exe and ransom.exe need to be put on the server, as is explained in the server's README
