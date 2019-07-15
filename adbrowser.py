# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# adbrowser.py  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Created by: Jordan Bonecutter for HPCForge  # # # # # # # # # # # # # #
# 15 July 2019  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import json
import jread
import time
import datetime
import zbrowse 
import os

class Adbrowser:
    zb      = None
    sites   = None
    outfile = "res/crawl.json"
    restore = None
    results = None

    def __init__(self, sitesfile, outfile, restore, zbpath, cpath):
        with open(sitesfile, "r") as fi:
            self.sites = json.loads(fi.read())
        self.outfile = outfile
        self.restore = restore
        self.zb      = zbrowse.ZBrowse(zbpath, 52849, cpath, None, None, None) 

    @classmethod
    def fromdict(cls, d):
        rs = None
        of = None
        if "outfile" in d:
            of = d["outfile"]
        if "restore" in d:
            rs = d["restore"]
        return cls(d["sitesfile"], of, rs, d["zbrowse_path"], d["chromium_path"])

    @classmethod
    def fromfile(cls, fname):
        with open(fname, "r") as fi:
            js = json.loads(fi.read())
            return cls.fromdict(js)

    def crawl(self, count, should_print, save_image):
        # local variables
        start = 0
        end   = 0
        tot   = 0
    
        # try to open a restore file
        if self.restore != None and os.path.exists(self.restore):
            with open(self.restore, "r") as fi:
                self.results = json.loads(fi.read())
        # if there is no restore file
        # then create a new data structure
        else:
            self.results = {}
        for site in self.sites:
            if site not in self.results:
                self.results.update({site:{"snapshots":[], "timer":45}})

        # Forever while loop
        while count > 0:
            count -= 1
            # Iterate through all sites in
            # the given list
            for site in self.sites:
                # Use ZBrowse to get a snap
                # of the sites
                #
                # We will time the snap so that
                # we can adjust the timeout value
                # accordingly
                t0    = self.results[site]["timer"]
                start = time.time()
                date  = str(datetime.datetime.now())
                tree  = self.zb.run("https://www."+site, t0+5)
                end   = time.time()
                tot   = end-start
                # If we timed out
                if tot >= t0:
                    # Double the timeout value
                    self.results[site]["timer"] *= 2
                    continue
                # If we didn't timeout, use a running
                # contraharmonic mean (chm to emphasize
                # large values, it's better to not timeout
                # than to timeout)
                else:
                    t0 = (((t0*t0)+((tot)*(tot)))/(t0+tot))
                    self.results[site]["timer"] = t0

                # If for whatever reason the snapshot
                # failed, continue looping
                if tree == {}:
                    if should_print:
                        print("Unknown error...")
                    continue

                # Extract the tree
                # tree = jread.get_tree(tree)
                self.results[site]["snapshots"].append({"date":date,"tree":tree,"format":jread.get_format()})
                if save_image:
                    jread.draw_tree(t,"res/img/tree_"+site+str(len(self.results[site]["snapshots"]))+".png")

                # Print Deets 
                if should_print:
                    print("Completed scraping " + site + " in " + str(tot) + " seconds")
        return 0

    def stop(self):
        self.zb.stop()

    def save(self):
        if self.results != None:
            with open(self.outfile, "w") as fi:
                json.dump(self.results, fi)
