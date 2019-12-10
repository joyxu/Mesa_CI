#!/usr/bin/python
import datetime
import os
import json
import random
import shutil
import sys
from . import ProjectMap, Options, RevisionSpecification, run_batch_command, Export, check_gpu_hang

class PerfBuilder(object):
    def __init__(self, benchmark, iterations=2, discard=0,
                 env=None, custom_iterations_fn=None):
        self._benchmark = benchmark
        self._iterations = iterations
        self._discard = discard
        self._pm = ProjectMap()
        self._env = env
        self._opt = Options()
        if self._env is None:
            self._env = {}
        build_root = self._pm.build_root()
        hw_prefix = self._opt.hardware[:3]
        prefix = build_root + "/" + hw_prefix + "/usr/local/lib/"
        self._env["LD_LIBRARY_PATH"] = prefix + ":" + prefix + "dri"
        self._env["LIBGL_DRIVERS_PATH"] = prefix + "dri"
        self._opt.update_env(self._env)
        self._custom_iterations_fn = custom_iterations_fn

    def build(self):
        # todo(majanes) possibly verify that benchmarks are in /opt
        pass

    def set_resolution(self):
        env = self._env
        # set the resolution to 1080p
        (out, _) = run_batch_command(["xrandr"],
                                     streamedOutput=False,
                                     quiet=True,
                                     env=env)
        for line in out.splitlines():
            words = line.split()
            if words[1] != "connected" or words[2] == "secondary":
                continue
            run_batch_command(["xrandr", "--output", words[0], "--mode", "1920x1080"],
                              quiet=True, streamedOutput=False, env=env)
        
        (out, _) = run_batch_command(["xdpyinfo"],
                                     quiet=True,
                                     streamedOutput=False,
                                     env=env)
        for line in out.splitlines():
            if "dimensions:" not in line:
                continue
            if "1920x1080" not in line:
                print "ERROR: could not set screen resolution to 1080p"
                print line
                assert(False)
            # else resolution is correct
            break

    def test(self):
        iterations = self._iterations
        save_dir = os.getcwd()
        if self._opt.hardware == "builder":
            print "ERROR: hardware must be set to a specific sku.  'builder' is not a valid hardware setting."
            assert(False)
        hw = self._opt.hardware[:3]
        mesa_dir = "/tmp/build_root/" + self._opt.arch + "/" + hw + "/usr/local/lib"
        os.chdir(self._pm.project_source_dir("sixonix"))

        if os.name != "nt":
            self.set_resolution()

        benchmarks = self._benchmark
        if type(benchmarks) != type([]):
            benchmarks = [self._benchmark]
        scores = dict([[b,[]] for b in benchmarks])

        # build a list of each benchmark to run
        bench_runs = []
        iterations = self._iterations
        it_multiplier = 1
        if self._opt.type == "daily":
            it_multiplier = 5
        for b in benchmarks:
            if self._custom_iterations_fn:
                iterations = self._custom_iterations_fn(b, hw) or iterations
            bench_runs += [b] * iterations * it_multiplier

        random.shuffle(bench_runs)
        iteration = 0
        for b in bench_runs:
            cmd = []
            if b in ["manhattan",
                     "manhattan_o",
                     "car_chase",
                     "car_chase_o",
                     "trex",
                     "trex_o",
                     "fill",
                     "fill_o",
                     "tess",
                     "tess_o",
                     "heaven",
                     "valley",
                     "OglBatch0",
                     "OglBatch1",
                     "OglBatch2",
                     "OglBatch3",
                     "OglBatch4",
                     "OglBatch5",
                     "OglBatch6",
                     "OglBatch7",
                     "OglCSCloth",
                     "OglCSDof",
                     "OglDeferred",
                     "OglDeferredAA",
                     "OglDrvRes",
                     "OglDrvShComp",
                     "OglDrvState",
                     "OglFillPixel",
                     "OglFillTexMulti",
                     "OglFillTexSingle",
                     "OglGeomPoint",
                     "OglGeomTriList",
                     "OglGeomTriStrip",
                     "OglHdrBloom",
                     "OglMultithread",
                     "OglPSBump2",
                     "OglPSBump8",
                     "OglPSPhong",
                     "OglPSPom",
                     "OglShMapPcf",
                     "OglShMapVsm",
                     "OglTerrainFlyInst",
                     "OglTerrainFlyTess",
                     "OglTerrainPanInst",
                     "OglTerrainPanTess",
                     "OglTexFilterAniso",
                     "OglTexFilterTri",
                     "OglTexMem128",
                     "OglTexMem512",
                     "OglVSDiffuse1",
                     "OglVSDiffuse8",
                     "OglVSInstancing",
                     "OglVSTangent",
                     "OglZBuffer"]:
                cmd = [sys.executable, "run_benchmark.py", b]
            else:
                cmd = ["./glx.sh", mesa_dir, b.upper()]
            print " ".join(cmd)
            (out, err) = run_batch_command(cmd, streamedOutput=False, env=self._env)
            if err:
                print "err: " + err
            if iteration >= self._discard:
                if not out:
                    print "ERROR: no score: " + b
                    continue
                scores[b].append(float(out.splitlines()[-1]))
            iteration += 1

        os.chdir(save_dir)
        for b in benchmarks:
            result = {}
            benchmark = b
            if os.name == "nt":
                r = "UFO"
            else:
                r = str(RevisionSpecification().revision("mesa"))
            result[benchmark] = {hw: {"mesa=" + r: [{"score": scores[benchmark]}]}}
            out_dir = "/tmp/build_root/" + self._opt.arch + "/scores/" + benchmark + "/" + hw
            if os.name == "nt":
                out_dir = self._pm.project_source_dir("sixonix") + "/windows/scores/" + benchmark + "/" + hw
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            outf = out_dir + "/" + datetime.datetime.now().isoformat().replace(":", ".") + ".json"
            with open(outf, 'w') as of:
                json.dump(result, fp=of)
                
        check_gpu_hang(False)
        Export().export_perf()

    def clean(self):
        if os.name == "nt":
            out_dir = self._pm.project_source_dir("sixonix") + "/windows/scores"
            if os.path.exists(out_dir):
                shutil.rmtree(out_dir)
