import json as JSON

def load(fname):
    with open(fname, "r") as fi:
        return JSON.loads(fi.read())

def entries_with_key(l, key):
    ret = {}
    for item in l:
        if item[key] not in ret:
            ret.update({item[key]: 1})
        else:
            ret[item[key]] += 1
    return ret
