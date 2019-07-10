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
from adblockparser import AdblockRules as ABR
from PIL           import Image        as IMG
from PIL           import ImageDraw    as IMD
from PIL           import ImageFont    as IMF

TREE_PARSER = None
RULES       = None
RULES_FILE  = "easylist.json"
VT_ATTR     = {"apk_file": "vt.key", "req_url": "https://www.virustotal.com/vtapi/v2/url/report"}
FORMAT      = "backreferenced-1.1"

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
            color = (50, 20, 255)
            if tree[level][item]["ad"]:
                color = (255, 20, 50)

            # since we are iterating "horizontally", we
            # need only update the x position
            cx  = c0x + structure[level][item]*(2*rad + bufx)
            
            # draw ecntered text
            sitesize = draw.textsize(item, font=fnt)
            vttxt    = str(tree[level][item]["vtscore"])
            vtssize  = draw.textsize(vttxt, font=fnt)

            # draw the circle + text
            draw.ellipse([cx-rad, cy-rad, cx+rad, cy+rad], color, color)
            draw.text([cx-sitesize[0]/2, cy-sitesize[1]], item,  font=fnt, fill=(0,0,0))
            draw.text([cx-vtssize[0]/2 , cy+vtssize [1]], vttxt, font=fnt, fill=(0,0,0))
            
            # if we aren't at the top level then
            # draw a line connecting it to its parent(s)
            if plev != -1:
                # iterate through parents
                for parent in tree[level][item]["parents"].keys():

                    # get the index of the parent
                    pindex = structure[level-1][parent]
                    cpx    = c0xp + (pindex)*(2*rad + bufx)
                    cpy    = c0yp
                
                    # get the width of the parent layer
                    plsize = len(puni)
                    # calculate on offset so that lines dont intersect
                    offset = (puni[parent]+2)*bufy/(plsize+3)
                    # draw 3 lines to connect the parent and child
                    draw.line([(cx, cy-rad), (cx, cy-rad-offset-thck/2)], (0,0,0),thck)
                    draw.line([(cx, cy-rad-offset), (cpx, cy-rad-offset)], (0,0,0), thck)
                    draw.line([(cpx, cy-rad-offset+thck/2), (cpx, cpy+rad)], (0,0,0), thck)

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

        tree = add_branch(tree, (par, p_url), (res, r_url), RULES)
        tree = add_branch(tree, (res, r_url), (chi, c_url), RULES)

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
    if p_url == c_url or p_url == "nil" or c_url == "nil":
        return tree

    p_lyr = tree_bfs(tree, p_url)

    # if the parent is not in the tree
    if p_lyr == -1:
        # put the parent at the root
        tree[0].update({p_url: {"parents": {"_root": 1}, "ad": False, "vtscore": 0}})
        p_lyr = 0
        
    # make sure the tree has enough layers
    tree = tree + [{} for _ in range(len(tree), p_lyr+2)]

    # if the child is not in the tree
    if not child in tree[p_lyr+1]:
        tree[p_lyr+1].update({c_url: {"parents": {p_url: 1}, "ad": False, "vtscore": 0}})

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

    if not tree[p_lyr+1][c_url]["ad"] and rules.should_block(child[1]):
        tree[p_lyr+1][c_url]["ad"] = True

    if not tree[p_lyr][p_url]["ad"] and rules.should_block(parent[1]):
        tree[p_lyr][p_url]["ad"] = True
    
    return tree

def tree_bfs(tree, item):
    # search "horizontally"
    for i in range(0, len(tree)):
        if item in tree[i]:
            return i
    # item is not in the tree
    return -1

# eof #
