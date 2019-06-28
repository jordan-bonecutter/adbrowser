# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# snapshot.py # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Created by: Jordan Bonecutter for HPCForge  # # # # # # # # # # # # # #
# 25 June 2019  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import os, io

def snap(url):
    # Path on my machine to the ZBrowse file
    PATH = "../zbrowse/js/index.js "
    # Use node.js to execute it
    EXEC = "node "
    # Add the http prefix to the url
    PRFX = "http://www."
    # Call the program redirecting stdout to a file
    os.system(EXEC + PATH + PRFX + url + " > tmp.snp")
    # Read stdout
    t = open("tmp.snp", "r").read()
    # Delete stdout tmp file
    os.system("rm -f tmp.snp")
    return t
