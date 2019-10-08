#!/usr/bin/python

import os
import subprocess
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from build_support import build
from options import Options
from project_map import ProjectMap
from utils.command import run_batch_command
from utils.utils import cpu_count
from export import Export


class SconsBuilder(object):
    def __init__(self):
        self.src_dir = ProjectMap().source_root() + "/repos/mesa"

    def clean(self):
        pass
    
    def test(self):
        pass

    def build(self):
        save_dir = os.getcwd()
        os.chdir(self.src_dir)

        # scons build is broken, will occasionally fail if temporaries
        # are still around.  Use git's nuclear clean method instead of
        # the clean targets.
        run_batch_command(["git", "clean", "-dfx"])

        env = {}
        Options().update_env(env)
        run_batch_command(["scons", "-j",
                              str(cpu_count())], env=env)

        run_batch_command(["git", "clean", "-dfx"])
        os.chdir(save_dir)
        
def main():
    b = SconsBuilder()
    save_dir = os.getcwd()
    try:
        build(b)
    except subprocess.CalledProcessError as e:
        # build may have taken us to a place where ProjectMap doesn't work
        os.chdir(save_dir)  
        Export().create_failing_test("mesa-scons-buildtest", str(e))

if __name__ == '__main__':
    main()
