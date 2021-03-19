import os
import logging
import difflib

# from urllib.request import urlopen
import urllib


def get_gcode(url, local=None):
    log = logging.getLogger()
    content = ""
    if local != None and os.path.isfile(local):
        with open(local, "r") as file:
            content = file.read()
        log.info("GCode fetched from {}".format(local))
        return content
    else:
        f = urllib.urlopen(url)
        httpCode = f.getcode()
        if httpCode != 200:
            logging.getLogger().error(
                "HTTP Code {} while fetching resource {}".format(httpCode, url)
            )
            return ""
        log.info(
            "GCode fetched from {} as local file '{}' was not readable.".format(
                url, local
            )
        )
        content = f.read()
    return content


def compare(gcode1, gcode2, ignoreComments=True, maxLines=500):
    arr1 = gcode1.splitlines()
    arr2 = gcode2.splitlines()
    logging.getLogger().info(
        "comparing gcodes: generated {} lines, expected {} lines (Limit: {} lines)...".format(
            len(arr1), len(arr2), maxLines
        )
    )
    if ignoreComments:
        arr1 = map(_strip_comments, arr1[:maxLines])
        arr2 = map(_strip_comments, arr2[:maxLines])

    output_list = [li for li in difflib.ndiff(arr1, arr2) if li[0] != " "]
    return output_list


def _strip_comments(line):
    if len(line) > 0 and line[0] == ";":
        return "; ---"
    else:
        return line.split(";", 1)[0]
