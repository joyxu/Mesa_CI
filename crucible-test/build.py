#!/usr/bin/python

import sys
import os.path as path
sys.path.append(path.join(path.dirname(path.abspath(sys.argv[0])), "..",
                          "repos", "mesa_ci"))
import build_support as bs


if __name__ == "__main__":
    bs.build(bs.CrucibleTester())
