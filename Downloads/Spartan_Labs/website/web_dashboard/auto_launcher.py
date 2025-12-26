import time
import subprocess
import socket
import os

# Configuration
SC_PROCESS_NAME = "SierraChart"
DASHBOARD_PORT = 5050
LAUNCH_SCRIPT = r"C:\Users\Quantum\Desktop\CV-Sierra\web_dashboard\LAUNCH_WEB_DASHBOARD.bat"

def is_sierra_running():
    try:
        # Check running processes
        output = subprocess.check_output('tasklist /fo csv /nh', shell=True).decode('utf-8', errors='ignore')
        return SC_PROCESS_NAME.lower() in output.lower()
    except:
        return False

def is_dashboard_running():
    try:
        # Check if dashboard port is open
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', DASHBOARD_PORT)) == 0
    except:
        return False

def main():
    print("monitoring_active")
    while True:
        try:
            if is_sierra_running():
                if not is_dashboard_running():
                    # Sierra is open, but Dashboard is closed -> Launch it!
                    bat_dir = os.path.dirname(LAUNCH_SCRIPT)
                    subprocess.Popen(f'"{LAUNCH_SCRIPT}"', cwd=bat_dir, shell=True)
                    # Wait for startup
                    time.sleep(15)
            time.sleep(5)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    main()
