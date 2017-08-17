#!/usr/bin/python3
# -*- coding: utf-8 -*-

import subprocess


def download(remote, local):
    # pcs download -f apps/bypy/test/test.flv test.flv
    cmd = 'pcs download -f {remote_path} {local_path}'.format(
        remote_path = remote,
        local_path = local,
    )
    return subprocess.run(cmd, shell = True)
