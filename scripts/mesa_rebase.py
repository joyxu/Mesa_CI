#!/usr/bin/env python3
import argparse
import datetime
import git
import sys
import time


def main():
    """ Rebase the current branch in repos/mesa onto either the given branch
    (with --rebase-onto) or origin/master, push the branch to a new tag, and
    return the sha of the rebased branch.
    Note: debug output printed to stderr, so that the final print in this
    script can be used by a shell"""
    parser = argparse.ArgumentParser(description=(''))
    parser.add_argument('--rebase-onto', help=('Rebase onto this branch '
                                               '(default: origin/master'))
    args = parser.parse_args()
    mesa_srcdir = 'repos/mesa'
    rebase_branch = 'origin/master'
    if args.rebase_onto:
        rebase_branch = args.rebase_onto
    mesa_repo = git.Repo(mesa_srcdir)
    mesa_orig_sha = mesa_repo.commit().hexsha
    print('Rebasing Mesa @ ' + mesa_orig_sha + ' onto ' + rebase_branch,
          file=sys.stderr)
    try:
        mesa_repo.git.rebase('-v', rebase_branch)
    except git.exc.GitCommandError as e:
        mesa_repo.git.rebase('--abort')
        print('ERROR: Failed to rebase branch:', file=sys.stderr)
        print(str(e), file=sys.stderr)
        sys.exit(1)
    tag_msg = mesa_orig_sha + ' rebased onto ' + rebase_branch
    tag_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    mesa_repo.create_tag(tag_name, ref=mesa_repo.commit(), message=tag_msg)
    remote = None
    try:
        remote = mesa_repo.remotes.ci_internal_rebase_mesa_repo
    except AttributeError:
        remote = mesa_repo.create_remote('ci_internal_rebase_mesa_repo',
                                         url='ssh://git@gitlab.devtools.intel.com:29418/mesa_ci/repos/mesa-rebase-testing.git')
    if not remote:
        print('ERROR: unable to configure remote for pushing tag',
              file=sys.stderr)
        sys.exit(1)

    print('Pushing tag "' + tag_name + '" to repo "' + remote.url + '"...',
          file=sys.stderr)
    tries = 1
    while tries <= 5:
        try:
            remote.push(1)
            break
        except git.exc.GitCommandError:
            print("Unable to push tag, retrying in 5 seconds (attempt " +
                  str(tries) + "/5)")
            time.sleep(5)
            tries += 1
            if tries > 5:
                print('ERROR: Unable to push tag to remote repo!')
                sys.exit(1)

    # print sha to stdout so it can be collected by a shell
    print(mesa_repo.commit().hexsha)


if __name__ == '__main__':
    main()
