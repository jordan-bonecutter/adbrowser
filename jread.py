import json
import re
import PIL
from PIL import Image as IMG
from PIL import ImageDraw as IMD
from PIL import ImageFont as IMF

PARSER = None

# my regex string:
# ^ = look for string start
# (?: .*?\.)*
#   - the parenthesis mean to create a new regex group
#   - the ?: means that the regex compiler doesn't need 
#     to save the result of this group 
#     (we don't care about www. or ads.qs. or whatever)
#   - the .*?\. means to look for the shortest string of 
#     characters ending in a period
#   - the * after the close paranthesis means to find the 
#     most string of characters followed by periods
#   - for https://google.com this would isolate https://
# ([A-Za-z\d]+\.[A-Za-z\.]+)/
#   - once again, the paranethesis means to find a group
#   - [A-Za-z\d]+\. means to find a string of atleast length
#     consisting of only characters in A-Z, a-z, or 0-9 ending
#     with a period (for https://google.com/ this would isolate
#     google)
#   - Similarly, [A-Za-z\.]+/ means to find a string of atleast
#     length one consisting of A-Z, a-z, and . ending in a / 
#     (for https://google.com/ this would isolate com/)
# .*$
#   - this means to find any string of any length until you 
#     hit the null character
#magic_string = r"^(?:.*?\.)*([A-Za-z\d]+\.[A-Za-z\.]+)/.*$"
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
    if PARSER == None:
        PARSER = re.compile(magic_string)

    if len(url) > 40:
        url = url[:40]
    if url == None:
        return "nil"
    res = PARSER.search(url)
    if res == None:
        return "nil"
    return res.group(1)

def draw_tree(tree):
    # get the tree topology
    levels = [0]
    levels,width = get_levels(tree, 0, levels, 0)

    # from the tree topology, we can find the size our 
    # image needs to be
    radius = 200
    bufx   = 100
    bufy   = 400
    size   = (2*(radius+bufx)*width, 2*(radius+bufy)*(len(levels)-1))
    bmp    = IMG.new("RGB", size, (255, 255, 255))
    draw   = IMD.Draw(bmp)
    drawn  = [0]*len(levels)
    fnt    = IMF.truetype("Menlo-Regular.ttf", 50)
    draw_tree_sub(tree, 0, levels, draw, drawn, size, fnt, (-1,-1), radius, bufx, bufy)
    del draw
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
    if curr >= len(levels):
        levels.append(0)
    for item in tree.keys():
        levels[curr] += 1
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

    if head_url == "nil" or head_url == parent_url:
        if 'children' in head:
            for child in head['children']:
                tree_recurse(tree, child, parent_url)
        return tree

    # try to put it as a new node on the tree
    if not head_url in tree:
        #breakpoint()
        tree.update({head_url:{}})

    # if the node has no children, return
    if not 'children' in head:
        return tree
    
    # iterate through children
    for child in head['children']:
        tree_recurse(tree[head_url], child, head_url)

    return tree

def start():
    return get_json('yh.json')