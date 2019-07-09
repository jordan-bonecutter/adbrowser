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
from PIL import Image as IMG
from PIL import ImageDraw as IMD
from PIL import ImageFont as IMF

TREE_PARSER = None

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
            for parent in tree[level][child]:
                if parent not in puni:
                    puni.update({parent: index})
                    index += 1

        for item in structure[level].keys():
            # since we are iterating "horizontally", we
            # need only update the x position
            cx  = c0x + structure[level][item]*(2*rad + bufx)
            
            # draw ecntered text
            textsize = draw.textsize(item, font=fnt)

            # draw the circle + text
            draw.ellipse([cx-rad, cy-rad, cx+rad, cy+rad], (50, 0, 255), (50, 0, 255))
            draw.text([cx-textsize[0]/2, cy-textsize[1]/2], item, font=fnt, fill=(0,0,0))
            
            # if we aren't at the top level then
            # draw a line connecting it to its parent(s)
            if plev != -1:
                # iterate through parents
                for parent in tree[level][item].keys():
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
    global TREE_PARSER
    if TREE_PARSER == None:
        TREE_PARSER = re.compile(tree_string)
    
    # init an empty tree
    tree    = [{}]
    matches = TREE_PARSER.findall(s)
    # iterate through the matches and 
    # bild the tree
    for match in matches:
        c_url = get_url(match[0])
        p_url = get_url(match[1])
        r_url = "nil"
        j     = json.loads(match[2])
        if "request" in j and "request" in j["request"]:
            if "headers" in j["request"]["request"]:
                if "Referer" in j["request"]["request"]["headers"]:
                    r_url = get_url(j["request"]["request"]["headers"]["Referer"])
        
        tree = add_branch(tree, p_url, r_url)
        tree = add_branch(tree, r_url, c_url)
        
    return tree

def add_branch(tree, parent, child):
    if parent == child or parent == "nil" or child == "nil":
        return tree

    p_lyr = tree_bfs(tree, parent)

    # if the parent is not in the tree
    if p_lyr == -1:
        # put the parent at the root
        tree[0].update({parent: {"_root": 1}})
        p_lyr = 0
        
    # make sure the tree has enough layers
    tree = tree + [{} for _ in range(len(tree), p_lyr+2)]

    # if the child is not in the tree
    if not child in tree[p_lyr+1]:
        tree[p_lyr+1].update({child: {parent: 1}})

    # if the child is in the tree and 
    # the child doesn't contain a reference
    # to the parent
    elif not parent in tree[p_lyr+1][child]:
        tree[p_lyr+1][child].update({parent: 1})

    # if the child is in the tree and
    # the child already contains a reference
    # to the parent
    else:
        tree[p_lyr+1][child][parent] += 1

    return tree

def tree_bfs(tree, item):
    # search "horizontally"
    for i in range(0, len(tree)):
        if item in tree[i]:
            return i
    # item is not in the tree
    return -1

# eof #
