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
node_version = "fulltree_backreferenced1.2, trimtree-backreferenced1.0"

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
    typecolors = {"": (150, 150, 150), "Other": (150, 150, 150), "unknown": (150, 150, 150)}
    typecolors.update({"Image": (230, 230, 20)})
    typecolors.update({"Stylesheet": (20, 230, 100)})
    typecolors.update({"Script": (255, 20, 20)})
    typecolors.update({"EventSource": (20, 230, 100)})
    typecolors.update({"Font": (20, 230, 100)})
    typecolors.update({"Media": (255, 20, 20)})
    typecolors.update({"Fetch": (230, 230, 20)})
    typecolors.update({"Document": (230, 230, 20)})
    typecolors.update({"XHR": (230, 230, 20)})

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
            size = (bufx + w*(bufx+(2*rad)), bufy + h*(bufy+(2*rad)))
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size[0], size[1])
            break
        except cairo.Error:
            rad   = int(rad/2)
            bufx  = int(bufx/2)
            bufy  = int(bufy/2)
            thck  = int(thck/2)
            tsize = int(tsize/2)
            tbuf  = int(tbuf/2)

    ctx     = cairo.Context(surface)
    ctx.set_source_rgb(1, 1, 1)
    ctx.rectangle(0,0,size[0], size[1])
    ctx.fill()

    fnt = cairo.ToyFontFace("Menlo", cairo.FontSlant.NORMAL, cairo.FontWeight.NORMAL)
    opt = cairo.FontOptions()
    fnt = cairo.ScaledFont(fnt, cairo.Matrix(size[0]/60,0,0,size[0]/60,0,0),cairo.Matrix(1,0,0,1,0,0), opt)
    ctx.set_scaled_font(fnt)
    nnt = str(num_nodes(tree))
    net = str(num_ad_nodes(tree, True))
    nit = str(num_ad_nodes(tree, False))
    inf = str(nnt+","+net+","+nit)
    ext = fnt.text_extents(inf)
    ctx.move_to(0, ext.height)

    ctx.set_source_rgb(50/255,20/255,255/255)
    ctx.show_text(nnt)
    ctx.set_source_rgb(0,0,0)
    ctx.show_text(",")
    ctx.set_source_rgb(255/255,20/255,50/255)
    ctx.show_text(net)
    ctx.set_source_rgb(0,0,0)
    ctx.show_text(",")
    ctx.set_source_rgb(255/255,20/255,200/255)
    ctx.show_text(nit)
    ctx.stroke()

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
            
            # draw centered text
            try:
                sqtxt = str(tree[level][item]["squish"])
            except KeyError:
                sqtxt = ""

            # draw the circle + text
            ctx.set_source_rgb(color[0], color[1], color[2])
            ctx.arc(cx, cy, rad, 0, 2*math.pi)
            ctx.fill()

            if "types" in tree[level][item]:
                ntypes = len(tree[level][item]["types"])
                for idt, t in enumerate(tree[level][item]["types"]):
                    try:
                        color = typecolors[t]
                    except KeyError:
                        print(t)
                        color = typecolors[""]
                    ctx.set_source_rgb(color[0]/255, color[1]/255, color[2]/255)
                    ctx.arc(cx, cy, rad, idt*2*math.pi/ntypes, (idt+1)*2*math.pi/ntypes)
                    ctx.stroke()

            elif "type" in tree[level][item]:
                try:
                    color = typecolors[tree[level][item]["type"]]
                except:
                    print(tree[level][item]["type"])
                    color = typecolors[""]
                ctx.set_source_rgb(color[0]/255, color[1]/255, color[2]/255)
                ctx.arc(cx, cy, rad, 0, 2*math.pi)
                ctx.stroke()

            ctx.set_source_rgba(0, 0, 0, 1.0)

            ext = fnt.text_extents(get_url(item))
            ctx.move_to(cx-ext.width/2, cy-tbuf)
            ctx.show_text(get_url(item))

            ext = fnt.text_extents(sqtxt)
            ctx.move_to(cx-ext.width/2, cy+ext.height + tbuf)
            ctx.show_text(sqtxt)
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
                    offy = int((puni[parent]+2)*bufy/(plsize+3))
                    ofrx = int((thck*(thisptot-1)) + (2*thck*(thisptot-1)))
                    of0x = int(-ofrx/2)
                    offx = int(of0x + thisp*ofrx/thisptot)
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

def traverse_tree(base, root, tree, nodes):
    global _rules
    pid = root["parent"]
    cid = root["data"]
    if get_url(pid) == "nil" or get_url(cid) == "nil":
        return

    # try to find the parent
    try:
        par_l = nodes[pid]
    except KeyError:
        tree[0].update({pid: {"parents": {None:0}, "ad": "no", "vt": 0, "type": "", "frameId": 0}})
        if _rules.should_block(pid):
            tree[0][pid]["ad"] = "yes"
        nodes.update({pid: 0})
        par_l = 0

    if len(tree) == par_l+1:
        tree.append({})

    # try to find the child
    try:
        child_node = tree[par_l+1][cid]
        child_node["parents"].update({pid: 1})
    except KeyError:
        tree[par_l+1].update({cid: {"parents": {pid: 1}, "ad": "no", "vt": 0, "type": "", "frameId": 0}})
        if _rules.should_block(cid):
            tree[par_l+1][cid]["ad"] = "yes"
        try: 
            tree[par_l+1][cid]["type"]    = root["networkData"]["request"]["type"]
            tree[par_l+1][cid]["frameId"] = root["networkData"]["request"]["frameId"]
        except KeyError:
            tree[par_l+1][cid]["type"] = "unknown"
            tree[par_l+1][cid]["frameId"] = -1
        nodes.update({cid: par_l+1})

    for child in root["children"]:
        traverse_tree(base, child, tree, nodes)

def get_tree(root):
    global _rules
    if _rules == None:
        if os.path.exists(_rules_pkl):
            with open(_rules_pkl, "rb") as fi:
                _rules = pickle.load(fi)
        else:
            with open(_rules_file, "r") as fi:
                _rules = json.loads(fi.read())
            with open(_rules_pkl, "wb") as fi:
                pickle.dump(_rules, fi, -1)

    tree  = [{}]
    nodes = {}
    for child in root["_root"]["children"]:
        traverse_tree(root["_root"], child, tree, nodes)

    for idl, layer in enumerate(tree[1:]):
        for url, node in layer.items():
            if node["ad"] == "yes":
                continue
            for parent in node["parents"].keys():
                if tree[idl][parent]["ad"] != "no":
                    node["ad"] = "inherited"
                    break

    return {"tree_full": tree, "tree_trimmed": trim_tree(tree)}

def trim_tree(tree):
    trim = []
    for idl, level in enumerate(tree):
        trim.append({})
        for name, info in level.items():
            alias = get_url(name)
            try:
                trim[idl][alias]["squish"] += 1
                try:
                    trim[idl][alias]["types"][info["type"]] += 1
                except KeyError:
                    trim[idl][alias]["types"].update({info["type"]: 1})
                if trim[idl][alias]["ad"] == "no" and info["ad"] != "no":
                    trim[idl][alias]["ad"] = info["ad"]
                elif trim[idl][alias]["ad"] != "yes" and info["ad"] == "yes":
                    trim[idl][alias]["ad"] = "yes"
            except KeyError:
                trim[idl].update({alias: {"parents": {}, "ad": "no", "squish": 1, "vt": 0, "types": {}}})
                try:
                    trim[idl][alias]["types"][info["type"]] += 1
                except KeyError:
                    trim[idl][alias]["types"].update({info["type"]: 1})
                trim[idl][alias]["ad"] = info["ad"]
            for parent in info["parents"]:
                palias = get_url(parent)
                try:
                    trim[idl][alias]["parents"][palias] += 1
                except KeyError:
                    trim[idl][alias]["parents"].update({palias: 1})

    return trim

def num_ad_nodes(tree, explicit):
    ret = 0
    for layer in tree:
        for url, data in layer.items():
            if explicit:
                if data["ad"] == "yes":
                    ret += 1
            else:
                if data["ad"] != "no":
                    ret += 1
    return ret

def num_nodes(tree):
    ret = 0
    for layer in tree:
        ret += len(layer)

    return ret

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
