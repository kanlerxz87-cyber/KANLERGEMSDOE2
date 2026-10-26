"""Run tests with machine-readable GitHub annotations, preserving failure exit status."""
import subprocess
import sys

result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
print(result.stdout)
if result.returncode:
    message=result.stdout.replace('%','%25').replace('\r','%0D').replace('\n','%0A')
    print('::error title=Test failure details::'+message)
raise SystemExit(result.returncode)
