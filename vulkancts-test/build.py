#!/usr/bin/python

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..", "repos", "mesa_ci"))
import build_support as bs

class SlowTimeout:
    def __init__(self):
        pass

    def GetDuration(self):
        return 60

class VulkanTestList(object):
    def __init__(self):
        self.pm = bs.ProjectMap()

    def tests(self, env):
        # provide a DeqpTrie with all tests
        deqp_dir = os.path.dirname(self.binary())
        os.chdir(deqp_dir)
        cmd = ["./" + os.path.basename(self.binary()),
               "--deqp-runmode=xml-caselist"]
        bs.run_batch_command(cmd, env=env)
        trie = bs.DeqpTrie()
        trie.add_xml("dEQP-VK-cases.xml")
        os.chdir(self.pm.project_build_dir())
        # Detect the latest mustpass file to use, and use it
        mustpass_dir = self.pm.project_source_dir("vulkancts") + "/external/vulkancts/mustpass/"
        versions = os.listdir(mustpass_dir)
        if '.gitignore' in versions:
            versions.remove('.gitignore')
        # Convert versions to an int and compare to get latest version
        versions.sort(key=lambda v: [int(i) for i in v.split('.')],
                      reverse=True)
        latest_version = versions[0]
        print("Using whitelist for %s" % latest_version)
        whitelist_txt = mustpass_dir + '/' + latest_version + "/vk-default.txt"
        whitelist = bs.DeqpTrie()
        whitelist.add_txt(whitelist_txt)
        trie.filter_whitelist(whitelist)

        return trie
    
    def binary(self):
        return self.pm.build_root() + "/opt/deqp/modules/vulkan/deqp-vk"

    def blacklist(self, all_tests):
        # filter tests for the platform
        o = bs.Options()
        blacklist_file = self.pm.project_build_dir() + o.hardware[:3] + "_expectations/vk_unstable_tests.txt"
        blacklist = bs.DeqpTrie()
        blacklist.add_txt(blacklist_file)
        all_tests.filter(blacklist)
        blacklist = bs.DeqpTrie()
        global_blacklist_file = (self.pm.project_build_dir() + '/'
                                 + "blacklist.txt")
        blacklist.add_txt(global_blacklist_file)
        all_tests.filter(blacklist)

class VulkanTester(object):
    def build(self):
        pass
    def clean(self):
        pass
    def test(self):
        pm = bs.ProjectMap()
        global_opts = bs.Options()
        if global_opts.arch == "m64":
            icd_name = "intel_icd.x86_64.json"
        elif global_opts.arch == "m32":
            icd_name = "intel_icd.i686.json"
        env = {"VK_ICD_FILENAMES" : pm.build_root() + \
               "/share/vulkan/icd.d/" + icd_name,
               "ANV_ABORT_ON_DEVICE_LOSS" : "true"}
        tester = bs.DeqpTester()
        binary = pm.build_root() + "/opt/deqp/modules/vulkan/deqp-vk"
        params = ["--deqp-surface-type=fbo"]
        if os.path.exists(pm.project_source_dir("vulkancts") + "/external/vulkancts/mustpass/1.1.2"):
            params.append("--deqp-shadercache=disable")
        results = tester.test(binary,
                              VulkanTestList(),
                              params,
                              env=env)
        o = bs.Options()
        config = bs.get_conf_file(o.hardware, o.arch, project=pm.current_project())
        tester.generate_results(results, bs.ConfigFilter(config, o))

bs.build(VulkanTester(),
         time_limit=SlowTimeout())

