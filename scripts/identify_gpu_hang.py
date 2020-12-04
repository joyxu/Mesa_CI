#!/usr/bin/env python3
import os
import sys
import re

hang_match = re.compile(r".*\](.*)\[(\d*)\]")
while(True):
    line = sys.stdin.readline()
    if "gpu hang" not in line.lower():
        continue
    print("Found GPU Hang: " + line)
    found = hang_match.match(line)
    if not found:
        print("ERROR: could not find PID in string")
        continue
    msg = found.group(1)
    proc = found.group(2)
    if not os.path.exists("/proc/" + proc + "/cmdline"):
        print("Unable to determine hanging process, path doesn't exist: "
              + "/proc/" + proc + "/cmdline")
        continue
    cmdline = open("/proc/" + proc + "/cmdline").read()
    print("Hanging process: " + cmdline.replace("\0", " "))

    module = None
    for token in msg.split():
        if "glcts" in msg:
            module = "glcts"
        if "deqp" not in msg:
            continue
        module = token.split("-")[-1]
        if module == "vk":
            module = "vulkan"
    if not module:
        print("Error: could not determine module from process name: " + msg)

    for arg in cmdline.split("\0"):
        if "qpa" not in arg:
            continue
        qpa = arg.split("=")[-1]
        qpa_path = "/tmp/build_root/m64/opt/deqp/modules/" + module + "/" + qpa
        if module == "glcts":
            qpa_path = "/tmp/build_root/m64/bin/gl/modules/" + qpa
        current_test = "none"
        with open(qpa_path, 'r', errors='replace') as f:
            for qpaline in f.readlines():
                if qpaline.startswith("#beginTestCaseResult"):
                    current_test = qpaline.split(" ")[-1]
                if qpaline.startswith("#endTestCaseResult"):
                    current_test = "none"
        print("Hanging test: " + current_test)
