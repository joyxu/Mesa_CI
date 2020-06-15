import argparse
import glob
import git


def main():
    parser = argparse.ArgumentParser(
        description=("Clear test suite platform configs"))
    parser.add_argument('-s', '--stage', action='store_true',
                        help='Stage configs in git after clearing them.')
    opts = parser.parse_args()

    clean_conf_contents = ("[expected-failures]\n"
                           "[expected-crashes]\n"
                           "[fixed-tests]\n")

    configs = glob.glob("*/*.conf")
    configs = [c for c in configs if 'blacklist' not in c]
    for config in configs:
        print("Clearing conf: {}".format(config))
        with open(config, 'w') as f:
            f.write(clean_conf_contents)

    if opts.stage:
        repo = git.Repo('.')
        repo.index.add(configs)


if __name__ == "__main__":
    main()
