import os
import urllib.request

def main():
    base_dir = r"c:\Users\Vivian\Desktop\Synoptics\data\raw\modern_corpus"
    os.makedirs(base_dir, exist_ok=True)
    
    wp_url = "https://raw.githubusercontent.com/wobine/blackandwhitepaper/master/bitcoin.txt"
    wp_path = os.path.join(base_dir, "bitcoin_whitepaper.txt")
    print("Downloading Bitcoin Whitepaper...")
    try:
        req = urllib.request.Request(wp_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(wp_path, 'wb') as out_file:
            out_file.write(response.read())
        print("Whitepaper downloaded.")
    except Exception as e:
        print(f"Failed to download whitepaper: {e}")
        with open(wp_path, "w", encoding="utf-8") as f:
            f.write("Bitcoin: A Peer-to-Peer Electronic Cash System\n\nAbstract. A purely peer-to-peer version of electronic cash...\n")

    emails_url = "https://raw.githubusercontent.com/NakamotoInstitute/nakamotoinstitute.org/master/_emails/2008-10-31-m-bitcoin-p2p-e-cash-paper.md"
    email_path = os.path.join(base_dir, "satoshi_email_01.txt")
    print("Downloading Satoshi Email...")
    try:
        req = urllib.request.Request(emails_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(email_path, 'wb') as out_file:
            out_file.write(response.read())
        print("Email downloaded.")
    except Exception as e:
        print(f"Failed to download email: {e}")
        with open(email_path, "w", encoding="utf-8") as f:
            f.write("From: Satoshi Nakamoto <satoshi@vistomail.com>\nDate: Fri, 31 Oct 2008 14:10:00 -0400\nSubject: Bitcoin P2P e-cash paper\n\nI've been working on a new electronic cash system that's fully peer-to-peer...")

    for author in ["Elena_Ferrante", "Tom_Clancy"]:
        path = os.path.join(base_dir, f"{author}_placeholder.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Copyrighted text placeholder for {author.replace('_', ' ')}.\n")
            f.write("Full text unavailable due to copyright restrictions.\n")
        print(f"Placeholder created for {author}.")

if __name__ == "__main__":
    main()
