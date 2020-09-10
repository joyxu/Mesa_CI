#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                             "..", "repos", "mesa_ci", "build_support"))
from build_support import build
from builders import AutoBuilder, MesonBuilder
from options import Options
from project_map import ProjectMap


class DrmBuilder(AutoBuilder):
    def __init__(self):
        AutoBuilder.__init__(
            self,
            configure_options=[
                '--enable-etnaviv-experimental-api',
                '--enable-freedreno',
            ],
        )

    def test(self):
        # libdrm now has a 2-minute long test, which is too long to
        # wait for.
        pass


def meson_build():
    global_opts = Options()

    options = [
        '-Detnaviv=true',
        '-Dfreedreno=true',
    ]
    if global_opts.config != 'debug':
        options.extend(['-Dbuildtype=release', '-Db_ndebug=true'])
    b = MesonBuilder(extra_definitions=options, install=True)
    build(b)


def main():
    pm = ProjectMap()
    sd = pm.project_source_dir(pm.current_project())
    if os.path.exists(os.path.join(sd, 'meson.build')):
        meson_build()
    else:
        build(DrmBuilder())


if __name__ == '__main__':
    main()
