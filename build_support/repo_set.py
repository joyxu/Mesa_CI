# Copyright (C) Intel Corp.  2014.  All Rights Reserved.

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice (including the
# next paragraph) shall be included in all copies or substantial
# portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE COPYRIGHT OWNER(S) AND/OR ITS SUPPLIERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

#  **********************************************************************/
#  * Authors:
#  *   Mark Janes <mark.a.janes@intel.com>
#  **********************************************************************/

import hashlib
import json
import os
import signal
import subprocess
import sys
import time
import xml.etree.cElementTree as et

import git

from . import ProjectMap
from . import Options
from . import run_batch_command

class _ProjectBranch:
    def __init__(self, projectName):
        # default to master branch
        self.branch = "origin/master"
        self.name = projectName
        self.sha = None
        self.trigger = False

class BranchSpecification:
    """This class tracks a "branch set" in the build's git repositories
    which define a single logical build.  A change to any of the
    branches will result in a world build.

    """
    def __init__(self, branch_tag, repos=None):
        self._project_branches = {}
        self.name = branch_tag.attrib["name"]
        self.project = branch_tag.attrib["project"]
        if not repos:
            repos = RepoSet()
        self._repos = repos

        # by default, all repos are at origin/master
        for name in repos.projects():
            pb = _ProjectBranch(name)
            self._project_branches[name] = pb
            pb.branch = repos.branch(name)

        # override the defaults
        for a_project in branch_tag:
            name = a_project.tag
            if not self._project_branches.has_key(name):
                # repo unavailable
                continue
            self._project_branches[name].trigger = True
            # allow the spec to set a "stable" branch that won't trigger
            if a_project.attrib.has_key("trigger"):
                trigger = (a_project.attrib["trigger"] == "true")
                self._project_branches[name].trigger = trigger
            if a_project.attrib.has_key("branch"):
                self._project_branches[name].branch = a_project.attrib["branch"]

        invalid = []
        for (name, branch) in self._project_branches.iteritems():
            repo = repos.repo(branch.name)
            if not repo:
                continue
            try:
                branch.sha = repo.commit(branch.branch).hexsha
            except:
                invalid.append(name)
        for i in invalid:
            del(self._project_branches[i])

    def update_commits(self):
        # get the current commit for each project
        self._repos.fetch()
        for (_, branch) in self._project_branches.iteritems():
            repo = self._repos.repo(branch.name)
            branch.sha = repo.commit(branch.branch).hexsha
        
    def needs_build(self):
        # checks the commits on the branch repos to see if they have
        # been updated.
        for (_, branch) in self._project_branches.iteritems():
            if not branch.trigger:
                continue
            repo = self._repos.repo(branch.name)
            hexsha = repo.commit(branch.branch).hexsha
            if  branch.sha != hexsha:
                return branch.name + "=" + repo.git.rev_parse(hexsha, short=True)
        return False

    def checkout(self):
        """checks out the specified branches for each repository in the branch
        set """
        for (name, branch) in self._project_branches.iteritems():
            repo = self._repos.repo(name)
            success = False
            attempt = 0
            while not success and attempt < 10:
                try:
                    attempt += 1
                    repo.git.reset("--hard")
                    repo.git.checkout(["-f", branch.branch])
                    success = True
                except:
                    print "Encountered error checking out"
                    time.sleep(10)
                    run_batch_command(["rm", "-f", repo.working_tree_dir + "/.git/index.lock"])


class TimeoutException(Exception):
    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return self._msg

def is_build_lab():
    buildspec = ProjectMap().build_spec()
    master_host = buildspec.find("build_master").attrib["hostname"]
    p = subprocess.Popen(["ping", "-c", "1", "-w", "1", "-q", master_host + ".local"],
                         stderr=open(os.devnull, "w"), stdout=open(os.devnull, "w"))
    p.communicate()
    if p.returncode:
        # error from ping: not in build lab
        return False
    return True
    
    
class RepoSet:
    """this class represents the set of git repositories which are
    specified in the build_specification.xml file."""
    def __init__(self, clone=False):
        buildspec = ProjectMap().build_spec()
        self._repos = {}
        # key is project, value is dictionary of remote name => remote object
        self._remotes = {}
        # key is project, value is the default branch for the repo (usually master)
        self._branches = {}
        if type(buildspec) == str or type(buildspec) == unicode:
            buildspec = et.parse(buildspec)
        repo_dir = ProjectMap().source_root() + "/repos"
        repos = buildspec.find("repos")

        build_lab = is_build_lab()
        build_lab_git = "git://" + \
                        ProjectMap().build_spec().find("build_master").attrib["hostname"] + \
                        ".local/git/"
        attempts = 1
        if build_lab:
            attempts = 10

        # fetch all the repos into _repo_dir
        for tag in repos:
            project = tag.tag
            url = tag.attrib["repo"]
            if build_lab:
                url = build_lab_git + project + "/origin"
            branch = "origin/master"
            if tag.attrib.has_key("branch"):
                branch = tag.attrib["branch"]

            # prohibit double entry
            assert not self._repos.has_key(project)
            project_repo_dir = repo_dir + "/" + project
            if not os.path.exists(project_repo_dir) and clone:
                os.makedirs(project_repo_dir)
                success = False
                for attempt in range(0,attempts):
                    if attempt > 0:
                        time.sleep(10)
                    try:
                        print "attempting clone of " + url
                        git.Repo.clone_from(url,
                                            project_repo_dir)
                        success = True
                        break
                    except:
                        print "WARN: unable to clone repo: " + url
                if not success and not build_lab:
                    os.makedirs(project_repo_dir + "/do_not_use")

            if os.path.exists(project_repo_dir + "/do_not_use"):
                continue

            repo = git.Repo(project_repo_dir)
            self._repos[project] = repo
            self._remotes[project] = {}
            self._branches[project] = branch

            for remote in repo.remotes:
                self._remotes[project][remote.name] = remote

            for a_remote in tag.findall("remote"):
                remote_name = a_remote.attrib["name"]
                if not self._remotes[project].has_key(remote_name) and clone:
                    url = a_remote.attrib["repo"]
                    if build_lab:
                        url = build_lab_git + project + "/" + remote_name
                    for attempt in range(0,attempts):
                        print "Adding remote: " + remote_name + " " + url
                        success = False
                        try:
                            if attempt > 0:
                                time.sleep(10)
                            remote = repo.create_remote(remote_name, url)
                            remote.fetch()
                            success = True
                            self._remotes[project][remote_name] = remote
                            break
                        except:
                            print "WARN: remote not available: " + url
                            repo.delete_remote(remote_name)
                    if not success and not build_lab:
                        # make a dummy remote, so it doesn't attempt to fetch later
                        remote = repo.create_remote(remote_name, project_repo_dir)

    def repo(self, project_name):
        return self._repos[project_name]

    def branch(self, project_name):
        return self._branches[project_name]

    def projects(self):
        return self._repos.keys()

    def alarm(self, secs):
        if os.name != "nt":
            signal.alarm(secs)   # 5 minutes

    def fetch(self):
        def signal_handler(signum, frame):
            raise TimeoutException("Fetch timed out.")

        for repo in self._repos.values():
            garbage_collection_fail = repo.working_tree_dir + "/.git/gc.log"
            if os.path.exists(garbage_collection_fail):
                run_batch_command(["rm", "-f", garbage_collection_fail])
            try:
                repo.git.prune()
            except Exception as e:
                print "ERROR: git repo is corrupt, removing: " + repo.working_tree_dir
                run_batch_command(["rm", "-rf", repo.working_tree_dir])
                raise;
            if os.name != "nt":
                signal.signal(signal.SIGALRM, signal_handler)
            for remote in repo.remotes:
                print "fetching " + remote.url
                # 4 attempts
                success = False
                for _ in range(1,4):
                    try:
                        self.alarm(300)   # 5 minutes
                        remote.fetch()
                        self.alarm(0)
                        success = True
                        break
                    except git.GitCommandError as e:
                        print "error fetching: " + str(e)
                        self.alarm(0)
                        time.sleep(1)
                    except AssertionError as e:
                        print "assertion while fetching: " + str(e)
                        self.alarm(0)
                        time.sleep(1)
                    except TimeoutException as e:
                        print str(e)
                    except Exception as e:
                        print str(e)
                        time.sleep(1)
                if not success:
                    print "Failed to fetch remote, ignoring: " + remote.url
        # the fetch has left our repo objects in an inconsistent
        # state.  We need to recreate them.
        self.__init__()

    def branch_missing_revisions(self):
        """provides the revisions which are on master but are not on the
        current branch(es).  This information can be used to filter
        out known test failures that only exist on the branch

        """
        projects = self.projects()
        revs = []
        for project in projects:
            repo = self.repo(project)
            # branches can be long-lived: eg mesa_10.4.  300 commits
            # on the branch is long enough for 10.4
            branch_commits = [commit.hexsha for commit in repo.iter_commits(max_count=1200)]
            tmp_revs = []

            # branchs can be a long time in the past.  For 10.4, there
            # have been more than 1000 commits since the branch point.
            try:
                for master_commit in repo.iter_commits(self._branches[project], max_count=8000):
                    hexsha = master_commit.hexsha
                    if hexsha not in branch_commits:
                        tmp_revs.append(hexsha)
                        continue
                    print "Found branch point for " + project + ": " + hexsha
                    revs = revs + tmp_revs
                    break
            except(git.exc.GitCommandError):
                continue

        return revs

class RevisionSpecification:
    def __init__(self, from_string=None, from_cmd_line=None):
        # key is project, value is revision
        self._revisions = {}

        if from_string is not None:
            self.from_string(from_string)
            return

        if from_cmd_line is not None:
            self.from_cmd_line_param(from_cmd_line)
            return

        repo_set = RepoSet()
        projects = repo_set.projects()
        for p in projects:
            try:
                repo = repo_set.repo(p)
                rev = repo.git.rev_parse("HEAD", short=True)
            except:
                continue
            self._revisions[p] = rev

    def from_string(self, spec):
        if type(spec) == str or type(spec) == unicode:
            spec = et.fromstring(spec)
        assert(spec.tag == "RevSpec")
        self._revisions = spec.attrib

    def to_cmd_line_param(self):
        revs = []
        for (project, rev) in self._revisions.iteritems():
            if project == "mesa_jenkins":
                continue
            if project == "mesa_ci":
                continue
            if project == "prerelease":
                continue
            if project == "gmock":
                continue
            if project == "gtest":
                continue
            if project == "sixonix":
                continue
            if project == "apitrace":
                continue
            revs.append(project + "=" + rev)
        return " ".join(revs)

    def from_cmd_line_param(self, params):
        revs = []
        for rev in params:
            rev = rev.split("=")
            rev[1] = '"' + rev[1] + '"'
            revs.append(rev[0] + "=" + rev[1])
        rev_text = "<RevSpec " + " ".join(revs) + "/>"
        self.from_string(rev_text)

    def to_elementtree(self):
        elem = et.Element('RevSpec')
        for n, h in sorted(self._revisions.iteritems(), key=lambda x: x[0]):
            elem.set(n, h)
        return et.ElementTree(elem)

    def __str__(self):
        return et.tostring(self.to_elementtree().getroot())

    def checkout(self):
        repo_set = RepoSet()
        for (project, revision) in self._revisions.iteritems():
            project_repo = repo_set.repo(project)
            project_repo.git.checkout(["-f", revision])

    def revision(self, project):
        return self._revisions[project]

class RepoStatus:
    def __init__(self, buildspec=None):
        if not buildspec:
            buildspec = ProjectMap().build_spec()
        if type(buildspec) == str or type(buildspec) == unicode:
            buildspec = et.parse(buildspec)

        # key is project, value is repo object
        self._repos = RepoSet()

        # referencing the HEAD of an unfetched remote will fail.  This
        # happens the first time branches are polled
        # after. build_specification.xml has been updated to add a
        # remote.
        self._repos.fetch()

        self._branches = []

        branches = buildspec.find("branches")

        for branch in branches.findall("branch"):
            try:
                self._branches.append(BranchSpecification(branch, repos=self._repos))
            except:
                print "WARN: couldn't get status for branch: " + branch.attrib["name"]
                pass


    def poll(self):
        """returns list of branches that should be triggered"""
        ret_dict = {}
        self._repos.fetch()
        for branch in self._branches:
            trigger_commit = branch.needs_build()
            if trigger_commit:
                ret_dict[branch.name] = trigger_commit
                branch.update_commits()
        return ret_dict

class BuildSpecification:
    def __init__(self, buildspec=None):
        if not buildspec:
            buildspec = ProjectMap().build_spec()
        if type(buildspec) == str or type(buildspec) == unicode:
            buildspec = et.parse(buildspec)

        self._buildspec = buildspec
        self._reposet = RepoSet()
        self._branch_specs = {}

        for abranch in buildspec.findall("branches/branch"):
            try:
                branch = BranchSpecification(abranch, repos=self._reposet)
                self._branch_specs[branch.name] = branch
            except:
                print "WARN: couldn't get status for branch: " + abranch.attrib["name"]
                pass

    def branch_specification(self, branch_name):
        return self._branch_specs[branch_name]

    def checkout(self, branch_name, commits=None):
        if not commits:
            commits = []
        if branch_name in self._branch_specs:
            self._branch_specs[branch_name].checkout()
        else:
            print "WARN: branch not found, ignoring: " + branch_name
        rs = RevisionSpecification(from_cmd_line = commits)
        rs.checkout()

class ProjectInvoke:
    """this object summarizes the component and all options required to
    invoke a build on a single project.  Invocation can take place
    locally or on CI.  ProjectInvoke supports writing status files for
    the invoked build to a network folder, to prevent duplicate builds.

    """

    def __init__(self, options=None, revision_spec=None, 
                 project=None, from_string=None):
        if from_string:
            self.from_string(from_string)
            return

        if not options:
            options = Options()
        self.options = options

        if not project:
            project=ProjectMap().current_project()
        self.project = project

        if not revision_spec:
            revision_spec = RevisionSpecification()
        self.revision_spec = revision_spec

    def __str__(self):
        tag = et.Element("ProjectInvoke")
        tag.set("Project", self.project)
        tag.append(et.fromstring(str(self.revision_spec)))
        tag.append(self.options.to_elementtree())
        return et.tostring(tag)

    def from_string(self, string):
        tag = et.fromstring(string)
        self.project = tag.attrib["Project"]
        self.options = Options(from_xml=tag.find("Options"))
        revtag = tag.find("RevSpec")
        self.revision_spec = RevisionSpecification(from_string=revtag)
        
        
    def info_file(self):
        o = self.options
        shard_str = ""
        if o.shard != 0:
            shard_str = "_" + o.shard
        return "/".join([o.result_path, 
                         self.project,
                         o.arch,
                         o.config,
                         o.hardware, 
                         "_build_info" + shard_str + ".txt"])

    def _read_info(self):
        """returns a dictionary of status content"""
        info_file = self.info_file()
        if not os.path.exists(info_file):
            # sometimes network/mount hiccups make it seem like the
            # file is not there
            time.sleep(0.2)
            if not os.path.exists(info_file):
                return {}
            print "WARN: network hiccup detected"

        attempt_number = 0
        while attempt_number < 5:
            attempt_number += 1
            try:
                info_text = open(info_file, "r").read()
                info_dict = json.loads(info_text)
                return info_dict
            except:
                # network hiccup
                time.sleep(5)

        # failed to parse several times.
        return {}

    def _write_info(self, info_dict):
        info_file = self.info_file()
        info_dir = os.path.dirname(info_file)
        tries = 0
        while not os.path.exists(info_dir) and tries < 20:
            tries += 1
            if tries > 1:
                print "WARN: failed to make info directory: " + info_dir
                sys.stdout.flush()
                time.sleep(10)
                savedir = os.getcwd()
                try:
                    mount_dir = "/".join(info_dir.split("/")[:5])
                    print "WARN: changing to directory: " + mount_dir
                    sys.stdout.flush()
                    os.chdir(mount_dir)
                    print "WARN: success"
                    sys.stdout.flush()
                except:
                    pass
                os.chdir(savedir)
            try:
                os.makedirs(info_dir)
            except:
                # race condition means some other build may have
                # created the directory.
                pass
        open(info_file, "w").write(json.dumps(info_dict))

    def get_info(self, key, block=True):
        for _ in range(0,10):
            info = self._read_info()
            if info.has_key(key):
                return info[key]
            if not block:
                return None
            # possible that the data has not been flushed to the
            # server
            time.sleep(1)

    def set_info(self, key, value):
        info_dict = self._read_info()
        info_dict[key] = value
        self._write_info(info_dict)

    def hash(self, salt):
        """provides a string value to uniquely identify a build.  This is used
        to find builds and resolve clashes between similar builds on
        the jenkins server"""
        return hashlib.md5(salt + str(self)).hexdigest()
        
    def to_short_string(self):
        items = [self.project,
                 self.options.arch, 
                 self.options.config, 
                 self.options.hardware]
        if self.options.shard != "0":
            items.append(self.options.shard)
        return " ".join(items)
