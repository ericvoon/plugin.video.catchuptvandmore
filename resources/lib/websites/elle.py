# -*- coding: utf-8 -*-
'''
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto
    This file is part of Catch-up TV & More.
    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''
# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

import re
import json

from codequick import Route, Resolver, Listitem
import urlquick

from resources.lib import download
from resources.lib.labels import LABELS


URL_ROOT = 'http://www.elle.fr'

URL_CATEGORIES = URL_ROOT + '/Videos/'

URL_JS_CATEGORIES = 'https://cdn-elle.ladmedia.fr/js/compiled/showcase_bottom.min.js?version=%s'
# IdJsCategories

URL_VIDEOS_JSON = 'https://content.jwplatform.com/v2/playlists/%s'
# CategoryId


def website_entry(plugin, item_id):
    """
    First executed function after website_bridge
    """
    return root(plugin, item_id)


def root(plugin, item_id):
    """Add modes in the listing"""
    categories_html = urlquick.get(
        URL_CATEGORIES).text
    categories_js_id = re.compile(
        r'compiled\/showcase_bottom.min\.js\?version=(.*?)\"').findall(categories_html)[0]
    categories_js_html = urlquick.get(
        URL_JS_CATEGORIES % categories_js_id).text
    list_categories = re.compile(
        r'\!0\,playlistId\:\"(.*?)\"').findall(categories_js_html)

    for category_id in list_categories:

        data_categories_json = urlquick.get(
            URL_VIDEOS_JSON % category_id).text
        data_categories_jsonparser = json.loads(data_categories_json)
        category_name = data_categories_jsonparser["title"]

        item = Listitem()
        item.label = category_name

        item.set_callback(
            list_videos,
            item_id=item_id,
            category_id=category_id)
        yield item


@Route.register
def list_videos(plugin, item_id, category_id):
    """Build videos listing"""
    replay_episodes_json = urlquick.get(
        URL_VIDEOS_JSON % category_id).text
    replay_episodes_jsonparser = json.loads(replay_episodes_json)

    for episode in replay_episodes_jsonparser["playlist"]:
        item = Listitem()

        item.label = episode["title"]
        video_url = episode["sources"][0]["file"]
        item.art['thumb'] = episode["image"]
        item.info['info'] = episode["description"]

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_url=video_url,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_url=video_url)
        yield item


@Resolver.register
def get_video_url(
        plugin, item_id, video_url, download_mode=False, video_label=None):
    """Get video URL and start video player"""
    if download_mode:
        return download.download_video(video_url, video_label)

    return video_url
