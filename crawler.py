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

RUN          = 0

def snap(url, timeout):
    global REGEX, magic_string, RUN

    # Clear browser cache
    # I know, I know... this is really hideous
    # This wouldn't work unless I cleared the files
    # that start with a hex digit so this is the best
    # got. TODO: make this better (?)
    c_loc = "/Users/jordanbonecutter/Library/Caches/Google/Chrome\ Canary/Default/"
    os.system("rm -rf " + c_loc + "Cache/0*") 
    os.system("rm -rf " + c_loc + "Cache/1*") 
    os.system("rm -rf " + c_loc + "Cache/2*") 
    os.system("rm -rf " + c_loc + "Cache/3*") 
    os.system("rm -rf " + c_loc + "Cache/4*") 
    os.system("rm -rf " + c_loc + "Cache/5*") 
    os.system("rm -rf " + c_loc + "Cache/6*") 
    os.system("rm -rf " + c_loc + "Cache/7*") 
    os.system("rm -rf " + c_loc + "Cache/8*") 
    os.system("rm -rf " + c_loc + "Cache/9*") 
    os.system("rm -rf " + c_loc + "Cache/a*") 
    os.system("rm -rf " + c_loc + "Cache/b*") 
    os.system("rm -rf " + c_loc + "Cache/c*") 
    os.system("rm -rf " + c_loc + "Cache/d*") 
    os.system("rm -rf " + c_loc + "Cache/e*") 
    os.system("rm -rf " + c_loc + "Cache/f*") 
    os.system("rm -rf " + c_loc + "Cache/index")
    os.system("rm -rf " + c_loc + "Cache/index-dir/*")

    os.system("rm -rf " + c_loc + "Code Cache/js/0*") 
    os.system("rm -rf " + c_loc + "Code Cache/js/1*") 
    os.system("rm -rf " + c_loc + "Code Cache/js/2*") 
    os.system("rm -rf " + c_loc + "Code Cache/js/3*") 
    os.system("rm -rf " + c_loc + "Code Cache/js/4*") 
    os.system("rm -rf " + c_loc + "Code Cache/js/5*") 
    os.system("rm -rf " + c_loc + "Code Cache/js/6*") 
    os.system("rm -rf " + c_loc + "Code Cache/js/7*") 
    os.system("rm -rf " + c_loc + "Code Cache/js/8*") 
    os.system("rm -rf " + c_loc + "Code Cache/js/9*") 
    os.system("rm -rf " + c_loc + "Code Cache/js/a*") 
    os.system("rm -rf " + c_loc + "Code Cache/js/b*") 
    os.system("rm -rf " + c_loc + "Code Cache/js/c*") 
    os.system("rm -rf " + c_loc + "Code Cache/js/d*") 
    os.system("rm -rf " + c_loc + "Code Cache/js/e*") 
    os.system("rm -rf " + c_loc + "Code Cache/js/f*") 
    os.system("rm -rf " + c_loc + "Code Cache/js/index")
    os.system("rm -rf " + c_loc + "Code Cache/js/index-dir/*")

    os.system("rm -rf " + c_loc + "Storage/ext/*")

    # Path on my machine to the ZBrowse file
    PATH = "../zbrowse/js/index.js"
    # Use node.js to execute it
    EXEC = "node"
    # Add the http prefix to the url
    PRFX = "https://www."
    # Redirect stdout to a file
    new_sout = open("sout" + str(RUN) + ".snp", "w")
    new_serr = open("serr" + str(RUN) + ".snp", "w")
    RUN += 1
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
        # If there was an out of memory error
        if em != None:
            # Close the error fd
            ec.close()
            # Set the tree to empty
            t = "{}"
            print("JS ran out of memory")
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
            # os.system("rm -r *.snp")
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
        # os.system("rm -r *.snp")
        print("Timeout")
    return t

def crawl(sites):
    # local variables
    t0    = 45

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
            t0    = sites[site][1]
            start = TIME.time()
            s     = snap(site, t0+5)
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
    
            sites[site][1] = t0

            # If for whatever reason the snapshot
            # failed, continue looping
            if s == "{}" or s == None or s == "":
                continue

            # Extract the tree
            t = JREAD.get_tree(s)
            JREAD.draw_tree(t, "./sites/" + site + str(sites[site][0]) + ".png")

            # Save it to a file
            print("Completed scraping " + site + " in " + str(tot) + " seconds")
            f = open("sites/" + site + "[" + str(sites[site][0]) + "].json", "w")
            JSON.dump(t, f)
            f.close()
            sites[site][0] += 1

def main():
    SITES = {"yahoo.com": [0,45], "forbes.com":[0,45], "bbc.com":[0,45], "cnn.com":[0,45]}
    SITES.update({"huffingtonpost.com":[0,45]})
    SITES.update({"nytimes.com":[0,45]})
    SITES.update({"foxnews.com":[0,45]})
    SITES.update({"nbc.com":[0,45]})
    SITES.update({"washingtonpost.com":[0,45]})
    SITES.update({"theguardian.com":[0,45]})
    crawl(SITES)

# main function call
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        if SUBP != None:
            # os.system("rm -rf *.snp")
            os.kill(SUBP.pid, signal.SIGTERM)
