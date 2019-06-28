# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# snapshot.py # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Created by: Jordan Bonecutter for HPCForge  # # # # # # # # # # # # # #
# 25 June 2019  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import os, io
import subprocess

def snap(url, timeout):
    # Path on my machine to the ZBrowse file
    PATH = "../zbrowse/js/index.js"
    # Use node.js to execute it
    EXEC = "node"
    # Add the http prefix to the url
    PRFX = "http://www."
    # Redirect stdout to a file
    new_sout = open("tmp.snp", "w")
    # Execute the node.js program
    p = subprocess.Popen(args=(EXEC, PATH, PRFX+url), stdout=new_sout)
    # We want to wait on a timeout so 
    # we need to try & except
    try:
        # Wait
        p.wait(timeout)
        # Close the file so that it saves
        new_sout.close()
        # Reopen it 
        # TODO: Find a better way to do this
        # than closing & reopening a file
        r = open("tmp.snp", "r")
        # Read it
        t = r.read()
        # Close it again
        r.close()
        # Remove it
        os.system("rm -r tmp.snp")
    except subprocess.TimeoutExpired:
        # If we timed out, kill the subproc
        p.kill()
        # Return an empty dictionary
        t = "{}"
        # Close redirected stdout
        new_sout.close()
        # Remove temp file
        os.system("rm -r tmp.snp")
    return t

if __name__ == "__main__":
    print(snap("google.com/", 100))
