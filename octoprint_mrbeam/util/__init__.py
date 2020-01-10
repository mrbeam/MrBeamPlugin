from itertools import chain

def dict_merge(d1, d2): # (d1: dict, d2: dict):
    for k, v in d1.items():
        if k in d2 and isinstance(v, dict) and isinstance(d2[k], dict):
            d2[k] = dict_merge(d1[k], d2[k])
    return dict(chain(d1.items(), d2.items()))
