#!/usr/bin/env python3

import multiprocessing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from build_support import build
from export import Export
from options import Options
from project_map import ProjectMap
from testers import DeqpTester, DeqpTrie, ConfigFilter
from utils.command import run_batch_command
from utils.fulsim import Fulsim
from utils.utils import get_conf_file, get_blacklists


class SlowTimeout:
    def __init__(self):
        self.timeout = 60
        self.hardware = Options().hardware

    def GetDuration(self):
        if self.hardware in ["gen9atom", "bsw"]:
            self.timeout = 90
        if "_sim" in self.hardware:
            self.timeout = 120
        return self.timeout


class VulkanTestList(object):
    def __init__(self):
        self.pm = ProjectMap()
        self.hardware = Options().hardware

    def tests(self, env):
        # provide a DeqpTrie with all tests
        deqp_dir = os.path.dirname(self.binary())
        os.chdir(deqp_dir)
        cmd = ["./" + os.path.basename(self.binary()),
               "--deqp-runmode=xml-caselist"]
        run_batch_command(cmd, env=env)
        trie = DeqpTrie()
        trie.add_xml("dEQP-VK-cases.xml")
        os.chdir(self.pm.project_build_dir())
        mustpass_file = None
        whitelist = DeqpTrie()
        if self.hardware.endswith('_sim'):
            if os.path.exists(self.pm.project_build_dir()
                              + '/sim_whitelist.conf'):
                mustpass_file = (self.pm.project_build_dir()
                                 + '/sim_whitelist.conf')
                print("Using mustpass for simulated platforms: "
                      + mustpass_file)
                whitelist.add_txt(mustpass_file)
        else:
            # Detect the latest mustpass file to use, and use it
            mustpass_dir = (self.pm.project_source_dir("vulkancts")
                            + "/external/vulkancts/mustpass/master/")
            mustpass_file = mustpass_dir + "/vk-default.txt"
            if not mustpass_file:
                print("Unable to find a valid whitelist/mustpass to use!")
                sys.exit(1)
            # mustpass file can be an index listing many mustpass files, or it
            # can be a single huge list of all tests.
            mustpass_file_is_index = True
            with open(mustpass_file) as f:
                for line in f:
                    if not line.rstrip().endswith('.txt'):
                        mustpass_file_is_index = False
                        break
                    else:
                        whitelist.add_txt(mustpass_dir + '/' + line.rstrip())
            if not mustpass_file_is_index:
                whitelist.add_txt(mustpass_file)

        trie.filter_whitelist(whitelist)
        return trie

    def binary(self):
        return self.pm.build_root() + "/opt/deqp/modules/vulkan/deqp-vk"

    def blacklist(self, all_tests):
        # filter tests for the platform
        for blacklist_file in get_blacklists():
            blacklist = DeqpTrie()
            blacklist.add_txt(blacklist_file)
            all_tests.filter(blacklist)


class VulkanTester(object):
    def __init__(self, env, cpus=None):
        if not env:
            env = {}
        self.env = env
        self.cpus = cpus

    def build(self):
        pass
    def clean(self):
        pass
    def test(self):
        pm = ProjectMap()
        global_opts = Options()
        if global_opts.arch == "m64":
            icd_name = "intel_icd.x86_64.json"
        elif global_opts.arch == "m32":
            icd_name = "intel_icd.i686.json"
        self.env.update({"VK_ICD_FILENAMES": pm.build_root()
                         + "/share/vulkan/icd.d/" + icd_name,
                         "ANV_ABORT_ON_DEVICE_LOSS": "true",
                         "MESA_VK_WSI_PRESENT_MODE" : "immediate"})

        tester = DeqpTester()
        binary = pm.build_root() + "/opt/deqp/modules/vulkan/deqp-vk"
        params = ["--deqp-surface-type=fbo", "--deqp-shadercache=disable"]
        o = Options()
        if 'icl' in o.hardware:
            self.cpus = multiprocessing.cpu_count() // 2

        results = tester.test(binary,
                              VulkanTestList(),
                              params,
                              env=self.env, cpus=self.cpus,
                              log_mem_stats=False)
        config = get_conf_file(o.hardware, o.arch,
                               project=pm.current_project())
        tester.generate_results(results, ConfigFilter(config, o))


if __name__ == '__main__':
    hardware = Options().hardware
    env = {}
    fs = Fulsim()
    import_build = True
    # VulkanTester defaults to all CPUs when this is None
    cpus = None

    if "_sim" in hardware and hardware in fs.platform_keyfile:
        if fs.is_supported():
            # sim-drm.py is invoked by Fulsim.get_env, and requires build_root
            # to be populated. To work around this, import build_root now and
            # call build with import_build=False so that the build_root is only
            # imported once
            import_build = False
            Export().import_build_root()
            env.update(fs.get_env())
            if hardware == 'dg1_sim':
                cpus = multiprocessing.cpu_count() // 2
        else:
            print("Unable to run simulated hardware in this environment!")
            sys.exit(1)

    build(VulkanTester(env=env, cpus=cpus), time_limit=SlowTimeout(),
          import_build=import_build)
