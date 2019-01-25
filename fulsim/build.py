#!/usr/bin/python
import sys
import os
import os.path as path
sys.path.append(path.join(path.dirname(path.abspath(sys.argv[0])), "..",
                          "repos", "mesa_ci"))
import build_support as bs

# Note: Override version with FULSIM_VERSION env. variable
fulsim_stable_versions = {
    'tgl': '102650',
    'ats': '25674',
}


def main():
    if bs.Options().arch != "m64":
        print("Unsupported arch (%s), not installing fulsim!"
              % bs.Options().arch)
        sys.exit(1)
    hardware = bs.Options().hardware
    fulsim_ver = os.environ.get('FULSIM_VERSION')
    if not fulsim_ver:
        fulsim_ver = fulsim_stable_versions[hardware]
    b = bs.FulsimBuilder(buildnum=fulsim_ver)
    bs.build(b)


if __name__ == '__main__':
    main()
