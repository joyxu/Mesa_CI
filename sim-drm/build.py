#!/usr/bin/python
import sys
import os.path as path
sys.path.append(path.join(path.dirname(path.abspath(sys.argv[0])), "..",
                          "repos", "mesa_ci"))
import build_support as bs


def main():
    if bs.Options().arch != "m64":
        print("Unsupported arch (%s), not building sim-drm!"
              % bs.Options().arch)
        sys.exit(1)
    b = bs.builders.MesonBuilder(install=True)
    bs.build(b)


if __name__ == '__main__':
    main()
