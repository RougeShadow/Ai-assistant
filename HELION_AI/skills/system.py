import subprocess

def handle(cmd):
    cmd = cmd.lower()

    if "open" in cmd:
        app = cmd.split("open")[-1].strip()
        subprocess.Popen(app, shell=True)
        return f"Opened {app}"

    if "close" in cmd:
        app = cmd.split("close")[-1].strip()
        subprocess.Popen(f"taskkill /im {app}.exe /f", shell=True)
        return f"Closed {app}"

    return "System command not recognized"
