# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# jread.py  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Created by: Jordan Bonecutter for HPCForge  # # # # # # # # # # # # # #
# 25 June 2019  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# imports
import json
import re
import cairo
import math
import tldextract
import requests
import csv
import os
import _pickle as pickle
from adblockparser import AdblockRules

_rules       = None
_rules_file  = "easylist.json"
_rules_pkl   = "pickles/rules.pkl"
_vt_attr     = {"apk_file": "vt.key", "req_url": "https://www.virustotal.com/vtapi/v2/url/report"}
node_version= "backreferenced-1.2"

def csv_2_zbrowse(fname):
    # start with an empty string
    s = ""

    # open the specified file
    with open(fname, "r") as fi:
        # read it
        reader = csv.reader(fi)

        # local var
        i = 0
        curr_lev = 0
        prev_lev = 0
        lastparent = []

        #iterate through the rows
        for row in reader:
            i += 1
            # for the first row, we have no previous
            # row so it's a special case
            if i == 1:
                s += "c:"+row[3] + "\n"
                s += "p:nil\n"
                s += "n:{}\n"
                curr_lev = 0
                lastparent.append(row[3])
                continue
            # update level pointers
            prev_lev = curr_lev
            curr_lev = int(row[2])

            # if the curent level is greater than the
            # previous level, it means this node is a child
            if curr_lev > prev_lev:
                # child
                if len(lastparent) < curr_lev+1:
                    lastparent.append(row[3])
                else:
                    lastparent[curr_lev] = row[3]
                s += "c:"+row[3] + "\n"
                s += "p:"+lastparent[curr_lev-1] + "\n"
                s += "n:{}\n"
            # if the current level is at the same as 
            # the previous node, it means that we are
            # still adding to the node on the previous level
            elif curr_lev == prev_lev:
                # child of prev parent
                s += "c:"+row[3]+"\n"
                s += "p:"+lastparent[curr_lev-1]+"\n"
                s += "n:{}\n"
                lastparent[curr_lev] = row[3]
            # only other choice is that we are going up levels
            else:
                # going back to other level
                s += "c:"+row[3]+"\n"
                s += "p:"+lastparent[curr_lev-1]+"\n"
                s += "n:{}\n"
                lastparent[curr_lev] = row[3]
    return s

def get_url(url):
    if url == None:
        return "nil"

    # use tldextract to get the domain
    ext = tldextract.extract(url)

    # if it couldn't find anything
    if ext.domain == "" or ext.suffix == "":
        return "nil"
    else:
        return ".".join((ext.domain, ext.suffix))

def draw_tree(tree, outname):
    # get the layout of the tree
    structure = [{} for _ in range(len(tree))]
    i = 0
    for level in tree:
        j = 0
        curr = structure[i]
        for key in level.keys():
            curr.update({key:j})
            j += 1
        i += 1

    # get the height and max width
    # of the tree
    h = len(structure)
    w = 0
    for level in structure:
        if len(level) > w:
            w = len(level)

    # picture parameters
    rad   = 200
    bufx  = 100
    bufy  = 300
    thck  = 10
    tsize = 50
    tbuf  = 6

    # create a new image
    while True:
        try:
            # get the image size
            size = (int(bufx + w*(bufx+(2*rad))), int(bufy + h*(bufy+(2*rad))))
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size[0], size[1])
            break
        except cairo.Error:
            rad   /= 2
            bufx  /= 2
            bufy  /= 2
            thck  /= 2
            tsize /= 2
            tbuf  /= 2

    ctx     = cairo.Context(surface)
    ctx.set_source_rgb(1, 1, 1)
    ctx.rectangle(0,0,size[0], size[1])
    ctx.fill()
    fnt = cairo.ToyFontFace("Menlo", cairo.FontSlant.NORMAL, cairo.FontWeight.NORMAL)
    opt = cairo.FontOptions()
    fnt = cairo.ScaledFont(fnt, cairo.Matrix(tsize, 0, 0, tsize, 0, 0), cairo.Matrix(1, 0, 0, 1, 0, 0), opt)
    ctx.set_scaled_font(fnt)
    ctx.set_line_cap (cairo.LineCap.BUTT)
    ctx.set_line_join(cairo.LineJoin.ROUND)
    ctx.set_line_width(thck)

    # draw!
    plev = -1
    c0xp = 0
    c0yp = 0
    slen = len(structure)
    # iterate through the levels of the tree
    for level in range (0, len(structure)):
        # get the width of the current level
        llen = len(structure[level])

        # find the x center coordinate
        ctr = size[0]/2
        rng = llen*(2*rad) + (llen-1)*bufx
        c0x = ctr - (rng/2) + rad

        # find the y center coordinate
        ctr = size[1]/2
        rng = slen*(2*rad) + (slen-1)*bufy
        c0y = ctr - (rng/2) + rad
        cy  = c0y + level*(2*rad + bufy)

        # calculate number of unique parents
        puni = {}
        index = 0
        for child in tree[level]:
            for parent in tree[level][child]["parents"]:
                if parent not in puni:
                    puni.update({parent: index})
                    index += 1

        for item in structure[level].keys():
            if tree[level][item]["ad"] == "yes":
                color = (255/255, 20/255, 50/255)
            elif tree[level][item]["ad"] == "no":
                color = (50/255, 20/255, 255/255)
            else:
                color = (255/255, 20/255, 200/255)


            # since we are iterating "horizontally", we
            # need only update the x position
            cx  = c0x + structure[level][item]*(2*rad + bufx)
            
            # draw ecntered text
            vttxt    = str(tree[level][item]["vt"])

            # draw the circle + text
            ctx.set_source_rgb(color[0], color[1], color[2])
            ctx.arc(cx, cy, rad, 0, 2*math.pi)
            ctx.fill()
            ctx.set_source_rgba(0, 0, 0, 1.0)

            ext = fnt.text_extents(get_url(item))
            ctx.move_to(cx-ext.width/2, cy-tbuf)
            ctx.show_text(get_url(item))

            ext = fnt.text_extents(vttxt)
            ctx.move_to(cx-ext.width/2, cy+ext.height + tbuf)
            ctx.show_text(vttxt)
            ctx.stroke()
            
            # if we aren't at the top level then
            # draw a line connecting it to its parent(s)
            if plev != -1:
                thisp    = 0
                thisptot = len(tree[level][item]["parents"])
                # iterate through parents
                for parent in tree[level][item]["parents"].keys():

                    # get the index of the parent
                    pindex = structure[level-1][parent]
                    cpx    = c0xp + (pindex)*(2*rad + bufx)
                    cpy    = c0yp
                
                    # get the width of the parent layer
                    plsize = len(puni)
                    # calculate on offset so that lines dont intersect
                    offy = (puni[parent]+2)*bufy/(plsize+3)
                    ofrx = (thck*(thisptot-1)) + (2*thck*(thisptot-1)) 
                    of0x = -ofrx/2
                    offx = of0x + thisp*ofrx/thisptot
                    # draw 3 lines to connect the parent and child
                    ctx.move_to(cx+offx, cy-rad)
                    ctx.line_to(cx+offx, cy-rad-offy)
                    ctx.line_to(cpx    , cy-rad-offy)
                    ctx.line_to(cpx    , cpy+rad)
                    ctx.stroke()

                    thisp += 1

        # remember the parent level and center
        # of the circle at the beginning of the parent level
        plev = level
        c0xp = c0x
        c0yp = cy

    # save the image
    surface.write_to_png(outname)

def get_tree(root):
    # save a regex for parsing the tree
    global _rules
    if _rules == None:
        if os.path.exists(_rules_pkl):
            with open(_rules_pkl, "rb") as fi:
                _rules = pickle.load(fi)
        else:
            with open(_rules_file, "r") as fi:
                _rules = AdblockRules(json.loads(fi.read()))
            with open(_rules_pkl, "wb") as fi:
                pickle.dump(_rules, fi, -1)

    # init an empty tree
    tree    = [{}]
    nodes   = {}

    tree_traverse(tree, nodes, root["_root"])

    for l in range(1, len(tree)):
        for n in tree[l].keys():
            if tree[l][n]["ad"] == "yes":
                continue
            for p in tree[l][n]["parents"].keys():
                if tree[l-1][p]["ad"] != "no":
                    tree[l][n]["ad"] = "inherited"
                    break

    return tree

def tree_traverse(tree, nodes, root):
    c_url = root["data"]
    p_url = root["parent"]
    try:
        r_url = root["networkData"]["request"]["request"]["headers"]["Referer"]
        add_branch(tree, nodes, p_url, r_url)
        add_branch(tree, nodes, r_url, c_url)
    except KeyError:
        add_branch(tree, nodes, p_url, c_url)

    if "children" in root:
        for child in root["children"]:
            tree_traverse(tree, nodes, child)

def add_branch(tree, nodes, parent, child):
    global _rules

    c_url = get_url(child)
    p_url = get_url(parent)
    if p_url == "nil" or c_url == "nil":
        return

    # search for parent
    #
    # if the parent is not in the tree
    if not parent in nodes:
        layer = 0
        tree[0].update({parent: {"ad": "no", "vt": 0, "parents": {}}})
        nodes.update({parent: 0})
        if _rules.should_block(parent):
            tree[0][parent]["ad"] = "yes"
    # if the parent is in the tree
    else:
        layer = nodes[parent]

    # make sure the tree is big enough
    if len(tree) == layer+1:
        tree.append({})

    # if the child is already in the tree
    if child in tree[layer+1]:
        if not parent in tree[layer+1][child]["parents"]:
            tree[layer+1][child]["parents"].update({parent: 1})
        else:
            tree[layer+1][child]["parents"][parent] += 1

    # if the child is not yet in the tree
    else:
        tree[layer+1].update({child: {"ad": "no", "vt": 0, "parents": {parent: 1}}})
        nodes.update({child: layer+1})
        if _rules.should_block(child):
            tree[layer+1][child]["ad"] = "yes"

def trim_tree(tree):
    trim  = [{}]
    nodes = {}
    names = []
    index = 0
    
    trim[0].update({0: tree[0]})
    nodes.update({list(tree[0].keys())[0]: index})
    names.append(list(tree[0].keys())[0])
    index += 1
    # go through each level of the tree
    for lev in tree[1:]:
        # fo thru each url in that level
        for url in lev.keys():
            # if the url is not in the tree
            if not url in nodes:
                # then we need to add it
                return 0
    return 0
                 

def get_vtscore(url):
    global _vt_attr

    if not "apk" in _vt_attr:
        with open(_vt_attr["apk_file"], "r") as fi:
            _vt_attr.update({"apk": fi.read()})
    if not "params" in _vt_attr:
        _vt_attr.update({"params": {"apikey": _vt_attr["apk"], "resource": None}})

    _vt_attr["params"]["resource"] = url

    response = requests.get(_vt_attr["req_url"], params=_vt_attr["params"])
    try:
        js = response.json()
        return js["positives"]
    except (json.decoder.JSONDecodeError, KeyError):
        return 0

# eof #
