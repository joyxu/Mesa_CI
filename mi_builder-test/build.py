import os
import os.path as path
import subprocess
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from build_support import build
from export import Export
from gtest import GTest
from options import Options
from project_map import ProjectMap
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "repos", "mesa_ci_internal"))
try:
    import internal_build_support.vars as internal_vars
except ModuleNotFoundError:
    internal_vars = None


class MiBuilderTest():
    def __init__(self):
        self._o = Options()
        self._pm = ProjectMap()
        self._build_root = self._pm.build_root()
        self._hw = self._o.hardware

    def build(self):
        pass

    def test(self):
        # The hw platform in the binary name doesn't always match the hardware
        # label used in CI, so this is a decoder dict
        mi_hw = {
            'ivb': 'gen7',
            'hsw': 'hsw',
            'bdw': 'gen8',
            'gen9': 'gen9',
            'icl': 'gen11',
            'tgl': 'gen12',
        }
        if internal_vars:
            mi_hw.update(internal_vars.mi_hw)

        if self._hw not in mi_hw:
            print('This platform does not have a supporting mi_builder binary')
            return 0
        mi_bin = 'intel_' + mi_hw[self._hw] + '_mi_builder_test'
        if not os.path.exists(os.path.join(self._build_root, 'bin', mi_bin)):
            print('No mi_builder was built/installed for this platform.')
            return 0
        gtest = GTest(self._build_root + '/bin', [mi_bin])
        gtest.run_tests()
        Export().export_tests()

    def clean(self):
        pass


if __name__ == "__main__":
    build(MiBuilderTest())
