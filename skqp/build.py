#!/usr/bin/python
import git
import importlib
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..", "repos", "mesa_ci"))
import build_support as bs

if __name__ == "__main__":
    bs.build(bs.SkqpBuilder())
