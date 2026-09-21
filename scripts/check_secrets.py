"""Check staged content and reachable Git history for this checkout's actual secrets.
Prints only counts / safe filenames, never credentials. Does not replace a general secret scanner.
"""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
secrets=[]
env=ROOT/'.env'
if env.exists():
    for line in env.read_text(encoding='utf-8-sig').splitlines():
        name,sep,value=line.partition('=')
        if sep and any(word in name.upper() for word in ['API_KEY','SECRET','TOKEN','PASSWORD']):
            value=value.strip().strip('"').strip("'")
            if len(value)>=12:secrets.append(value.encode())
staged=git('ls-files','-z').decode().split('\0');bad=[];count=0
for name in filter(None,staged):
    if name=='.env' or (Path(name).name.startswith('.env.') and Path(name).name!='.env.example') or any(part in {'.venv','node_modules','data','tmp'} for part in Path(name).parts):bad.append(name)
    raw=git('show',':'+name);count+=1
    if any(s in raw for s in secrets):bad.append(name)
for row in git('rev-list','--objects','--all').decode().splitlines():
    ident=row.split(' ',1)[0]
    if git('cat-file','-t',ident).strip()==b'blob':
        raw=git('cat-file','blob',ident)
        if any(s in raw for s in secrets):bad.append('historical Git blob '+ident)
if bad:
    print('Excluded/private content found in Git: '+', '.join(sorted(set(bad))));sys.exit(1)
print(f'Checked {count} staged files and reachable history: no configured secret values or forbidden local paths found.')
