# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# snapshot.py # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Created by: Jordan Bonecutter for HPCForge  # # # # # # # # # # # # # #
# 25 June 2019  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import os, io
from contextlib import redirect_stdout

def snap(url):
    PATH = "../zbrowse/js/index.js "
    EXEC = "node "
    PRFX = "http://www."
    os.system(EXEC + PATH + PRFX + url + " > tmp.snp")
    t = open("tmp.snp", "r").read()
    os.system("rm -f tmp.snp")
    return t
