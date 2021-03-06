# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2018  SylvainCecchetto

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
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download

from bs4 import BeautifulSoup as bs

import json
import urlquick

# TO DO
# Fix Video 404 / other type stream video (detect and implement)

URL_ROOT = 'https://abcnews.go.com'

# Stream
URL_LIVE_STREAM = URL_ROOT + '/video/itemfeed?id=abc_live11&secure=true'

URL_REPLAY_STREAM = URL_ROOT + '/video/itemfeed?id=%s'
# videoId


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_programs(plugin, item_id)


@Route.register
def list_programs(plugin, item_id):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_ROOT)
    root_soup = bs(resp.text, 'html.parser')
    list_programs_datas = root_soup.find(
        'div', class_='shows-dropdown').find_all('li')

    for program_datas in list_programs_datas:
        program_title = program_datas.find('span', class_='link-text').text
        program_url = program_datas.find('a').get('href')

        item = Listitem()
        item.label = program_title
        item.set_callback(
            list_videos,
            item_id=item_id,
            program_url=program_url)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url):

    resp = urlquick.get(program_url)
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = {}
    if root_soup.find(
            'article', class_='carousel-item row-item fe-top'):
        list_videos_datas = root_soup.find(
            'article', class_='carousel-item row-item fe-top').find_all(
                'div', class_='item')

    for video_datas in list_videos_datas:
        video_title = ''
        if video_datas.find('img').get('alt'):
            video_title = video_datas.find(
                'img').get('alt').replace('VIDEO: ', '')
        video_image = video_datas.find('img').get('data-src')
        video_id = video_datas.find('figure').get('data-id')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            video_id=video_id,
            item_id=item_id,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_id=video_id)
        yield item


@Resolver.register
def get_video_url(
        plugin, item_id, video_id, download_mode=False, video_label=None):

    resp = urlquick.get(URL_REPLAY_STREAM % video_id)
    json_parser = json.loads(resp.text)
    stream_url = ''
    for stream_datas in json_parser["channel"]["item"]["media-group"]["media-content"]:
        if stream_datas["@attributes"]["type"] == 'application/x-mpegURL':
            stream_url = stream_datas["@attributes"]["url"]

    if download_mode:
        return download.download_video(stream_url, video_label)
    return stream_url


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    resp = urlquick.get(URL_LIVE_STREAM)
    json_parser = json.loads(resp.text)
    stream_url = ''
    for live_datas in json_parser["channel"]["item"]["media-group"]["media-content"]:
        if 'application/x-mpegURL' in live_datas["@attributes"]["type"]:
            if 'preview' not in live_datas["@attributes"]["url"]:
                stream_url = live_datas["@attributes"]["url"]
    return stream_url
