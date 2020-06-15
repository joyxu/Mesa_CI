import argparse
import configparser
import glob


parser = argparse.ArgumentParser(description=("Parses platform conf files for "
                                              "failures blamed on a specific "
                                              "Mesa version."))
parser.add_argument('mesa_sha', help='Mesa commit SHA to search for.')
opts = parser.parse_args()

configs = glob.glob("*/*.conf")
configs = [c for c in configs if 'blacklist' not in c]

failures = {}
for config in configs:
    c = configparser.ConfigParser()
    try:
        c.read(config)
    except configparser.ParsingError:
        print("skipping file because it couldn't be parsed: {}".format(config))
        continue
    hw = config.split('/')[-1].split('.')[0]
    for section in ['expected-failures', 'expected-crashes']:
        if section not in c:
            continue
        for failure, ver in c.items(section):
            if opts.mesa_sha not in ver:
                continue
            hw_list = []
            if failure not in failures:
                failures[failure] = hw_list
            failures[failure].append(hw)

print('Found failures blamed on "mesa %s":' % opts.mesa_sha)
for failure, hw_list in failures.items():
    print(failure)
    print('\t%s' % ', '.join(hw_list))
