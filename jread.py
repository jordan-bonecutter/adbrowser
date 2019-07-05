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

URL_PARSER  = None
TREE_PARSER = None

# url regex string:
# we want to find the "second level domain". to do so
# we will read up until the top level domain and remeber
# it and what came before it
#
# from the outside we have:\
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
url_string  = r"(\w+\.\w{2,6})\/"

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

# use the magic string and regex to 
# isolate the important part of a 
# domain name
def get_url(url):
    global URL_PARSER
    # presumably we are going to call
    # this function many times so compiling
    # the regex will be faster
    if URL_PARSER == None:
        URL_PARSER = re.compile(url_string)

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
    res = URL_PARSER.search(url)
    if res == None:
        return "nil"

    # we should return the first 
    # regex capture group
    return res.group(1)

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
                    plsize = len(structure[level-1])
                    # calculate on offset so that lines dont intersect
                    offset = (pindex+1)*bufy/(plsize+2)
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
        j     = json.loads(match[2])
        if 'requests' in j and 'requests' in j['requests']:
            if 'headers' in j['requests']['requests']:
                if 'Referer' in j['requests']['requests']['headers']:
                    p_url = get_url(j['requests']['requests']['headers']['Referer'])
        # if the url is garbage or it is
        # a self redirect which we don't
        # really care about
        if c_url == "nil" or p_url == "nil" or c_url == p_url:
            continue
        p_lyr = tree_bfs(tree, p_url)

        # if the parent is not in the tree
        if p_lyr == -1:
            # add it to the root
            tree[0].update({p_url:{"_root":1}})
            if len(tree) == 1:
                tree.append({})

            # see if the child exists in 
            # the next layer
            if c_url in tree[1]:
                if p_url in tree[1][c_url]:
                    tree[1][c_url][p_url] += 1
                else:
                    tree[1][c_url].append(p_url)
            else:
                tree[1].update({c_url:{p_url:1}})

        # if the parent is in the tree
        else:
            if len(tree) == p_lyr+1:
                tree.append({})
            
            # see if the child exists in 
            # the next layer
            if c_url in tree[p_lyr+1]:
                if p_url in tree[p_lyr+1][c_url]:
                    tree[p_lyr+1][c_url][p_url] += 1
                else:
                    tree[p_lyr+1][c_url].update({p_url:1})
            else:
                tree[p_lyr+1].update({c_url:{p_url:1}})

    return tree

def tree_bfs(tree, item):
    # search "horizontally"
    for i in range(0, len(tree)):
        if item in tree[i]:
            return i
    # item is not in the tree
    return -1

# eof #
