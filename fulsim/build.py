#!/usr/bin/env python3

import sys
import os
import os.path as path
sys.path.append(path.join(path.dirname(path.abspath(sys.argv[0])), "..",
                          "repos", "mesa_ci", "build_support"))
from build_support import build
from builders import FulsimBuilder
from options import Options
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci_internal"))
try:
    import internal_build_support.vars as internal_vars
except ModuleNotFoundError:
    internal_vars = None

# Note: Override version with FULSIM_<HARDWARE>_VERSION env. variable
fulsim_stable_versions = {
    'tgl_sim': '103446',
}
if internal_vars:
    fulsim_stable_versions.update(internal_vars.fulsim_stable_versions)


def main():
    if Options().arch != "m64":
        print("Unsupported arch (%s), not installing fulsim!"
              % Options().arch)
        sys.exit(1)
    hardware = Options().hardware.replace('_iris', '')
    if hardware not in fulsim_stable_versions:
        print("There is no fulsim for this platform!")
        sys.exit(0)
    # matching is done on base hardware name, so strip off '_iris'
    fulsim_ver = None
    # When run with build_local, the override var is in os.environ under the
    # var's name. When run in CI, the override var is in the 'env' variable in
    # os.environ. This handles both cases.
    env = os.environ.get('env')
    if env:
        for var in env.split():
            if 'FULSIM_' + hardware.split('_sim')[0].upper() + '_VERSION' in var:
                fulsim_ver = var.split('=')[1]
                break
    else:
        fulsim_ver = os.environ.get('FULSIM_'
                                    + hardware.split('_sim')[0].upper()
                                    + '_VERSION')
    if not fulsim_ver:
        fulsim_ver = fulsim_stable_versions[hardware]
    b = FulsimBuilder(buildnum=fulsim_ver)
    build(b)


if __name__ == '__main__':
    main()
