"""
This util contains all the necessary methods to communicate with the github api
"""
import base64

from requests.adapters import HTTPAdapter, MaxRetryError
from requests import ConnectionError
from urllib3 import Retry

from octoprint_mrbeam.mrb_logger import mrb_logger
import requests
import json

_logger = mrb_logger("octoprint.plugins.mrbeam.util.github_api")
REPO_URL = "https://api.github.com/repos/mrbeam/{repo}"

def get_file_of_repo_for_tag(file, repo, tag):
    """
    return the content of the <file> of the repo <repo> for the given tag/branch/hash <tag>

    Args:
        file: file
        tag: tag/branch/hash
        repo: github repository

    Returns:
        content of file
    """
    try:
        url = "{repo_url}/contents/{file}?ref={tag}".format(
            repo_url=REPO_URL.format(repo=repo), file=file, tag=tag
        )

        headers = {
            "Accept": "application/json",
        }

        s = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.3)
        adapter = HTTPAdapter(max_retries=retry)
        s.mount("https://", adapter)
        s.keep_alive = False

        response = s.request("GET", url, headers=headers)
    except MaxRetryError:
        _logger.warning("timeout while trying to get the  file")
        return None
    except ConnectionError:
        _logger.warning("connection error while trying to get the file {}".format(url))
        return None

    if response:
        json_data = json.loads(response.text)
        content = base64.b64decode(json_data["content"])
        return content
    else:
        _logger.warning("no valid response for the file - {}".format(response))
        return None
