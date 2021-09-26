

import shlex
import subprocess

from log import log


def run_cmd(cmd: str, cwd=None, sudo=False, block=True, shell=False,
            stdout=subprocess.PIPE) -> (int, subprocess.Popen):
    if sudo:
        cmd += 'sudo '
    if not shell:
        cmd = shlex.split(cmd)

    p = subprocess.Popen(cmd, cwd=cwd, shell=shell,
                         encoding='utf-8', bufsize=1,
                         stdout=stdout,
                         stderr=subprocess.STDOUT,
                         stdin=subprocess.PIPE)
    ret = 0
    if block:
        ret, out = p.communicate()
        if ret:
            log.error(f'rum cmd failed: cmd={cmd}, out={out}')
    return ret, p
