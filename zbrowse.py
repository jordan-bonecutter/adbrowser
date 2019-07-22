# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# zbrowse.py  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Created by: Jordan Bonecutter for HPCForge  # # # # # # # # # # # # # #
# 15 July 2019  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import subprocess as sub
import os
import re
import json
import signal
import _pickle as pickle

class ZBrowse:
    _chromium = None
    path      = None
    proc      = None
    port      = 9222
    timeout   = 30
    stdo_name = "tmp/zbrowse_sout.snp"
    stde_name = "tmp/zbrowse_serr.snp"
    _stdo     = None
    _stde     = None
    _err_regx = None
    _ctrace   = "res/traces.json"
    pklpath   = "pickles/"

    def __init__(self, path, port, chromium_path, stdo_name, stde_name, chrometrace_name):
        self.path  = path
        self._chromium = Chromium(chromium_path, port, "tmp/chromium_out.snp", "tmp/chromium_err.snp", 0)
        if port != None:
            self.port = port
        if stdo_name != None:
            self.stdo_name = stdo_name
        if stde_name != None:
            self.stde_name = stde_name
        if chrometrace_name != None:
            self._ctrace = chrometrace_name
        if os.path.exists(self.pklpath+"zbrowse_err_regx.pkl"):
            with open(self.pklpath+"zbrowse_err_regx.pkl", "rb") as fi:
                self._err_regx = pickle.load(fi)
        else:
            self._err_regx = re.compile(r"heap out of memory")
            with open(self.pklpath+"zbrowse_err_regx.pkl", "wb") as fi:
                pickle.dump(self._err_regx, fi, -1)

    def run(self, url, timeout):
        self._chromium.start()
        tree = {}

        self._stdo = open(self.stdo_name, "w")
        self._stde = open(self.stde_name, "w")
        zopts = ("node", self.path, url, str(self.port))
        self.proc  = sub.Popen(args=zopts, stdout=self._stdo, stderr=self._stde)

        try:
            # Wait
            self.proc.wait(timeout)
            self.proc.kill()
            self._chromium.kill(True, True)
            # Close the files so they save
            self._stdo.close()
            self._stde.close()
            # Check stderr for an error message
            with open(self.stde_name, "r") as stderr_fi:
                stderr_msg = self._err_regx.search(stderr_fi.read())
            # If there was an out of memory error
            if stderr_msg == None:
                # Reopen it 
                # TODO: Find a better way to do this
                # than closing & reopening a file
                with open(self.stdo_name, "r") as stdout_fi:
                    # Read it
                    s = stdout_fi.read()
                    try:
                        tree = json.loads(s)
                    except json.decoder.JSONDecodeError:
                        tree = {}
            # Remove it
            os.system("rm -f "+self.stdo_name)
            os.system("rm -f "+self.stde_name)
            self.proc      = None
        except sub.TimeoutExpired:
            # If we timed out, kill the subproc
            self.proc.kill()
            self._chromium.kill(True, True)
            self.proc      = None
            # Return an empty dictionary
            tree = {}
            # Close redirected stdout
            self._stdo.close()
            self._stde.close()
            # Remove temp file
            os.system("rm -f "+self.stdo_name)
            os.system("rm -f "+self.stde_name)

        # wait for chrome to save the trace
        if not os.path.exists("chrometrace.log"):
            return tree

        # try to decode it
        with open("chrometrace.log", "r") as fi:
            try:
                traces = json.loads(fi.read())
            except json.JSONDecodeError:
                traces = {"traceEvents": []}

        # if the trace doesn't exist, then create it
        if not os.path.exists(self._ctrace):
            with open(self._ctrace, "w") as fi:
                json.dump(traces, fi)

        else:
            with open(self._ctrace, "r") as fi:
                traces["traceEvents"] += json.loads(fi.read())["traceEvents"]
            with open(self._ctrace, "w") as fi:
                json.dump(traces, fi)

        os.system("rm -f chrometrace.log")
        return tree

    def stop(self):
        self._chromium.kill(True, True)
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

    def start(self):
        tst = "--trace-config-file"
        rdp = "--remote-debugging-port="+str(self.port)
        cc  = "--disk-cache-size="+str(self._maxc)
        gc  = "--disable-gpu-program-cache"
        mc  = "--media-cache-size="+str(self._maxc)
        cd  = "--aggressive-cache-discard"
        sc  = "--disable-gpu-shader-disk-cache"

        copts = (self.path, "--headless", tst, rdp, cc, gc, mc, cd, sc)
        self._sout = open(self._sost, "w")
        self._serr = open(self._sest, "w")
        self.proc = sub.Popen(args=copts, stdout=self._sout, stderr=self._serr)

    def kill(self, rm_sout, rm_serr):
        if self.proc != None:
            os.kill(self.proc.pid, signal.SIGTERM)
            self._sout.close()
            self._serr.close()
        if rm_sout:
            os.system("rm -f "+self._sost)
        if rm_serr:
            os.system("rm -f "+self._sest)
