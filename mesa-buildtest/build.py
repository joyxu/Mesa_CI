#!/usr/bin/env python3

import sys
import os
import subprocess
from mesonbuild import optinterpreter, coredata
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from builders import MesonBuilder
from build_support import build
from export import Export
from options import Options
from project_map import ProjectMap


def main():
    pm = ProjectMap()
    sd = pm.project_source_dir(pm.current_project())

    save_dir = os.getcwd()

    global_opts = Options()

    # Autodetect valid gallium drivers in Mesa source
    gallium_drivers = set()
    gallium_drivers_exclude = set(['i915', 'd3d12'])
    oi = optinterpreter.OptionInterpreter('')
    oi.process(os.path.join(sd, 'meson_options.txt'))
    for k, v in oi.options.items():
        key = k
        # k is OptionKey in newer Meson, but this type doesn't exist in older
        # Meson, so testing for type == str is needed
        if not isinstance(k, str):
            key = k.name
        if key != 'gallium-drivers':
            continue
        if not v.choices:
            raise RuntimeError(f"ERROR: no meson choices for: {key}")
        gallium_drivers = set(v.choices)
        break
    gallium_drivers -= gallium_drivers_exclude
    if not gallium_drivers:
        raise RuntimeError("ERROR: Failed to parse available gallium "
                           "drivers from meson options")

    options = [
        '-Dbuild-tests=true',
        '-Dgallium-drivers={}'.format(','.join(gallium_drivers)),
        '-Dgallium-vdpau=true',
        '-Dgallium-xvmc=true',
        '-Dgallium-xa=true',
        '-Dgallium-va=true',
        '-Dgallium-nine=true',
        '-Dgallium-opencl=standalone',
        '-Dtools=all',
    ]

    # the knob for omx changed durring the 18.1 cycle, if tizonia support is
    # present we need to use bellagio, otherwise we need true.
    with open(os.path.join(sd, 'meson_options.txt')) as f:
        for l in f:
            if 'tizonia' in l:
                options.append('-Dgallium-omx=bellagio')
                break
        else:
            options.append('-Dgallium-omx=true')
    if global_opts.config != 'debug':
        options.extend(['-Dbuildtype=release', '-Db_ndebug=true'])
    b = MesonBuilder(extra_definitions=options, install=False)

    try:
        build(b)
    except subprocess.CalledProcessError as e:
        # build may have taken us to a place where ProjectMap doesn't work
        os.chdir(save_dir)
        Export().create_failing_test("mesa-meson-buildtest", str(e))

if __name__ == '__main__':
    main()
