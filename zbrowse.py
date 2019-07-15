# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# zbrowse.py  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Created by: Jordan Bonecutter for HPCForge  # # # # # # # # # # # # # #
# 15 July 2019  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import subprocess as sub
import os
import re
import json

class ZBrowse:
    _chromium = None
    path      = None
    proc      = None
    port      = 9222
    timeout   = 30
    stdo_name = "zbrowse_sout.snp"
    stde_name = "zbrowse_serr.snp"
    _stdo     = None
    _stde     = None
    _err_regx = None
    _err_rstr = r"heap out of memory"
    _ctrace   = "res/traces.json"

    def __init__(self, path, port, chromium_path, stdo_name, stde_name, chrometrace_name):
        self.path  = path
        self._chromium = Chromium(chromium_path, port, "chromium_out.snp", "chromium_err.snp", 0)
        if port != None:
            self.port = port
        if stdo_name != None:
            self.stdo_name = stdo_name
        if stde_name != None:
            self.stde_name = stde_name
        if chrometrace_name != None:
            self._ctrace = chrometrace_name

    def run(self, url, timeout):
        self._chromium.start(timeout)

        self._stdo = open(self.stdo_name, "w")
        self._stde = open(self.stde_name, "w")
        zopts = ("node", self.path, url)
        self.proc  = sub.Popen(args=zopts, stdout=self._stdo, stderr=self._stde)

        try:
            # Wait
            self.proc.wait(timeout)
            self.proc.kill()
            self._chromium.kill(True, True, True)
            # Close the files so they save
            self._stdo.close()
            self._stde.close()
            # Check stderr for an error message
            with open(self.stde_name, "r") as stderr_fi:
                if self._err_regx == None:
                    self._err_regx = re.compile(self._err_rstr)
                stderr_msg = self._err_regx.search(stderr_fi.read())
            # If there was an out of memory error
            if stderr_msg != None:
                # Set the tree to empty
                tree = {}
            # Otherwise if the run was succesful
            else:
                # Reopen it 
                # TODO: Find a better way to do this
                # than closing & reopening a file
                with open(self.stdo_name, "r") as stdout_fi:
                    # Read it
                    tree = json.loads(stdout_fi.read())
            # Remove it
            os.system("rm -f "+self.stdo_name)
            os.system("rm -f "+self.stde_name)
            self.proc      = None
        except sub.TimeoutExpired:
            # If we timed out, kill the subproc
            self.proc.kill()
            self._chromium.kill(True, True, True)
            self.proc      = None
            # Return an empty dictionary
            tree = {}
            # Close redirected stdout
            self._stdo.close()
            self._stde.close()
            # Remove temp file
            os.system("rm -f "+self.stdo_name)
            os.system("rm -f "+self.stde_name)

        while not os.path.exists("chrometrace.log"):
            continue
        try:
            with open("chrometrace.log", "r") as fi:
                curr = json.loads(fi.read())
            if not os.path.exists(self._ctrace):
                with open(self._ctrace, "w") as fi:
                    json.dump({"traceEvents":[]}, fi)
            with open(self._ctrace, "r") as fi:
                prev = json.loads(fi.read())
                prev["traceEvents"] = prev["traceEvents"] + curr["traceEvents"]
            with open(self._ctrace, "w") as fi:
                json.dump(prev, fi)
        except json.JSONDecodeError:
            os.system("rm -f chrometrace.log")
            return tree
        os.system("rm -f chrometrace.log")

        return tree

    def stop(self):
        self._chromium.kill(True, True, True)
        if self.proc:
            self.proc.kill()
            self._stdo.close()
            self._stde.close()
            os.system("rm -f "+self.stdo_name)
            os.system("rm -f "+self.stde_name)

class Chromium:
    path  = None
    proc  = None
    port  = 9222
    _maxc = 0
    _sout = None
    _serr = None
    _sost = "chromium_out.snp"
    _sest = "chromium_err.snp"

    def __init__(self, path, port, stdo_fname, stde_fname, cache_size):
        self.path = path
        if port != None:
            self.port = port
        if stdo_fname != None:
            self._sost = stdo_fname
        if stde_fname != None:
            self._sest = stde_fname
        if cache_size != None:
            self._maxc = cache_size

    def start(self, startup_timeout):
        t0 = startup_timeout
        if t0 == None:
            t0 = 30
        tst = "--trace-startup"
        rdp = "--remote-debugging-port="+str(self.port)
        cc  = "--disk-cache-size="+str(self._maxc)
        gc  = "--disable-gpu-program-cache"
        mc  = "--media-cache-size="+str(self._maxc)
        cd  = "--aggressive-cache-discard"
        sc  = "--disable-gpu-shader-disk-cache"

        copts = (self.path, "--headless", tst, tst+"-duration="+str(t0), rdp, cc, gc, mc, cd, sc)
        self._sout = open(self._sost, "w")
        self._serr = open(self._sest, "w")
        self.proc = sub.Popen(args=copts, stdout=self._sout, stderr=self._serr)

    def kill(self, rm_sout, rm_serr, clr_cache):
        if self.proc:
            self.proc.kill()
            self._sout.close()
            self._serr.close()
        if rm_sout:
            os.system("rm -f "+self._sost)
        if rm_serr:
            os.system("rm -f "+self._sest)
