import os
import os.path as path
import subprocess
import sys
sys.path.append(path.join(path.dirname(path.abspath(sys.argv[0])), "..",
                          "repos", "mesa_ci"))
import build_support as bs


class MiBuilderTest():
    def __init__(self):
        self._o = bs.Options()
        self._pm = bs.ProjectMap()
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
        }

        if self._hw not in mi_hw:
            print('This platform does not have a supporting mi_builder binary')
            return 0
        mi_bin = 'intel_' + mi_hw[self._hw] + '_mi_builder_test'
        if not os.path.exists(os.path.join(self._build_root, 'bin', mi_bin)):
            print('No mi_builder was built/installed for this platform.')
            return 0
        gtest = bs.GTest(self._build_root + '/bin', [mi_bin])
        gtest.run_tests()
        bs.Export().export_tests()

    def clean(self):
        pass


if __name__ == "__main__":
    bs.build(MiBuilderTest())
