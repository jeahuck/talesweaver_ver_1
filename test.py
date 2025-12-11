import subprocess
import time

ps_script = r"C:\Users\82106\IdeaProjects\clickTest\ocr_server.ps1"

# PowerShell 서버 실행
subprocess.Popen(
    ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", ps_script],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

time.sleep(1)  # 서버 준비 시간