#!/usr/bin/env python3
"""
Smart India Hackathon (SIH) Host Link & Public Tunnel Generator
Exposes the local frontend (port 5173) and routes backend APIs (port 8000)
seamlessly via a secure public HTTPS url using localtunnel or ngrok.
"""
import socket
import sys
import os
import subprocess
import time
import threading

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Resolve network IP address without sending actual packets
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def print_banner():
    banner = """
======================================================================
     Smart India Hackathon (SIH) - Host Link Generator & Tunneling
======================================================================
  Platform: AI-Powered Dynamic Multi-Vehicle Logistics Optimization DSS
======================================================================
"""
    print(banner)

def show_local_links(ip):
    print("  [Local & Network Host Links]")
    print(f"  * Frontend UI (Local):    http://localhost:5173")
    print(f"  * Frontend UI (Network):  http://{ip}:5173  <-- Open this on local devices")
    print(f"  * Backend API (Local):    http://localhost:8000")
    print(f"  * Backend API (Network):  http://{ip}:8000")
    print(f"  * Swagger API Docs:       http://localhost:8000/docs")
    print(f"  * Health Check Probe:     http://localhost:8000/health")
    print("======================================================================")

def run_localtunnel():
    print("\n[+] Initializing Localtunnel (port 5173)...")
    print("[i] Command: npx localtunnel --port 5173")
    print("[i] Requesting secure endpoint. Please wait...\n")
    
    try:
        proc = subprocess.Popen(
            ["npx", "localtunnel", "--port", "5173"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True
        )
    except Exception as e:
        print(f"[-] Failed to execute 'npx localtunnel': {e}")
        print("[!] Ensure Node.js and npm are installed on the host system.")
        return

    url_found = False
    
    def read_stdout(p):
        nonlocal url_found
        for line in p.stdout:
            line_str = line.strip()
            if "your url is:" in line_str.lower():
                url = line_str.split("is:")[-1].strip()
                url_found = True
                print("=======================================================================")
                print("  🎉 SECURE PUBLIC HTTPS TUNNEL CREATED SUCCESSFULLY!")
                print("=======================================================================")
                print(f"  * Public URL: {url}")
                print("  * Access:     Any device connected to the internet can now access")
                print("                your SIH Logistics Platform.")
                print("  * Proxying:   Requests to /api and /ws are auto-routed to")
                print("                your local FastAPI backend (port 8000).")
                print("=======================================================================")
                print("\nPress Ctrl+C to terminate the tunnel and exit.")
            else:
                if not url_found:
                    # Print setup messages (e.g. npx downloading package messages)
                    print(f"  [localtunnel] {line_str}")

    t = threading.Thread(target=read_stdout, args=(proc,))
    t.daemon = True
    t.start()

    try:
        while proc.poll() is None:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[-] Shutting down localtunnel process...")
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()
        print("[+] Tunnel closed successfully.")

def run_ngrok():
    print("\n[+] Starting Ngrok on port 5173...")
    print("[i] Command: npx ngrok http 5173")
    print("[i] If you haven't set your auth token, run:")
    print("    npx ngrok config add-authtoken <your-auth-token>\n")
    print("=======================================================================")
    print("Launching Ngrok interactive interface... Press Ctrl+C to exit.")
    print("=======================================================================")
    time.sleep(1.5)
    
    try:
        subprocess.run(["npx", "ngrok", "http", "5173"], shell=True)
    except KeyboardInterrupt:
        print("\n[-] Ngrok stopped.")
    except Exception as e:
        print(f"[-] Failed to execute 'npx ngrok': {e}")
        print("[!] Ensure Node.js, npm are installed, and ngrok is authenticated.")

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    ip = get_local_ip()
    print_banner()
    show_local_links(ip)
    
    print("\nSelect public tunnel provider option:")
    print("  [1] Localtunnel (Zero configuration, no signup - RECOMMENDED)")
    print("  [2] Ngrok (Highly stable, requires free account authtoken)")
    print("  [3] Exit Link Generator")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        if choice == '1':
            run_localtunnel()
        elif choice == '2':
            run_ngrok()
        elif choice == '3':
            print("\nExiting. Good luck with the SIH presentation!")
        else:
            print("\n[-] Invalid choice. Exiting.")
    except KeyboardInterrupt:
        print("\n\nExiting. Good luck with the SIH presentation!")

if __name__ == "__main__":
    main()
