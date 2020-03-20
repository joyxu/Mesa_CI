import argparse
import configparser
import glob


def main():
    parser = argparse.ArgumentParser(description=("Parses platform conf "
                                                  "files for failures that "
                                                  "are unique to s given "
                                                  "hardware platform"))
    parser.add_argument('hw', help=('Platform to find unique failures in CI '
                                    'for, e.g. "gen9_iris"'))
    opts = parser.parse_args()
    projects = glob.glob("*-test") + ['webgl']

    hw_config_file = opts.hw + '.conf'
    for project in projects:
        configs = [c for c in glob.glob(project + "/*.conf") if 'blacklist' not in c]

        c = configparser.ConfigParser(allow_no_value=True)
        try:
            c.read(project + '/' + hw_config_file)
        except configparser.ParsingError as e:
            print("skipping file in project {} because it couldn't be "
                  "parsed: {}".format(project, hw_config_file))
            continue
        hw_project_failures = []
        for section in ['expected-failures', 'expected-crashes']:
            if section not in c:
                continue
            for failure, _ in c.items(section):
                hw_project_failures.append(failure)
        unique_fails = [f for f in hw_project_failures]
        for config in configs:
            if config == project + '/' + hw_config_file:
                continue
            c = configparser.ConfigParser(allow_no_value=True)
            try:
                c.read(config)
            except configparser.ParsingError as e:
                print("skipping file because it couldn't be "
                      "parsed: {}".format(config))
                continue
            for section in ['expected-failures', 'expected-crashes']:
                if section not in c:
                    continue
                section_lower = [f.lower() for f in c[section]]
                unique_fails = [f for f in unique_fails if f.lower() not in section_lower]
        print(project + ' (count: ' + str(len(unique_fails)) + ')')
        if not unique_fails:
            continue
        for f in unique_fails:
            print('\t{}'.format(f))




if __name__ == "__main__":
    main()
