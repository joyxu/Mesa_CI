#!/usr/bin/python2
# encoding=utf-8
# Copyright © 2018 Intel Corporation

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Attempt to fetch build_support repository, then fetch additional
repositories.
"""

from __future__ import print_function
import argparse
import git
import importlib
import os
import sys
import time

build_support_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "repos", "mesa_ci"))
internal_build_support_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "repos", "mesa_ci_internal"))


def try_clone(repo, repo_dir):
    print('Trying to clone build support from {}'.format(repo))
    git.Repo.clone_from(repo, repo_dir)


def retry_checkout(repo, branch, fatal=False):
    repo_name = repo.git.working_dir.split('/')[-1]
    fail = True
    for i in range(15):
        repo.remotes['origin'].fetch()
        try:
            print("Checking out " + repo_name
                  + " commit (try {}/15)".format(i+1))
            repo.git.checkout([branch])
            fail = False
        except git.GitCommandError:
            print("Unable to checkout " + repo_name
                  + " commit, retrying in 15s..")
            time.sleep(15)
        else:
            break
    if fail and fatal:
        raise Exception("ERROR: Unable to checkout " + repo_name + " commit.")
    elif fail:
        print("Warn: Unable to checkout " + repo_name + " commit.")


if not os.path.exists(build_support_dir):
    repo_dir = os.path.dirname(build_support_dir)
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)

    try:
        try_clone("git://otc-mesa-ci.local/git/mesa_ci", build_support_dir)
    except git.exc.GitCommandError:
        try:
            try_clone("git://otc-mesa-ci.jf.intel.com/git/mesa_ci",
                      build_support_dir)
        except git.exc.GitCommandError:
            try:
                try_clone("https://gitlab.freedesktop.org/Mesa_CI/mesa_ci.git",
                          build_support_dir)
            except git.exc.GitCommandError:
                print("ERROR: could not clone sources")
                sys.exit(1)
bs_repo = git.Repo(build_support_dir)

if not os.path.exists(internal_build_support_dir):
    repo_dir = os.path.dirname(internal_build_support_dir)
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)
    try:
        try_clone("git://otc-mesa-ci.local/git/mesa_ci_internal",
                  internal_build_support_dir)
    except git.exc.GitCommandError:
        try:
            try_clone("ssh://git@gitlab.devtools.intel.com:29418/mesa_ci/mesa_ci_internal.git",
                      internal_build_support_dir)
        except git.exc.GitCommandError:
            print("WARN: could not clone mesa_ci_internal")

# Don't initialize an empty dir as a repo (i.e. if clone failed)
internal_bs_repo = None
if os.path.exists(internal_build_support_dir):
    internal_bs_repo = git.Repo(internal_build_support_dir)

parser = argparse.ArgumentParser(description="checks out branches and commits")
parser.add_argument('--branch', type=str, default="",
                    help="The branch to base the checkout on. (default: %(default)s)")
parser.add_argument('--project', type=str, default="",
                    help="Limit commits to repos required by the project. (default: none)")
parser.add_argument('--revspec', type=str, default="",
                    help=("XML file containing revision spec listing out "
                          "projects and revisions to fetch (default: none)"))
parser.add_argument('commits', metavar='commits', type=str, nargs='*',
                    help='commits to check out, in repo=sha format')
args = parser.parse_args()
# 'Commits' parameter is searched for mesa_ci repo, which fetch sources uses to
# check out instead of 'origin/master'
build_support_branch = 'origin/master'
internal_build_support_branch = 'origin/master'
if args.commits:
    for c in args.commits:
        repo, sha = c.lower().split('=')
        if repo == 'mesa_ci':
            build_support_branch = sha
        if repo == 'mesa_ci_internal':
            internal_build_support_branch = sha

retry_checkout(bs_repo, build_support_branch, fatal=True)
if internal_bs_repo:
    retry_checkout(internal_bs_repo, internal_build_support_branch)

# Load build_support modules
sys.path.insert(0, os.path.join(build_support_dir, "build_support"))
from dependency_graph import DependencyGraph
from project_invoke import RevisionSpecification
from project_map import ProjectMap
from repo_set import RepoSet, BuildSpecification
from options import Options

def main():
    repos = RepoSet()
    spec = BuildSpecification(repo_set=repos)

    limit_to_repos = {}
    # commits overrides versions in revspec
    if args.revspec and os.path.exists(args.revspec):
        for c in RevisionSpecification.from_xml_file(args.revspec).to_cmd_line_param().split():
            repo, sha = c.lower().split('=')
            limit_to_repos[repo] = sha
    if args.commits:
        for c in args.commits:
            repo, sha = c.lower().split('=')
            limit_to_repos[repo] = sha
    project = args.project
    branch = args.branch
    branchspec = None
    if branch:
        branchspec = spec.branch_specification(branch)

    if not project and branchspec:
        # we can infer the project from the --branch parameter
        project = branchspec.project

    deps = []
    if project:
        # only fetch sources that are required for the project
        deps = DependencyGraph(project,
                               Options(args =[sys.argv[0]]),
                               repo_set=repos).all_sources(allow_missing=True)
        # the project will not be a prerequisite of itself, but we do
        # need to get its sources.
        deps.append(project)
        repo_names = list(limit_to_repos.keys())
        for repo in repo_names:
            if repo not in deps:
                del limit_to_repos[repo]

    for repo in deps:
        if repo not in limit_to_repos:
            limit_to_repos[repo] = None

    # obtain any sources which were not present at invocation
    cloned_new_repo = repos.clone(limit_to_repos)

    if cloned_new_repo:
        # recreate objects based on new sources
        repos = RepoSet()
        spec = BuildSpecification(repo_set=repos)
        if branchspec:
            branchspec = spec.branch_specification(branch)
        
    if branchspec:
        # use the branch specification to configure any sources that remain indeterminate
        branchspec.set_revisions(limit_to_repos)

    fail = True
    for i in range(15):
        repos.fetch(limit_to_repos)
        try:
            print("Checking out specified commit (try {}/15)".format(i+1))
            repos.checkout(limit_to_repos)
            fail = False
        except git.GitCommandError:
            print("Unable to checkout specified commit, retrying in 15s..")
            time.sleep(15)
        else:
            break
    if fail:
        raise Exception("ERROR: Unable to checkout specified commit.")

    # fetch (but do not check out) all revisions that are required by
    # externals in the target projects.  They need to be in the cached
    # repo so that the component can check out the required commit
    # within its source tree.
    s_root = ProjectMap().source_root()
    sys.path.append(s_root)
    external_revisions = {}
    for project in deps:
        # check for get_external_revisions in each build.py
        build_dir = s_root + "/" + project
        if not os.path.exists(build_dir + "/build.py"):
            continue
        try:
            build_module = importlib.import_module(project + ".build")
            build_module.get_external_revisions(external_revisions)
        except:
            continue

    # obtain any sources which were not present at invocation
    if not external_revisions.keys():
        return

    cloned_new_repo = repos.clone(external_revisions.keys())
    if cloned_new_repo:
        # recreate objects based on new sources
        repos = RepoSet()

    for project, tags in external_revisions.items():
        if type(tags) != type([]):
            repos.fetch({project : tags})
            continue
        for tag in tags:
            repos.fetch({project : tag})

if __name__ == '__main__':
    main()
