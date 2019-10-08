import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from testers import SkqpTester
from build_support import build
from options import Options


if __name__ == "__main__":
    env = {}
    if 'iris' in Options().hardware:
        env['MESA_LOADER_DRIVER_OVERRIDE'] = 'iris'

    Options().update_env(env)
    build(SkqpTester(env=env))
