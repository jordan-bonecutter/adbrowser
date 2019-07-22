import json
import jread

di = "res/img/"

def all_pngs():
    with open("res/crawl.json", "r") as fi:
        crawls = json.loads(fi.read())

    for site, data in crawls.items():
        for ids, snap in enumerate(data["snapshots"]):
            jread.draw_tree(snap["tree"], di+site+"_full"+str(ids)+".png")
            jread.draw_tree(jread.trim_tree(snap["tree"]), di+site+"_trim"+str(ids)+".png")

def ads_list(explicit):
    with open("res/crawl.json", "r") as fi:
        crawls = json.loads(fi.read())

    ads = {}
    for site, data in crawls.items():
        for snap in data["snapshots"]:
            for layer in snap["tree"]:
                for url, data in layer.items():
                    if explicit:
                        if data["ad"] == "yes":
                            try:
                                ads[jread.get_url(url)] += 1
                            except KeyError:
                                ads.update({jread.get_url(url): 1})
                    else:
                        if data["ad"] != "no":
                            try:
                                ads[jread.get_url(url)] += 1
                            except KeyError:
                                ads.update({jread.get_url(url): 1})

    to_sort = []
    for site, weight in ads.items():
        to_sort.append((site, weight))

    sort = sorted(to_sort, key=lambda item: -item[1])
    return sort
def types_list():
    with open("res/crawl.json", "r") as fi:
        crawls = json.loads(fi.read())
    types = {}
    for site, data in crawls.items():
        for snap in data["snapshots"]:
            for layer in snap["tree_full"]:
                for url, data in layer.items():
                    try:
                        types[data["type"]] += 1
                    except KeyError:
                        types.update({data["type"]: 1})
    return types
