import argparse
import glob
import git

import os.path

def main():
    parser = argparse.ArgumentParser(
        description=("Clear test suite platform configs"))
    parser.add_argument('-s', '--stage', action='store_true',
                        help='Stage configs in git after clearing them.')
    parser.add_argument('--hw_config_path', help=('path to config file if different '
                                                  'from mesa_jenkins'))
    opts = parser.parse_args()

    clean_conf_contents = ("[expected-failures]\n"
                           "[expected-crashes]\n"
                           "[fixed-tests]\n")

    config_path = ''
    if opts.hw_config_path is not None:
        config_path = os.path.expanduser(opts.hw_config_path) + '/'

    configs = glob.glob(config_path + "*/*.conf")
    configs = [c for c in configs if 'blacklist' not in c]
    for config in configs:
        print("Clearing conf: {}".format(config))
        with open(config, 'w') as f:
            f.write(clean_conf_contents)

    if opts.stage:
        repo = git.Repo('.')
        if config_path != '':
            repo = git.Repo(config_path)

        repo.index.add(configs)


if __name__ == "__main__":
    main()
