# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# main.py # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Created by: Jordan Bonecutter for HPCForge  # # # # # # # # # # # # # #
# 15 July 2019  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import sys
import argparse
import adbrowser
import json

def main(argv):
    try:
        flags        = "i:qhp" 
        quiet        = False
        browse       = None
        picture      = False
        restore_file = "options.json"
        args         = argparse.parse(flags, argv)

        for flag, arg in args:
            if flag == "-i":
                if arg == None:
                    print(argv[0]+": argument \"-i\" requires 1 positional argument")
                    return 1
                else:
                    restore_file = arg
            elif flag == "-p":
                picture = True
            elif flag == "-q":
                quiet = not quiet
            elif flag == "-h":
                print("usage: ./"+argv[0]+" -i <restore_file>")
                print("extra: -q (toggle quiet mode), -h (help mode), -p (save picture)")
                return 0
            else:
                print(argv[0]+": invalid argument \""+flag+"\"")
                return 1

        browse = adbrowser.Adbrowser.fromfile(restore_file)
        browse.crawl(10000000, not quiet, picture)
        return 0

    except KeyboardInterrupt:
        browse.stop()
        browse.save()
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
