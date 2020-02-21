#!/usr/bin/env python3
# pip3 install requests

import requests
import os
import json
import logging
from html.parser import HTMLParser
import argparse
import datetime
from urllib.parse import urlsplit, urlunsplit

# constants
URL_FEEDS = "https://appimage.github.io/feed.json"
HOME = os.path.expanduser("~")  # this is portable across OS"s
LOCAL_CONF_DIR = os.path.join(HOME, ".config", "appimages-util")
DB = os.path.join(LOCAL_CONF_DIR, "appimages.json")
SAVE_OFTEN = True
LOG_LEVEL = logging.DEBUG
MAX_LOOPS = 0              # DEBUG ONLY. if <=0 then no limit.
VERSION = "1.0"


def init_logging():
    """
    Naive logging module init
    """
    global _logger
    _logger = logging.getLogger("appimage-utils")
    _logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    _logger.addHandler(ch)


def download_initial_db():
    """
    Download an initial version of DB
    @return a list (we hope)
    """
    response = requests.get(URL_FEEDS)
    return response.json()["items"]


def read_db():
    """
    Return json data present on local db
    """
    x = None
    with open(DB) as in_file:
        x = json.load(in_file)
    return x


def create_db(_continue=False):
    """
    Entry point
    """
    global statistics
    if not _continue:
        all_apps = download_initial_db()
        save_db(all_apps)
    else:
        all_apps = read_db()
    statistics.packages = len(all_apps)
    loops = 0
    for app_dict in all_apps:
        # es. app_dict =
        # {"name": "AKASHA", "description": "Akasha platform", "categories": ["Network"],
        # "authors": [{"name": "AkashaProject", "url": "https://github.com/AkashaProject"}],
        # "license": None, "links": [{"type": "GitHub", "url": "AkashaProject/Community"},
        # {"type": "Download", "url": "https://github.com/AkashaProject/Community/releases"}],
        # "icons": ["AKASHA/icons/128x128/akasha.png"], "screenshots": ["AKASHA/screenshot.png"]}
        url = None
        if "links" in app_dict and app_dict["links"]:
            for x in app_dict["links"]:
                if x["type"] == "Download":
                    url = x["url"]
                    break
        if url:
            _logger.info("package " + str(app_dict["name"]))
            _oldappimages = statistics.app_images
            if "versions" in app_dict and _continue:
                # skip package, previously elaborated
                continue
            loops += 1
            app_dict["versions"] = search_versions(url)
            if statistics.app_images > _oldappimages:
                statistics.packages_with_appimages += 1
            if SAVE_OFTEN:
                save_db(all_apps)
            if MAX_LOOPS > 0 and loops >= MAX_LOOPS:
                break
            _logger.info("Statistics:\n" + str(statistics))
        # TODO else delete that package
    save_db(all_apps)


def search_versions(url, versions=None, depth=1):
    """
    Follow url searching for AppImages
    @param url is a full url, not just "/hello" or "#hello"
    """
    global crawled_urls, statistics
    if versions is None:
        versions = []

    if url is not None and url != "/":

        if url in crawled_urls:
            return versions
        _logger.info(" > crawling URL " + str(url))

        crawled_urls.add(url)

        try:
            response = requests.head(url, allow_redirects=True)
            # github link redirects to real link
            # by default, 'requests' follow links in GET non in HEAD
        except:
            _logger.error("Cannot connect to URL '%s'" % url)
            return versions

        crawled_urls.add(response.url)
        mimetype = get_mimetype(response)
        if mimetype is not None and mimetype.startswith("text/html"):
            # The given URL is an HTML Page
            if depth > 0:
                response = requests.get(url)
                parser = AppImageHTMLParser(url, versions, depth)
                parser.feed(response.text)
        else:
            # The given URL could be a downloadable file
            props = guess_appimage_properties(url, response)
            if props is not None:
                _logger.info("  > found AppImage!")
                if props not in versions:
                    versions.append(props)
                    statistics.app_images += 1

        _logger.info(" > END crawling URL " + str(url))
    
    return versions

class AppImageHTMLParser(HTMLParser):
    """
    Follow links in HTML page
    """

    def __init__(self, url, versions, depth):
        """
        @param versions a set of already-found files
        @param depth depth of search algorithm
        """
        super().__init__()
        self.versions = versions
        self.depth = depth
        self.url = url

    def handle_starttag(self, tag, attrs):
        """
        Executed when any tag begins
        """
        if tag != "a":      # Hope it's case-insensitive
            return
        url2 = self.get_attr(attrs, "href")
        if url2 and url2 != "/" and not url2.startswith("#"):
            if url2.startswith("/"):
                url2 = url_absolute(url2, self.url)
            search_versions(url2, self.versions, self.depth-1)


    def get_attr(self, attrs, attr_name):
        """
        Return first occurrence of given attr
        """
        for (attr, value) in attrs:
            if attr == attr_name:
                return value


def guess_appimage_properties(url, response):
    """
    return a record of AppImage properties, or None
    @param url Gihubb download URL
    """
    # TODO allow tar/zip archives
    if url.startswith("https://github.com") and "/releases/" in url:
        filename = url[url.rfind("/")+1:]
        os = None
        # os values as in sys.platform
        if filename.endswith(".dmg"):
            os = "darwin"
        elif filename.endswith(".exe"):
            os = "win32"
        elif filename.endswith("AppImage"):
            os = "linux"
        if os is not None:
            return {
                "url": url,
                "os": os,
                "filesize": get_filesize(response)
                }
    return None


def url_absolute(path, parent_url):
    """
    (/newpath,  http://server/oldpath)   =>  http://server/newpath
    """
    parts = urlsplit(parent_url)
    return urlunsplit([parts[0], parts[1], path, None, None])

def url_remove_fragment(url):
    """
    http://one/two#three  =>  http://one/two
    """
    index = url.find("#")
    if index > 0:
        return url[0:index]
    else:
        return url


def url_get_parent(url):
    """
    http://one/two/three  =>  http://one/two
    http://one            =>  http://one
    """
    index = url.rfind("/")
    if index > 8:           # avoid https://
        return url[0:index]
    else:
        return url


def get_mimetype(response):
    """
    Extract MIME type from given response (usually a HEAD request), or None
    """
    try:
        return response.headers["Content-Type"]
    except:     # KeyError
        return None


def get_filesize(response):
    """
    Extract file size from given response (usually a HEAD request), or None
    """
    try:
        return int(response.headers["Content-Length"])
    except:     # KeyError, ValueError
        return None


def create_parent_dir(filename):
    """
    Create parent directory
    """
    parentdir = os.path.dirname(filename)
    if parentdir:
        os.makedirs(parentdir, exist_ok=True)


def save_db(all_apps):
    """
    Save all_apps to disk, using DB as filename
    """
    _logger.debug("Saving to database " + DB)
    create_parent_dir(DB)
    with open(DB, "w") as outfile:
        json.dump(all_apps, outfile)


def parse_cli_args():
    """
    Parse CLI aguments, return an object containing all of them
    """
    parser = argparse.ArgumentParser(description="(Re)generate apps database." +
                                     "DB is by default in " + DB)
    parser.add_argument("-v", "--version", action="version", version="%(prog)s " + VERSION)
    parser.add_argument("--db", help="custom DB location (optional)")
    parser.add_argument("--max-loops", type=int, help="a limit on number of packages (for debug purposes)")
    parser.add_argument("--continue", action="store_true", dest="_continue",
                        help="do not download, continue a previous build")
    args = parser.parse_args()
    return args


class Statistics:
    """
    Plain object, store some packages statistics
    """
    def __init__(self):
        self.packages = 0
        self.app_images = 0
        self.packages_with_appimages = 0
        self.start_time = datetime.datetime.now()

    def __str__(self):
        global crawled_urls
        return "Tot.packages:\t\t\t\t" + str(self.packages) + "\n" + \
            "Crawled URL's:\t\t\t\t" + str(len(crawled_urls)) + "\n" + \
            "AppImage's found:\t\t\t" + str(self.app_images) + "\n" + \
            "Packages with at least one AppImage:\t" + str(self.packages_with_appimages) + "\n" + \
            "Time elapsed:\t\t\t\t" + str(self.time_elapsed()) + "h.\n"

    def time_elapsed(self):
        """
        Return minutes elapsed since self.start_time
        """
        end_time = datetime.datetime.now()
        difference = end_time - self.start_time
        return (int)(difference.total_seconds() // 3600)

# global variables
crawled_urls = set()
_logger = None
statistics = Statistics()


if __name__ == "__main__":
    args = parse_cli_args()
    init_logging()
    _logger.debug("CLI arguments: " + str(args))
    if args.db:
        DB = args.db
    if args.max_loops:
        MAX_LOOPS = args.max_loops
    _logger.info("Begin search...")
    try:
        create_db(args._continue)
    finally:
        # Statistics will be printed also in case of exceptions
        _logger.info("Statistics:\n" + str(statistics))
    _logger.info("Done.")
