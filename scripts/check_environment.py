import json
import os
import platform
import shutil
from pathlib import Path
root = Path(__file__).resolve().parent.parent
candidate = Path.home()/'qnx800'
installed_qcc = candidate/'host/win64/x86_64/usr/bin/qcc.exe'
report = {'host_platform':platform.system(),'python':platform.python_version(),
          'qcc_on_path':shutil.which('qcc'),'QNX_HOST_present':bool(os.getenv('QNX_HOST')),
          'QNX_TARGET_present':bool(os.getenv('QNX_TARGET')),
          'default_install_qcc':str(installed_qcc) if installed_qcc.is_file() else None,
          'default_install_env_script':str(candidate/'qnxsdp-env.bat') if (candidate/'qnxsdp-env.bat').is_file() else None,
          'qnx_roundtrip_verified':False,'authorization_verified':False,
          'gate':'PENDING_NATIVE_VALIDATION',
          'note':'Not on PATH does not mean not installed. See toolchain-check.md for compilation evidence.'}
(root/'review/environment-check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
