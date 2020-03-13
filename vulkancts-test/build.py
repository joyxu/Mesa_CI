#!/usr/bin/python

import multiprocessing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from build_support import build
from options import Options
from project_map import ProjectMap
from testers import DeqpTester, DeqpTrie, ConfigFilter
from utils.command import run_batch_command
from utils.utils import get_conf_file, get_blacklists


class SlowTimeout:
    def __init__(self):
        self.timeout = 60
        hardware = Options().hardware
        if hardware in ["gen9atom", "bsw"]:
            self.timeout = 90

    def GetDuration(self):
        return self.timeout

class VulkanTestList(object):
    def __init__(self):
        self.pm = ProjectMap()

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
        # Detect the latest mustpass file to use, and use it
        mustpass_dir = (self.pm.project_source_dir("vulkancts")
                        + "/external/vulkancts/mustpass/")
        # The mustpass file in vk cts 1.1.5 changed to a single file for all vk
        # cts versions
        whitelist_txt = mustpass_dir + "/master/vk-default.txt"
        if os.path.exists(whitelist_txt):
            print("Using single whitelist")
        else:
            # Use old vk cts mustpass file
            versions = os.listdir(mustpass_dir)
            if '.gitignore' in versions:
                versions.remove('.gitignore')
            # Convert versions to an int and compare to get latest version
            versions.sort(key=lambda v: [int(i) for i in v.split('.')],
                          reverse=True)
            latest_version = versions[0]
            whitelist_txt = (mustpass_dir + '/' + latest_version
                             + "/vk-default.txt")
            print("Using whitelist for %s" % latest_version)
        whitelist = DeqpTrie()
        whitelist.add_txt(whitelist_txt)
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
        env = {"VK_ICD_FILENAMES" : pm.build_root() + \
               "/share/vulkan/icd.d/" + icd_name,
               "ANV_ABORT_ON_DEVICE_LOSS" : "true",
               "MESA_VK_WSI_PRESENT_MODE" : "immediate"}
        tester = DeqpTester()
        binary = pm.build_root() + "/opt/deqp/modules/vulkan/deqp-vk"
        params = ["--deqp-surface-type=fbo", "--deqp-shadercache=disable"]
        o = Options()
        cpus = None
        if 'icl' in o.hardware:
            cpus = multiprocessing.cpu_count() // 2

        results = tester.test(binary,
                              VulkanTestList(),
                              params,
                              env=env, cpus=cpus, log_mem_stats=True)
        config = get_conf_file(o.hardware, o.arch, project=pm.current_project())
        tester.generate_results(results, ConfigFilter(config, o))

if __name__ == '__main__':
    build(VulkanTester(),
          time_limit=SlowTimeout())

