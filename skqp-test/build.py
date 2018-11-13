import sys
import os
import os.path as path
sys.path.append(path.join(path.dirname(path.abspath(sys.argv[0])), "..",
                          "repos", "mesa_ci"))
import build_support as bs
if __name__ == "__main__":
    env = {}
    bs.Options().update_env(env)
    bs.build(bs.SkqpTester(env=env))
