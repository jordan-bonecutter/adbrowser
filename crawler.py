# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# crawler.py  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Created by: Jordan Bonecutter for HPCForge  # # # # # # # # # # # # # #
# 28 June 2019  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import json     as JSON
import jread    as JREAD
import time     as TIME
import datetime as DTTM
import getopt   as OPT
import os, io, sys
import subprocess
import re

magic_string = r"heap out of memory"
REGEX        = None
SUBP         = None
RESULTS      = None

OFNAME       = "res/crawl.json"
QUIET        = False

def qprint(s):
    if not QUIET:
        print(s)

def _clear_cache():
    hex_digits   = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
    # Clear browser cache
    # Haha! That's a little better I guess...
    # TODO: there is still a better way to do this...
    c_loc = "/Users/jordanbonecutter/Library/Caches/Google/Chrome\ Canary/Default/"
    for digit in hex_digits:
        os.system("rm -rf " + c_loc + "Cache/" + digit + "*")
        os.system("rm -rf " + c_loc + "Code Cache/js/" + digit + "*")
    os.system("rm -rf " + c_loc + "Cache/index")
    os.system("rm -rf " + c_loc + "Cache/index-dir/*")
    os.system("rm -rf " + c_loc + "Code Cache/js/index")
    os.system("rm -rf " + c_loc + "Code Cache/js/index-dir/*")
    os.system("rm -rf " + c_loc + "Storage/ext/*")

def snap(url, timeout, clear_cache):
    global REGEX, magic_string

    if clear_cache:
        _clear_cache()

    # Path on my machine to the ZBrowse file
    PATH = "../zbrowse/js/index.js"
    # Use node.js to execute it
    EXEC = "node"
    # Add the http prefix to the url
    PRFX = "https://www."
    # Redirect stdout to a file
    new_sout = open("sout.snp", "w")
    new_serr = open("serr.snp", "w")
    extra    = "--max_old_space_size=4096"
    # Execute the node.js program
    SUBP = subprocess.Popen(args=(EXEC, extra, PATH, PRFX+url), stdout=new_sout, stderr=new_serr)
    # We want to wait on a timeout so 
    # we need to try & except
    try:
        # Wait
        SUBP.wait(timeout)
        SUBP.kill()
        # Close the files so they save
        new_sout.close()
        new_serr.close()
        # Check stderr for an error message
        ec = open("serr.snp", "r")
        if REGEX == None:
            REGEX = re.compile(magic_string)
        em = REGEX.search(ec.read())
        ec.close()
        # If there was an out of memory error
        if em != None:
            # Set the tree to empty
            t = "{}"
            qprint("JS ran out of memory")
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
    except subprocess.TimeoutExpired:
        # If we timed out, kill the subproc
        SUBP.kill()
        SUBP = None
        # Return an empty dictionary
        t = "{}"
        # Close redirected stdout
        new_sout.close()
        # Remove temp file
        os.system("rm -r *.snp")
        qprint("Timeout")
    return t

def crawl(sites, save_image, restore):
    global RESULTS

    # local variables
    t0    = 45

    start = 0
    end   = 0
    tot   = 0
    if restore != None:
        with open(restore, 'r') as fi:
            RESULTS = JSON.loads(fi.read())
    else:
        RESULTS = {}
    for site in sites:
        if site not in RESULTS:
            RESULTS.update({site:{'snapshots':{}, 'timer':45}})

    # Forever while loop
    while True:
        # Iterate through all sites in
        # the given list
        for site in sites:
            # Use ZBrowse to get a snap
            # of the sites
            #
            # We will time the snap so that
            # we can adjust the timeout value
            # accordingly
            t0    = RESULTS[site]['timer']
            start = TIME.time()
            date  = str(DTTM.datetime.now())
            s     = snap(site, t0+5, True)
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
                t0 = (((t0*t0)+((tot)*(tot)))/(t0+tot))
    
            RESULTS[site]['timer'] = t0

            # If for whatever reason the snapshot
            # failed, continue looping
            if s == "{}" or s == None or s == "":
                qprint("Unknown error...")
                continue

            # Extract the tree
            t = JREAD.get_tree(s)
            RESULTS[site]['snapshots'].update({"date": date, "tree": t, "tree_format": "backreferenced-1.0"})
            if save_image:
                JREAD.draw_tree(t, "res/img/tree_" + site + str(len(RESULTS[site]['snapshots'])) + ".png")

            # Print Deets 
            qprint("Completed scraping " + site + " in " + str(tot) + " seconds")
    return 0

def main(argv):
    global OFNAME, QUIET

    # Get command line args:
    # -i: import a previous crawl
    # -o: export current crawl
    # -l: import list file
    # -q: toggle quiet mode (no qprint statements)
    # -h: help

    prev_crawl = ["res/crawl.json"]
    list_name  = "sites.json"

    breakpoint()
    try: 
        opts, args = OPT.getopt(argv, "qhi:o:l:", [])
    except OPT.GetoptError:
        qprint("usage: " + argv[0] + "-i <previous crawl> -o <export name> -l <url list>")
        return 2
    for opt, arg in opts:
        if opt == '-h':
            qprint("usage: " + argv[0] + "-i <previous crawl> -o <export name> -l <url list>")
            qprint("also : -q (toggle quiet mode) -h (help)")
            return 0
        elif opt == '-i':
            prev_crawl.insert(0, arg)
        elif opt == '-o':
            OFNAME = arg
        elif opt == '-l':
            list_name = arg
        elif opt == '-q':
            QUIET = not QUIET

    # Open the sites list json file
    if not os.path.exists(list_name):
        qprint("File " + list_name + "does not exist")
        return 1
    with open(list_name, "r") as fi:
        sites = JSON.loads(fi.read())
    # If the res directory is not set up
    if not os.path.isdir("res"):
        qprint("Creating results directory: ./res/")
        os.mkdir("res")
    if not os.path.isdir("res/img"):
        os.mkdir("res/img")

    # Try to restore an old run
    restore = None
    for run in prev_crawl:
        if os.path.exists(run):
            restore = run
            break
    return crawl(sites, True, restore)

# main function call
if __name__ == "__main__":
    try:
        ret = main(sys.argv)
        sys.exit(ret)
    except KeyboardInterrupt:
        qprint("Interrupted")
        # Kill the subprocess
        if SUBP != None:
            os.system("rm -rf *.snp")
            os.kill(SUBP.pid, signal.SIGTERM)
        # Save the results dictionary
        if RESULTS != None:
            with open(OFNAME, 'w') as fi:
                JSON.dump(RESULTS, fi)
