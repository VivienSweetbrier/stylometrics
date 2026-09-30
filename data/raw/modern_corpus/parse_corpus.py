import os
import re
import email
from email import policy
from pathlib import Path

def parse_email_document(file_path):
    """Parses standard email format (Cypherpunk mailing lists) into headers and body."""
    with open(file_path, 'r', encoding='utf-8') as f:
        msg = email.message_from_file(f, policy=policy.default)
    
    metadata = {
        'type': 'email',
        'from': msg.get('From', ''),
        'to': msg.get('To', ''),
        'date': msg.get('Date', ''),
        'subject': msg.get('Subject', '')
    }
    
    # Extract body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                body += part.get_payload(decode=True).decode('utf-8', errors='replace')
    else:
        body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
        
    # Check for PGP signature
    if "-----BEGIN PGP SIGNATURE-----" in body:
        metadata['has_pgp_signature'] = True
    else:
        metadata['has_pgp_signature'] = False

    return {'metadata': metadata, 'content': body}

def parse_whitepaper_document(file_path):
    """Parses whitepapers (e.g., Bitcoin Whitepaper) into discrete sections."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    metadata = {
        'type': 'whitepaper'
    }
    
    # Simple heuristic to split sections like "1. Introduction" or "12. Conclusion"
    # Matches a newline, followed by a number, a dot, a space, and text until newline.
    section_pattern = re.compile(r'(?:\n|^)(\d+\.\s+[A-Z][^\n]+)(?:\n|$)')
    
    segments = {}
    last_idx = 0
    current_section = "Title/Abstract"
    
    for match in section_pattern.finditer(content):
        # Everything before the match belongs to the previous section
        start, end = match.span(1)
        section_content = content[last_idx:match.start()].strip()
        if section_content:
            segments[current_section] = section_content
        
        current_section = match.group(1).strip()
        last_idx = match.end()
        
    # Add the last section
    last_content = content[last_idx:].strip()
    if last_content:
        segments[current_section] = last_content
        
    return {'metadata': metadata, 'segments': segments}

def main():
    base_dir = Path(r"c:\Users\Vivian\Desktop\Synoptics\data\raw\modern_corpus")
    
    print("Parsing Modern Corpus Data...\n")
    
    email_path = base_dir / "satoshi_email_01.txt"
    if email_path.exists():
        email_data = parse_email_document(email_path)
        print("--- Email Parse Result ---")
        print("Metadata:", email_data['metadata'])
        print("Content length:", len(email_data['content']))
        print("-" * 30 + "\n")
        
    wp_path = base_dir / "bitcoin_whitepaper.txt"
    if wp_path.exists():
        wp_data = parse_whitepaper_document(wp_path)
        print("--- Whitepaper Parse Result ---")
        print("Metadata:", wp_data['metadata'])
        print("Sections found:", list(wp_data['segments'].keys()))
        print("-" * 30 + "\n")

if __name__ == "__main__":
    main()
