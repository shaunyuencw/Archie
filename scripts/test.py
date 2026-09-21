"""Offline checkpoint gate. No API credentials, paid calls or automatic model downloads."""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
env={**os.environ,'APP_PROVIDER':'mock','APP_ALLOW_CLOUD':'false','OPENAI_API_KEY':'','APP_LIVE_TESTS':'false'}
steps=[('backend',[sys.executable,'-m','pytest','-q','--junitxml=reports/m7-tests.xml'],ROOT),
       ('typescript',['node','node_modules/typescript/bin/tsc','-b'],ROOT/'apps/web'),
       ('frontend-unit',['node','node_modules/vitest/vitest.mjs','run'],ROOT/'apps/web'),
       ('browser',['node','node_modules/@playwright/test/cli.js','test'],ROOT/'apps/web'),
       ('production-build',['node','node_modules/vite/bin/vite.js','build'],ROOT/'apps/web')]
results=[]
for name,args,cwd in steps:
    started=time.monotonic();result=subprocess.run(args,cwd=cwd,env=env)
    results.append({'check':name,'exit_code':result.returncode,'seconds':round(time.monotonic()-started,3)})
    (ROOT/'reports/offline-gate.json').write_text(json.dumps({'offline':True,'platform':sys.platform,'checks':results},indent=2),encoding='utf-8')
    if result.returncode:sys.exit(result.returncode)
