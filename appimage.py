#!/usr/bin/env python3
# pip3 install requests

import requests
import os
import json
import logging
from html.parser import HTMLParser
import argparse
import datetime
import sys

# constants
URL_DB = ""
HOME = os.path.expanduser("~")  # this is portable across OS"s
LOCAL_CONF_DIR = os.path.join(HOME, ".config", "appimages-util")
DB = os.path.join(LOCAL_CONF_DIR, "appimages.json")
APPS_FOLDER = os.path.join(HOME, "Applications")
LOG_LEVEL = logging.DEBUG
VERSION = "1.0"
OS = sys.platform     # see https://stackoverflow.com/questions/446209


if OS not in ('win32', 'linux' 'darwin'):
    raise ValueError("Unsupported platform: " + OS)


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


def download(remote_file_url, local_filename):
    """
    Download and save a remote file to a local file
    Parent folder is created if missing
    Overwrite existing file
    """
    create_parent_dir(local_filename)
    response = requests.get(remote_file_url, stream=True)

    # Throw an error for bad status codes
    response.raise_for_status()

    with open(local_filename, 'wb') as handle:
        for block in response.iter_content(1024):
            handle.write(block)


def sync():
    """
    Download and save the remote database to DB
    """
    download(URL_DB, DB)


def read_db():
    """
    Return json data present on local db
    """
    x = None
    with open(DB) as in_file:
        x = json.load(in_file)
    return x


def get_db_record(appname):
    """
    Read local db, then return the record corresponding to requested app
    @return a dict, or None on error
    """
    for x in read_db():
        if x["Name"] == appname:
            return x
    return None


def list_all():
    apps = read_db()
    if not apps:
        _logger.warning("Database not found, or empty")
        return
    for x in apps:
        print(x["name"])


def list():
    if not os.path.exists(APPS_FOLDER):
        _logger.warning("Apps folder %s does not exist" % APPS_FOLDER)
        return
    fnames = list_filenames(APPS_FOLDER)
    if not fnames:
        _logger.warning("No apps found")
        return
    for fname in fnames:
        print(fname)


def app_installed(appname):
    """
    Search if given app is installed, and in that case return full file path
    return None if not installed
    """
    local_file = os.path.join(APPS_FOLDER, appname + ".AppImage")
    # with no version, ok ?!?
    if os.exists(local_file):
        return local_file
    else:
        return None


def filter_versions(versions):
    """
    extract only versions compatible with current platform, and sort them
    """
    versions = [x for x in versions if x.os == OS]
    return sorted(versions)


def install(appnames):
    for appname in appnames:
        local_file = app_installed(appname)
        if local_file:
            _logger.warning("App %s is already installed" % appname)
            continue
        app = get_db_record(appname)
        if not app:
            _logger.error("App %s not found in database" % appname)
            exit(2)
        versions = filter_versions(app.versions)
        if not versions:
            _logger.debug("DEBUG app=" + str(app))
            _logger.error("App found on database, but no AppImages detected. " +
                          "You may try to manually download it from website %s" % url)
            exit(3)
        download(versions[-1], local_file)


def upgrade(appnames):
    # How do you know current version ?!?
    NOT_IMPLEMENTED()  # TODO


def get_updatable_apps():
    NOT_IMPLEMENTED()  # TODO


def remove(appnames, force=False):
    for appname in appnames:
        local_file = app_installed(appname)
        if local_file:
            os.unlink(local_file)
        else:
            if not force:
                _logger.error("App %s not found locally, searched in %s" %
                              (appname, local_file))
                exit(4)


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


def list_filenames(folder):
    """
    Return list of names of regular (non-folders) files inside given folder
    """
    return [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]


def parse_cli_args():
    """
    Parse CLI aguments, return an object containing all of them
    """
    parser = argparse.ArgumentParser(description="Install/remove AppImage's.")
    parser.add_argument("-v", "--version", action="version", version="%(prog)s " +
                        VERSION)
    parser.add_argument("--db", help="custom DB location (optional)")
    parser.add_argument("--dont-update", action='store_true', help="Avoid " +
                        "updating DB file, if possible")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--sync', '-s', action='store_true', help='Just update db ' +
                       'and exit')
    group.add_argument('--list', '-l', action='store_true', help='List all ' +
                       'AppImages installed in Applications folder')
    group.add_argument('--list-all', action='store_true', help='List all ' +
                       'AppImages present in DB')
    group.add_argument('--install', '-i', metavar='APPNAMES', nargs='+',
                       help='Install specified AppImage into Applications folder,' +
                       'retrieving and downloading the last available AppImage')
    group.add_argument('--update', '--upgrade', '-u', metavar='APPNAMES', nargs='*',
                       help='Update specified AppImage/s in Applications folder,' +
                       'or all apps if no argument is provided')
    group.add_argument('--remove', '-r', metavar='APPNAMES', nargs='+',
                       help='Remove specified AppImage/s in Applications folder')
    args = parser.parse_args()
    return args


# global variables
_logger = None


if __name__ == "__main__":
    args = parse_cli_args()
    init_logging()

    if args.db:
        DB = args.db

    if args.sync and args.dont_update:
        _logger.error("The given arguments are schizophrenic.")
        exit(1)

    if args.dont_update and not os.exists(DB):
        args.dont_update = False

    if (args.sync or args.install or args.update) and not args.dont_update:
        sync()

    if args.sync:
        pass
    elif args.list:
        list()
    elif args.list_all:
        list_all()
    elif args.install:
        install(args.install)
    elif args.update:
        update(args.update)
    elif args.remove:
        remove(args.remove)
