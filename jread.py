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
from adblockparser import AdblockRules as ABR

TREE_PARSER = None
RULES       = None
RULES_FILE  = "easylist.json"
VT_ATTR     = {"apk_file": "vt.key", "req_url": "https://www.virustotal.com/vtapi/v2/url/report"}
FORMAT      = "backreferenced-1.2"

FILE        = "../../../lifestyle.bg.d.csv"

# tree regex string:
# since the output from Zbrowse has been configured to be:
# c:<child_url>
# p:<parent_url>
# ...
# 
# we will make a regex who captures the child url & the parent url
# it will look for "c:" and then pature whatever comes before the \n
# it will then look for "p:" and pature anything till newline or EOF
tree_string = r"c:(.+)\np:(.+)\nn:({.*})"

def get_format():
    return FORMAT

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
    rad  = 200
    bufx = 100
    bufy = 300
    thck = 10

    # get the image size
    size = (bufx + w*(bufx+(2*rad)), bufy + h*(bufy+(2*rad)))

    # create a new image
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size[0], size[1])
    ctx     = cairo.Context     (surface)
    ctx.set_source_rgba(1, 1, 1, 1)
    ctx.rectange(0,0,size[0], size[1])
    ctx.fill()

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
                color = (255, 20, 50)
            elif tree[level][item]["ad"] == "no":
                color = (50, 20, 255)
            else:
                color = (255, 20, 200)


            # since we are iterating "horizontally", we
            # need only update the x position
            cx  = c0x + structure[level][item]*(2*rad + bufx)
            
            # draw ecntered text
            sitesize = draw.textsize(get_url(item), font=fnt)
            vttxt    = str(tree[level][item]["vt"])
            vtssize  = draw.textsize(vttxt, font=fnt)

            # draw the circle + text
            #draw.ellipse([cx-rad, cy-rad, cx+rad, cy+rad], color, color)
            #draw.text([cx-sitesize[0]/2, cy-sitesize[1]], get_url(item),  font=fnt, fill=(0,0,0))
            #draw.text([cx-vtssize[0]/2 , cy+vtssize [1]], vttxt, font=fnt, fill=(0,0,0))
            ctx.set_source_rgba(color[0], color[1], color[2], 1.0)
            ctx.arc(cx, cy, rad, 0, 2*math.pi)
            ctx.fill()
            ctx.set_source_rgba(0, 0, 0, 1.0)
            
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
                    draw.line([(cx+offx, cy-rad), (cx+offx, cy-rad-offy-thck/2)], (0,0,0),thck)
                    draw.line([(cx+offx, cy-rad-offy), (cpx, cy-rad-offy)], (0,0,0), thck)
                    draw.line([(cpx, cy-rad-offy+thck/2), (cpx, cpy+rad)], (0,0,0), thck)

                    thisp += 1

        # remember the parent level and center
        # of the circle at the beginning of the parent level
        plev = level
        c0xp = c0x
        c0yp = cy

    # delete the drawing object
    del draw
    # save the image
    img.save(outname, "PNG")

def get_tree(s):
    # save a regex for parsing the tree
    global TREE_PARSER, RULES
    if TREE_PARSER == None:
        TREE_PARSER = re.compile(tree_string)
    if RULES == None:
        with open(RULES_FILE, "r") as fi:
            RULES = ABR(json.loads(fi.read()))

    # init an empty tree
    tree    = [{}]
    nodes   = {}
    matches = TREE_PARSER.findall(s)
    # iterate through the matches and 
    # bild the tree
    for match in matches:
        c_url = match[0]
        p_url = match[1]
        r_url = "nil"
        j     = json.loads(match[2])
        if "request" in j and "request" in j["request"]:
            if "headers" in j["request"]["request"]:
                if "Referer" in j["request"]["request"]["headers"]:
                    r_url = j["request"]["request"]["headers"]["Referer"]
        

        add_branch(tree, nodes, p_url, r_url)
        add_branch(tree, nodes, r_url, c_url)

    for l in range(1, len(tree)):
        for n in tree[l].keys():
            if tree[l][n]["ad"] == "yes":
                continue
            for p in tree[l][n]["parents"].keys():
                if tree[l-1][p]["ad"] != "no":
                    tree[l][n]["ad"] = "inherited"
                    break

    return tree

def add_branch(tree, nodes, parent, child):
    global RULES

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
        if RULES.should_block(parent):
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
        if RULES.should_block(child):
            tree[layer+1][child]["ad"] = "yes"

def get_vtscore(url):
    global VT_ATTR

    if not "apk" in VT_ATTR:
        with open(VT_ATTR["apk_file"], "r") as fi:
            VT_ATTR.update({"apk": fi.read()})
    if not "params" in VT_ATTR:
        VT_ATTR.update({"params": {"apikey": VT_ATTR["apk"], "resource": None}})

    VT_ATTR["params"]["resource"] = url

    response = requests.get(VT_ATTR["req_url"], params=VT_ATTR["params"])
    try:
        js = response.json()
        return js["positives"]
    except (json.decoder.JSONDecodeError, KeyError):
        return 0

# eof #
