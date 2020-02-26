# AppImageRepository
AppImage repository

As Linux users, we like to find all applications in a single place, and download/install them with a click.
This is not possible with traditional AppImageHub. 

We provide

* a tool `appimage-crawler.py` whose goal is the creation of a database `appimages.json` of AppImage's, starting from other online found resources (currently we look at the feed https://appimage.github.io/feed.json).
* a webinterface https://luca-vercelli.github.io/AppImageRepository/ that allow downoading software found in the database
* a tool `appimage.py` that allows installing/removing packages from CLI looking at the database


## Known issues

* Currently, `appimage-crawler.py` requires several days of computation to generate data. Probably that could be improved.
* Sometimes, `appimage-crawler.py` stucks, it must be stopped and relaunched with `--continue` option. (Why?)
