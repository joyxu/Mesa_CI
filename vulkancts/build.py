#!/usr/bin/python

import sys, os
import git
import importlib

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..", "repos", "mesa_ci"))
import build_support as bs

def get_external_revisions(revisions_dict=None):
    return bs.deqp_external_revisions(project="vulkancts",
                                      revisions_dict=revisions_dict)

class VulkanCtsBuilder(object):
    def __init__(self):
        self._pm = bs.ProjectMap()
        self._options = bs.Options()
        self._src_dir = self._pm.project_source_dir()
        self._build_dir = self._src_dir + "/build_" + self._options.arch
        self._build_root = self._pm.build_root()

    def build(self):
        save_dir = os.getcwd()
        os.chdir(self._src_dir)
        try:
            bs.run_batch_command(["patch", "-p1", "CMakeLists.txt",
                                  self._pm.project_build_dir("vulkancts") + "/0001-Fix-PNG.patch"])
        except:
            print "WARN: failed to apply PNG patch"
        try:
            bs.run_batch_command(["patch", "-p1", "external/vulkancts/modules/vulkan/vktTestPackage.cpp",
                                  self._pm.project_build_dir("vulkancts") + "/0002-Attempt-to-load-prebuilt-spirv-from-cache.patch"])
        except:
            print "WARN: failed to apply prebuilt patch"
        os.chdir(save_dir)
        revisions = get_external_revisions()
        external_dir = (self._pm.project_source_dir('vulkancts')
                        + "/external/{}/src")
        bs.checkout_externals(project='vulkancts', revisions=revisions,
                              external_dir_format=external_dir)

        btype = "Release"
        # Vulkan cts is twice as slow for RelDeb builds, which impacts
        # the CI throughput.  For this reason, we unconditionally
        # optimize the build.
        # if self._options.config == "debug":
        #    btype = "RelDeb"
        flags = "-m64"
        if self._options.arch == "m32":
            flags = "-m32"
        cmd = ["cmake", "-GNinja", "-DCMAKE_BUILD_TYPE=" + btype,
               "-DCMAKE_C_COMPILER_LAUNCHER=ccache",
               "-DCMAKE_CXX_COMPILER_LAUNCHER=ccache",
               "-DCMAKE_C_FLAGS=" + flags, "-DCMAKE_CXX_FLAGS=" + flags,
               "-DCMAKE_C_COMPILER=clang", "-DCMAKE_CXX_COMPILER=clang++",
               "-DCMAKE_INSTALL_PREFIX:PATH=" + self._build_root, ".."]
        if not os.path.exists(self._build_dir):
            os.makedirs(self._build_dir)
        os.chdir(self._build_dir)
        bs.run_batch_command(cmd)
        bs.run_batch_command(["ninja", "vk-build-programs"])
        save_dir = os.getcwd()
        os.chdir("external/vulkancts/modules/vulkan")
        out_dir = os.path.join(self._src_dir, "external", "vulkancts", "data", "vulkan", "prebuilt")
        print "Pre-building spir-v binaries: vk-build-programs -d " + out_dir
        bs.run_batch_command(["./vk-build-programs", "-d", out_dir],
                             quiet=True,
                             streamedOutput=False)
        os.chdir(save_dir)
        bs.run_batch_command(["ninja"])
        bin_dir = self._build_root + "/opt/deqp/"
        if not os.path.exists(bin_dir):
            os.makedirs(bin_dir)

        bs.run_batch_command(["rsync", "-rlptD",
                              self._build_dir + "/external/vulkancts/modules",
                              bin_dir])

        bs.Export().export()

    def clean(self):
        bs.git_clean(self._src_dir)

    def test(self):
        pass


if __name__ == "__main__":
    bs.build(VulkanCtsBuilder())
