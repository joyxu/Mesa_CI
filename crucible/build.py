#!/usr/bin/python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..", "repos", "mesa_ci"))
import build_support as bs

bs.build(bs.CrucibleBuilder())


