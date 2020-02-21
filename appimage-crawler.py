#!/usr/bin/env python3
# pip3 install requests

import requests
import os
import json
import logging
from html.parser import HTMLParser
import argparse
import datetime

# constants
URL_FEEDS = "https://appimage.github.io/feed.json"
HOME = os.path.expanduser("~")  # this is portable across OS"s
LOCAL_CONF_DIR = os.path.join(HOME, ".config", "appimages-util")
DB = os.path.join(LOCAL_CONF_DIR, "appimages.json")
SAVE_OFTEN = True
LOG_LEVEL = logging.DEBUG
MAX_LOOPS = 10              # DEBUG ONLY. if <=0 then no limit.
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
    return json.load(DB)


def create_db(_continue=False):
    """
    Entry point
    """
    global statistics
    if not _continue:
        all_packages = download_initial_db()
        save_db(all_packages)
    else:
        all_packages = read_db()
    statistics.packages = len(all_packages)
    loops = 0
    for package_dict in all_packages:
        url = None
        if "links" in package_dict and package_dict["links"]:
            for x in package_dict["links"]:
                if x["type"] == "Download":
                    url = x["url"]
                    break
        if url:
            # es. package_dict =
            # {"name": "AKASHA", "description": "Akasha platform", "categories": ["Network"],
            # "authors": [{"name": "AkashaProject", "url": "https://github.com/AkashaProject"}],
            # "license": None, "links": [{"type": "GitHub", "url": "AkashaProject/Community"},
            # {"type": "Download", "url": "https://github.com/AkashaProject/Community/releases"}],
            # "icons": ["AKASHA/icons/128x128/akasha.png"], "screenshots": ["AKASHA/screenshot.png"]}
            _logger.info("package " + str(package_dict["name"]))
            _oldappimages = statistics.app_images
            if "versions" in package_dict and _continue:
                # skip package, previously elaborated
                continue
            loops += 1
            package_dict["versions"] = search_versions(url)
            if statistics.app_images > _oldappimages:
                statistics.packages_with_appimages += 1
            if SAVE_OFTEN:
                save_db(all_packages)
            if MAX_LOOPS > 0 and loops >= MAX_LOOPS:
                break
        # TODO else delete that package
    save_db(all_packages)


def search_versions(url, versions=None, depth=1):
    """
    Follow url searching for AppImages
    """
    global crawled_urls, statistics
    if versions is None:
        versions = []
    if url is not None:
        _logger.info(" > crawling URL " + str(url))
        crawled_urls.add(url)
        statistics.crawled_urls += 1
        response = requests.get(url)
        parser = AppImageHTMLParser(url, versions, depth)
        parser.feed(response.text)
        _logger.info(" > END crawling URL " + str(url))
    return versions


class AppImageHTMLParser(HTMLParser):
    """
    Follow links in HTML page, searching for AppImages
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
        global crawled_urls, statistics
        if tag != "a":      # Hope it's case-insensitive
            return
        url = self.get_attr(attrs, "href")
        if not url:
            return
        if url.startswith("/") or url.startswith("#"):
            url = self.url + url
        if url in crawled_urls:
            return
        _logger.info("  > found link " + str(url))
        crawled_urls.add(url)
        props = guess_appimage_properties(url)
        if props is not None:
            _logger.info("  > found AppImage!")
            if props not in self.versions:
                self.versions.append(props)
                statistics.app_images += 1
        elif self.depth > 0:
            mimetype = get_mimetype(url)
            _logger.info("  > mimetype: " + str(mimetype))
            if mimetype is not None and mimetype.startswith("text/html"):
                search_versions(url, self.versions, self.depth-1)

    def get_attr(self, attrs, attr_name):
        """
        Return first occurrence of given attr
        """
        for (attr, value) in attrs:
            if attr == attr_name:
                return value

def guess_appimage_properties(url):
    """
    return a record of AppImage properties, or None
    @param url
    """
    if url.startswith("https://github.com") and "/releases/" in url:
        filename = url[url.rfind("/")+1:]
        os = None
        if filename.find("AppImage") >= 0:
            # this will cut out a lot of files, it"s a security measure
            if filename.endswith(".dmg"):
                os = "mac"
            elif filename.endswith(".exe"):
                os = "win"
            else:
                os = "linux"
        if os is not None:
            return {
                "url": url,
                "os": os,
                "filesize": get_filesize(url)
                }
    return None


def get_mimetype(url):
    """
    Issue a HEAD request to retrieve MIME file type without downloading it
    """
    try:
        response = requests.head(url)
    except:
        return None
    if "Content-Type" in response.headers:          # case-insensitive
        return response.headers["Content-Type"]
    else:
        return None


def get_filesize(url):
    """
    Issue a HEAD request to retrieve file size without downloading it
    """
    try:
        response = requests.head(url)
    except:
        return None
    if "Content-Length" in response.headers:          # case-insensitive
        return int(response.headers["Content-Length"])
    else:
        return None


def create_parent_dir(filename):
    """
    Create parent directory
    """
    parentdir = os.path.dirname(filename)
    if parentdir:
        os.makedirs(parentdir, exist_ok=True)


def save_db(all_packages):
    """
    Save all_packages to disk, using DB as filename
    """
    _logger.debug("Saving to database " + DB)
    create_parent_dir(DB)
    with open(DB, "w") as outfile:
        json.dump(all_packages, outfile)


def parse_cli_args():
    """
    Parse CLI aguments, return an object containing all of them
    """
    parser = argparse.ArgumentParser(description="(Re)generate apps database." + \
        "DB is by default in " + DB)
    parser.add_argument("-v", "--version", action="version", version="%(prog)s " + VERSION)
    parser.add_argument("--db", help="custom DB location (optional)")
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
        self.crawled_urls = 0
        self.app_images = 0
        self.packages_with_appimages = 0
        self.start_time = datetime.datetime.now()

    def __str__(self):
        return "Tot.packages:\t\t\t\t" + str(self.packages) + "\n" + \
            "Crawled URL's:\t\t\t\t" + str(self.crawled_urls) + "\n" + \
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
    _logger.info("Begin search...")
    try:
        create_db(args._continue)
    finally:
        # Statistics will be printed also in case of exceptions
        _logger.info("Statistics:\n" + str(statistics))
    _logger.info("Done.")
