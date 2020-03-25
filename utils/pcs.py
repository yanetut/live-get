import os
import sys
import re
import subprocess

sys.path.append('..')
from utils.common import log_print

def upload(src, dst):
    if not os.path.exists(src):
        log_print('{src} not exist.'.format(src = src))
        return False
    cmd = 'baidupcs upload {src} {dst}'.format(
        src = src,
        dst = dst,
    )
    return subprocess.run(cmd, shell=True)


if __name__ == '__main__':
    ret = upload('zard__17-54_18-54.xml', '/apps/bypy/test').returncode
    print('ret: %d %s' % (ret, ret == 0))
