# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# crawler.py  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Created by: Jordan Bonecutter for HPCForge  # # # # # # # # # # # # # #
# 28 June 2019  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import json     as JSON
import jread    as JREAD
import snapshot as SNAPS

def crawl(sites):
    # Forever while loop
    while True:
        # Iterate through all sites in
        # the given list
        for site in sites.keys():
            # Use ZBrowse to get a snap
            # of the sites
            s = SNAPS.snap(site)

            # Extract the tree
            t = JREAD.get_tree(s)

            # Save it to a file
            f = open("sites/" + site + "[" + str(sites[site]) + "].json", "w")
            JSON.dump(t, f)
            f.close()
            sites[site] += 1

def main():
    SITES = {"yahoo.com": 0, "forbes": 0, "bbc.com": 0}
    crawl(SITES)

# main function call
if __name__ == "__main__":
    main()
