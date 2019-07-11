# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# jread.py  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Created by: Jordan Bonecutter for HPCForge  # # # # # # # # # # # # # #
# 25 June 2019  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# imports
import json
import re
import PIL
import tldextract
import requests
import csv
from adblockparser import AdblockRules as ABR
from PIL           import Image        as IMG
from PIL           import ImageDraw    as IMD
from PIL           import ImageFont    as IMF

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
    s = ""
    with open(fname, "r") as fi:
        reader = csv.reader(fi)
        i = 0
        curr_lev = 0
        prev_lev = 0
        lastparent = []
        for row in reader:
            i += 1
            if i == 1:
                s += "c:"+row[3] + "\n"
                s += "p:nil\n"
                s += "n:{}\n"
                curr_lev = 0
                lastparent.append(row[3])
                continue
            prev_lev = curr_lev
            curr_lev = int(row[2])
            if curr_lev > prev_lev:
                # child
                if len(lastparent) < curr_lev+1:
                    lastparent.append(row[3])
                else:
                    lastparent[curr_lev] = row[3]
                s += "c:"+row[3] + "\n"
                s += "p:"+lastparent[curr_lev-1] + "\n"
                s += "n:{}\n"
            elif curr_lev == prev_lev:
                # child of prev parent
                s += "c:"+row[3]+"\n"
                s += "p:"+lastparent[curr_lev-1]+"\n"
                s += "n:{}\n"
                lastparent[curr_lev] = row[3]
            else:
                # going back to other level
                s += "c:"+row[3]+"\n"
                s += "p:"+lastparent[curr_lev-1]+"\n"
                s += "n:{}\n"
                lastparent[curr_lev] = row[3]
    return s

def get_url(url):
    return url
'''
def get_url(url):
    # use tldextract to get the domain
    ext = tldextract.extract(url)

    # if it couldn't find anything
    if ext.domain == "" or ext.suffix == "":
        return "nil"
    else:
        return ".".join((ext.domain, ext.suffix))
'''

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
    img  = IMG.new ("RGB", size, (255, 255, 255))
    draw = IMD.Draw(img)
    fnt  = IMF.truetype("Menlo-Regular.ttf", 50)

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
            sitesize = draw.textsize(item[:25], font=fnt)
            vttxt    = str(tree[level][item]["vtscore"])
            vtssize  = draw.textsize(vttxt, font=fnt)

            # draw the circle + text
            draw.ellipse([cx-rad, cy-rad, cx+rad, cy+rad], color, color)
            draw.text([cx-sitesize[0]/2, cy-sitesize[1]], item[:25],  font=fnt, fill=(0,0,0))
            draw.text([cx-vtssize[0]/2 , cy+vtssize [1]], vttxt, font=fnt, fill=(0,0,0))
            
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
    tree         = [{}]
    matches = TREE_PARSER.findall(s)
    # iterate through the matches and 
    # bild the tree
    breakpoint()
    for match in matches:
        c_url = match[0]
        p_url = match[1]
        r_url = "nil"
        j     = json.loads(match[2])
        if "request" in j and "request" in j["request"]:
            if "headers" in j["request"]["request"]:
                if "Referer" in j["request"]["request"]["headers"]:
                    r_url = j["request"]["request"]["headers"]["Referer"]
        
        par = get_url(p_url)
        res = get_url(r_url)
        chi = get_url(c_url)

        #tree = add_branch(tree, (par, p_url), (res, r_url), RULES)
        #tree = add_branch(tree, (res, r_url), (chi, c_url), RULES)
        tree = add_branch(tree, (par, p_url), (chi, c_url), RULES)

    for level in range(1, len(tree)):
        for child, info in tree[level].items():
            if info["ad"] == "no":
                for parent in info["parents"].keys():
                    if tree[level-1][parent]["ad"] != "no":
                        tree[level][child]["ad"] = "inherited"

    return tree

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

def add_branch(tree, parent, child, rules):
    p_url = parent[0]
    c_url = child[0]
    '''
    if p_url == c_url or p_url == "nil" or c_url == "nil":
        return tree
    '''
    if p_url == "nil" or c_url == "nil":
        return tree

    p_lyr = tree_bfs(tree, p_url)

    # if the parent is not in the tree
    if p_lyr == -1:
        # put the parent at the root
        tree[0].update({p_url: {"parents": {"_root": 1}, "ad": "no", "vtscore": 0}})
        if rules.should_block(parent[1]):
            tree[0][p_url]["ad"] = "yes"
        p_lyr = 0
        
    # make sure the tree has enough layers
    tree = tree + [{} for _ in range(len(tree), p_lyr+2)]

    # if the child is not in the tree
    if not child in tree[p_lyr+1]:
        tree[p_lyr+1].update({c_url: {"parents": {p_url: 1}, "ad": "no", "vtscore": 0}})

    # if the child is in the tree and 
    # the child doesn't contain a reference
    # to the parent
    elif not parent in tree[p_lyr+1][c_url]["parents"]:
        tree[p_lyr+1][c_url].update({p_url: 1})

    # if the child is in the tree and
    # the child already contains a reference
    # to the parent
    else:
        tree[p_lyr+1][c_url]["parents"][p_url] += 1

    if tree[p_lyr+1][c_url]["ad"] == "no" and rules.should_block(child[1]):
        tree[p_lyr+1][c_url]["ad"] = "yes"

    return tree

def tree_bfs(tree, item):
    # search "horizontally"
    for i in range(0, len(tree)):
        if item in tree[i]:
            return i
    # item is not in the tree
    return -1

# eof #
