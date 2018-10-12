#!/usr/bin/python

import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..", "repos", "mesa_ci"))
import build_support as bs

class DrmBuilder(bs.AutoBuilder):
    def __init__(self):
        bs.AutoBuilder.__init__(
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
    global_opts = bs.Options()

    options = [
        '-Detnaviv=true',
        '-Dfreedreno=true',
    ]
    if global_opts.config != 'debug':
        options.extend(['-Dbuildtype=release', '-Db_ndebug=true'])
    b = bs.builders.MesonBuilder(extra_definitions=options, install=True)
    bs.build(b)


def main():
    pm = bs.ProjectMap()
    sd = pm.project_source_dir(pm.current_project())
    if os.path.exists(os.path.join(sd, 'meson.build')):
        meson_build()
    else:
        bs.build(DrmBuilder())


if __name__ == '__main__':
    main()
