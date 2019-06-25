# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# jread.py  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Created by: Jordan Bonecutter for HPCForge  # # # # # # # # # # # # # #
# 25 June 2019  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# imports
import json
import re
import PIL
from PIL import Image as IMG
from PIL import ImageDraw as IMD
from PIL import ImageFont as IMF

PARSER = None

# my regex string:
# we want to find the "second level domain". to do so
# we will read up until the top level domain and remeber
# it and what came before it
#
# from the outside we have:
# ()\/
# we see a capture group followed by a literal / charcter.
# since we want to capture up until the first /, we should 
# capture what is immediately before it. Inside the capture 
# group we have:
# \w+\.\w{2,6}
# remember, we want to capture the second level domain so 
# we will read up until the last dot that is followed by a 
# forward slash (\w{2,6} means any word character string in 
# length between 2 and 6. for www.google.com/ this would isolate
# the "com" part)
# It is surrounded in paranthesis to capture it. if we were to
# run it on the following url:
# https://doubleclickads.net/4fxj/l
# we would get:
# doubleclickads.net
magic_string = r"(\w+\.\w{2,6})\/"

# use the json library to build a 
# dictionary out of the json
def get_json(fi):
    contents = open(fi, 'r').read()
    return json.loads(contents)

# use the magic string and regex to 
# isolate the important part of a 
# domain name
def get_url(url):
    global PARSER
    # presumably we are going to call
    # this function many times so compiling
    # the regex will be faster
    if PARSER == None:
        PARSER = re.compile(magic_string)

    # trim the string so the 
    # regex takes faster
    if len(url) > 40:
        url = url[:40]

    # catch the caller passing NULL
    if url == None:
        return "nil"

    # if we didn't find a url, for example:
    # about:none
    # appears many times, we should return a
    # string letting the caller know that we
    # didn't get a match
    res = PARSER.search(url)
    if res == None:
        return "nil"

    # we should return the first 
    # regex capture group
    return res.group(1)

def draw_tree(tree):
    # get the tree topology
    levels = [0]
    levels,width = get_levels(tree, 0, levels, 0)

    # eventually i should make these fit the tree
    # size but that sounds like a lot of time
    radius = 200
    bufx   = 100
    bufy   = 400

    # from the tree topology, we can find the size our 
    # image needs to be
    size   = (2*(radius+bufx)*width, 2*(radius+bufy)*(len(levels)-1))

    # create the bitmap to draw on
    bmp    = IMG.new("RGB", size, (255, 255, 255))
    draw   = IMD.Draw(bmp)

    # params for the drawing function
    drawn  = [0]*len(levels)
    fnt    = IMF.truetype("Menlo-Regular.ttf", 50)
    draw_tree_sub(tree, 0, levels, draw, drawn, size, fnt, (-1,-1), radius, bufx, bufy)
    del draw

    # save it, of course
    bmp.save("testtree3.png", "PNG")

def draw_tree_sub(tree, curr, levels, draw, drawn, size, fnt, par_pos, rad, bufx, bufy):
    # iterate through subtree
    for key in tree.keys():
        # we want to draw the nodes so that each level is centered
        # so what we should do is find the center of the leftmost
        # circle (c0) and then add an offset for the current circle
        #
        # the center of the leftmost circle will be the center of the
        # page - half the range of all the circles (if you draw this
        # out you will see it). so i do this math for both the x & y 
        # coords and draw each circle accordingly
        ctr = size[0]/2
        rng = (2*(bufx+rad))*levels[curr] - (2*bufx)
        c0  = (ctr - (rng/2)) + rad
        cx  = (2*(rad+bufx))*drawn[curr] + c0

        ctr = size[1]/2
        rng = (2*(bufy+rad))*(len(levels)-1) - (2*bufy)
        c0  = (ctr - (rng/2)) + rad
        cy  = (2*(rad+bufy))*curr + c0

        # actually draw the circle
        draw.ellipse([cx-rad, cy-rad, cx+rad, cy+rad], (50, 0, 255), (50, 0, 255))
        # draw the text cenetered in the circle
        w,h = draw.textsize(key, font=fnt)
        draw.text((cx-w/2, cy-h/2), key, font=fnt, fill=(0, 255, 100))
        # draw a line connecting it to its parent
        # we want the lines to have some separation so that we can tell 
        # who their parent is. so each connection will have 3 segements, the
        # first segment moves purely up, the second segment moves purely horizontal
        # and the third segment moves purely up again. the first segment will move up 
        # different lengths depending on the node, so that's why there's some extra math.
        # basically, you start at angle pi/2 for the child circle (cx, cy-rad) then you move
        # up towards the y coordinate of the next circle cy-rad + dy (dy being that long
        # next part). then you move from that coord to 3pi/2 on the parent (p[0], p[1]+rad)
        if par_pos[0] > 0:
            draw.line([(cx, cy-rad), (cx, cy-rad + (drawn[curr]+1)*((par_pos[1]+rad-cy+rad))/(levels[curr]+2)), (par_pos[0], cy-rad + (drawn[curr]+1)*((par_pos[1]+rad-cy+rad))/(levels[curr]+2)), (par_pos[0], par_pos[1]+rad)], (0, 255, 100), 10)

        # increment drawn
        drawn[curr] += 1

        #recurse!
        draw_tree_sub(tree[key], curr+1, levels, draw, drawn, size, fnt, (cx, cy), rad, bufx, bufy)

# get the topology of our tree
def get_levels(tree, curr, levels, maxw):
    # if we traversed to a new level, we
    # need to add more space to the level 
    # list
    if curr >= len(levels):
        levels.append(0)

    # iterate through the children
    for item in tree.keys():
        # increment the number of childen 
        # at the current level of the tree 
        levels[curr] += 1
        # also find the maxwidth of the tree
        if levels[curr] > maxw:
            maxw = levels[curr]
        t, maxw = get_levels(tree[item], curr+1, levels, maxw)
    return levels, maxw

# build the dependency tree
def get_tree(jso):
    js = get_json(jso)

    # start at the root node
    head = js['_root']
    tree = {}
    tree = tree_recurse(tree, head, "no")
    return tree

def tree_recurse(tree, head, parent_url):
    # get head url
    head_url = get_url(head['data'])

    # if the redirect is to the same site or 
    # it is the root node, we don't count this
    # as a new level in the tree
    if head_url == "nil" or head_url == parent_url:
        if 'children' in head:
            for child in head['children']:
                tree_recurse(tree, child, parent_url)
        return tree

    # try to put it as a new node on the tree
    if not head_url in tree:
        tree.update({head_url:{}})

    # if the node has no children, return
    if not 'children' in head:
        return tree
    
    # iterate through children
    for child in head['children']:
        tree_recurse(tree[head_url], child, head_url)

    return tree
