import os
import tarfile
import urllib.request
import sys
from pathlib import Path

# URLs and paths
ENRON_URL = "https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz"
DOWNLOAD_PATH = "enron_mail_20150507.tar.gz"
TARGET_DIR = Path("data/raw/enron")

# Specific targets to extract
TARGET_MAILBOXES = [
    "maildir/skilling-j", 
    "maildir/lay-k", 
    "maildir/watkins-s"
]

def download_progress(count, block_size, total_size):
    percent = int(count * block_size * 100 / total_size)
    sys.stdout.write(f"\rDownloading Enron corpus... {percent}%")
    sys.stdout.flush()

def main():
    print("--- Enron Test Dataset Downloader ---")
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    
    # We already have test.tar.gz from the previous test, so let's rename it to skip redownload!
    if os.path.exists('test.tar.gz'):
        os.rename('test.tar.gz', DOWNLOAD_PATH)

    if not os.path.exists(DOWNLOAD_PATH):
        print(f"Downloading CMU Enron dataset from {ENRON_URL}")
        print("This is ~423MB and may take a few minutes...")
        urllib.request.urlretrieve(ENRON_URL, DOWNLOAD_PATH, reporthook=download_progress)
        print("\nDownload complete.")
    else:
        print("Enron tarball already exists. Skipping download.")

    print("Extracting target mailboxes (Skilling, Lay, Watkins)...")
    
    with tarfile.open(DOWNLOAD_PATH, "r:gz") as tar:
        members_to_extract = []
        for member in tar.getmembers():
            # Check if the file is within our target mailboxes
            for mailbox in TARGET_MAILBOXES:
                # The tar file paths look like: maildir/skilling-j/...
                if member.name.startswith(mailbox):
                    members_to_extract.append(member)
                    break
        
        print(f"Found {len(members_to_extract)} relevant files. Extracting to {TARGET_DIR}...")
        
        # Extract and adjust paths
        for member in members_to_extract:
            # e.g. maildir/skilling-j/inbox/1.
            # We want: data/raw/enron/skilling-j/inbox/1.
            parts = member.name.split('/')
            if len(parts) >= 2:
                # parts[0] = maildir
                # parts[1:] = skilling-j/inbox/...
                relative_path = '/'.join(parts[1:])
                target_path = TARGET_DIR / relative_path
                
                if member.isdir():
                    target_path.mkdir(parents=True, exist_ok=True)
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with tar.extractfile(member) as source, open(target_path, "wb") as dest:
                        if source:
                            dest.write(source.read())
                        
    print("Extraction complete.")
    print("Cleaning up tarball to save space...")
    os.remove(DOWNLOAD_PATH)
    
    print("\n--- Done! ---")
    print(f"Data saved to {TARGET_DIR.absolute()}")

if __name__ == "__main__":
    main()
