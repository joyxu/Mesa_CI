#!/usr/bin/python
import sys
import os
import os.path as path
sys.path.append(path.join(path.dirname(path.abspath(sys.argv[0])), "..",
                          "repos", "mesa_ci"))
import build_support as bs

# Note: Override version with FULSIM_<HARDWARE>_VERSION env. variable
fulsim_stable_versions = {
    'tgl_sim': '103429',
}


def main():
    if bs.Options().arch != "m64":
        print("Unsupported arch (%s), not installing fulsim!"
              % bs.Options().arch)
        sys.exit(1)
    # matching is done on base hardware name, so strip off '_iris'
    hardware = bs.Options().hardware.replace('_iris', '')
    fulsim_ver = None
    # When run with build_local, the override var is in os.environ under the
    # var's name. When run in CI, the override var is in the 'env' variable in
    # os.environ. This handles both cases.
    env = os.environ.get('env')
    if env:
        for var in env.split():
            if 'FULSIM_' + hardware.upper() + '_VERSION' in var:
                fulsim_ver = var.split('=')[1]
                break
    else:
        fulsim_ver = os.environ.get('FULSIM_' + hardware.upper() + '_VERSION')
    if not fulsim_ver:
        fulsim_ver = fulsim_stable_versions[hardware]
    b = bs.FulsimBuilder(buildnum=fulsim_ver)
    bs.build(b)


if __name__ == '__main__':
    main()
