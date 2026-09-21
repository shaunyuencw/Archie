"""Read-only environment report; never prints secrets or downloads models."""
import json, platform, shutil, subprocess, sys
from pathlib import Path

def command(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=15).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"

def doctor():
    visio = False
    if sys.platform == 'win32':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, 'Visio.Application'): visio = True
        except OSError: pass
    return {"os":platform.platform(), "architecture":platform.machine(), "cpu":command(['sysctl','-n','machdep.cpu.brand_string']) if sys.platform=='darwin' else platform.processor(), "python":sys.version.split()[0], "node":command(['node','--version']), "ram_bytes":command(['powershell','-NoProfile','-Command','(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory']) if sys.platform=='win32' else command(['sysctl','-n','hw.memsize']), "gpu":command(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader']), "ollama_version":command(['ollama','--version']), "ollama_models":command(['ollama','list']), "ollama_ps":command(['ollama','ps']), "visio_registered":visio, "live_capabilities":"unverified", "cloud_default":False}

if __name__=='__main__':
    report=doctor(); Path('reports').mkdir(exist_ok=True)
    Path('reports/environment.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
