import logging
import difflib

# from urllib.request import urlopen
import urllib


def get_gcode(url):
    f = urllib.urlopen(url)
    httpCode = f.getcode()
    if httpCode != 200:
        logging.getLogger().error(
            "HTTP Code {} while fetching resource {}".format(httpCode, url)
        )
        return ""
    content = f.read()
    return content


def compare(gcode1, gcode2, ignoreComments=True):
    arr1 = gcode1.splitlines()
    arr2 = gcode2.splitlines()
    if ignoreComments:
        arr1 = map(_strip_comments, arr1)
        arr2 = map(_strip_comments, arr2)

    output_list = [li for li in difflib.ndiff(arr1, arr2) if li[0] != " "]
    return output_list


def _strip_comments(line):
    if len(line) > 0 and line[0] == ";":
        return "; ---"
    else:
        return line
