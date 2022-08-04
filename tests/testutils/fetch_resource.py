#!/usr/bin/python

import sys
import os


RESOURCE_BASE = "https://mrbeam.github.io/test_rsc"
RESOURCE_TARGET = "/rsc"


def fetch(paths):

    cwd = os.getcwd()

    for p in paths[1:]:
        url = RESOURCE_BASE + p
        target = cwd + RESOURCE_TARGET + p  # careful - no checks at all
        cmd = (
            "wget -c -N -O " + target + " " + url
        )  # careful! url is not sanitized or checked in any other way.
        print("Fetching: " + cmd)
        out = os.system(cmd)
        if out != 0:
            print("Error. Return was " + str(out))
            return 1
    return 0


if __name__ == "__main__":

    if len(sys.argv) == 0:
        print("Usage fetch_resource.py /folder/resource.yaml /folder2/resource.jpg ...")
        sys.exit(1)

    else:
        rv = fetch(sys.argv)
        sys.exit(rv)
