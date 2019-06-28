# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# crawler.py  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Created by: Jordan Bonecutter for HPCForge  # # # # # # # # # # # # # #
# 28 June 2019  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import json     as JSON
import jread    as JREAD
import time     as TIME
import os, io
import subprocess
import re

magic_string = r"heap out of memory"
REGEX        = None
SUBP         = None

def snap(url, timeout):
    global REGEX, magic_string

    # Path on my machine to the ZBrowse file
    PATH = "../zbrowse/js/index.js"
    # Use node.js to execute it
    EXEC = "node"
    # Add the http prefix to the url
    PRFX = "https://www."
    # Redirect stdout to a file
    new_sout = open("sout.snp", "w")
    new_serr = open("serr.snp", "w")
    # Execute the node.js program
    SUBP = subprocess.Popen(args=(EXEC, PATH, PRFX+url), stdout=new_sout, stderr=new_serr)
    # We want to wait on a timeout so 
    # we need to try & except
    try:
        # Wait
        SUBP.wait(timeout)
        # Close the files so they save
        new_sout.close()
        new_serr.close()
        # Check stderr for an error message
        ec = open("serr.snp", "r")
        if REGEX == None:
            REGEX = re.compile(magic_string)
        em = REGEX.search(ec.read())
        # If there was an out of memory error
        if em != None:
            # Close the error fd
            ec.close()
            # Set the tree to empty
            t = "{}"
        # Otherwise if the run was succesful
        else:
            # Reopen it 
            # TODO: Find a better way to do this
            # than closing & reopening a file
            r = open("sout.snp", "r")
            # Read it
            t = r.read()
            # Close it again
            r.close()
            # Remove it
            os.system("rm -r *.snp")
            SUBP = None
    except:
        # If we timed out, kill the subproc
        SUBP.kill()
        SUBP = None
        # Return an empty dictionary
        t = "{}"
        # Close redirected stdout
        new_sout.close()
        # Remove temp file
        os.system("rm -r *.snp")
    return t

def crawl(sites):
    # local variables
    t0    = 1

    start = 0
    end   = 0
    tot   = 0

    # Forever while loop
    while True:
        # Iterate through all sites in
        # the given list
        for site in sites.keys():
            # Use ZBrowse to get a snap
            # of the sites
            #
            # We will time the snap so that
            # we can adjust the timeout value
            # accordingly
            start = TIME.time()
            s     = "hi"#snap(site, t0)
            end   = TIME.time()
            tot   = end-start
            # If we timed out
            if tot >= t0:
                # Double the timeout value
                t0 *= 2
                continue
            # If we didn't timeout, use a running
            # contraharmonic mean (chm to emphasize
            # large values, it's better to not timeout
            # than to timeout)
            else:
                t0 = ((((t0*t0)+((tot+1)*(tot+1)))/(t0+tot)))

            # If for whatever reason the snapshot
            # failed, continue looping
            if s == "hi":
                continue

            # Extract the tree
            t = JREAD.get_tree(s)

            # Save it to a file
            f = open("sites/" + site + "[" + str(sites[site]) + "].json", "w")
            JSON.dump(t, f)
            f.close()
            sites[site] += 1

def main():
    SITES = {"yahoo.com": 0, "forbes.com": 0, "bbc.com": 0}
    crawl(SITES)

# main function call
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        if SUBP != None:
            os.kill(SUBP.pid, signal.SIGTERM)
