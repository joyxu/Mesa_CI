#!/usr/bin/env python3

import os
import sys
import os.path as path
from mesonbuild import optinterpreter
sys.path.append(path.join(path.dirname(path.abspath(sys.argv[0])), "..",
                          "repos", "mesa_ci", "build_support"))
from build_support import build
from builders import MesonBuilder
from options import Options
from project_map import ProjectMap
from project_invoke import ProjectInvoke
from repo_set import RevisionSpecification, RepoSet

def main():
    global_opts = Options()
    sd = ProjectMap().project_source_dir()

    options = [
        '-Ddri-drivers=i965,i915',
        '-Dvulkan-drivers=intel',
        '-Dtools=intel',
        '-Dprefer-iris=false',
        '-Dglvnd=true',
    ]
    if (os.path.exists(ProjectMap().project_source_dir() +
                       "/src/gallium/drivers/iris")):
        options += ['-Dgallium-drivers=iris',
                    '-Dllvm=false']

    minor_version = tuple(ProjectInvoke().get_mesa_version().quad[0:2])
    cmp_version = (20, 3)
    platform_options = '-Dplatforms=x11'
    if minor_version < cmp_version:
        platform_options = ','.join([platform_options, 'drm'])
    options += [platform_options]

    cpp_args = None
    if global_opts.config == 'debug':
        # default buildtype is debugoptimized.

        # only applies to 64 bit binaries, overridden by cross file.
        # DEBUG was removed from debugoptimized because it is slow.
        cpp_args = "-DDEBUG"
    else:
        # WARN: 32 bit release builds will have -DDEBUG due to cross file (and
        # be slow)
        options.extend(['-Dbuildtype=release', '-Db_ndebug=true'])

    # Build/install mi_builder tests if this version of Mesa includes them
    oi = optinterpreter.OptionInterpreter('')
    oi.process(os.path.join(sd, 'meson_options.txt'))
    if 'install-intel-gpu-tests' in oi.options:
        options.append('-Dinstall-intel-gpu-tests=true')

    b = MesonBuilder(extra_definitions=options, install=True,
                     cpp_args=cpp_args)
    build(b)


if __name__ == '__main__':
    main()
