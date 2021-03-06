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

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import resolver_proxy

from bs4 import BeautifulSoup as bs

import re
import urlquick

# TODO
# Add more button

URL_LIVE_BFM_PARIS = 'http://www.bfmtv.com/mediaplayer/live-bfm-paris/'

URL_REPLAY_BFMPARIS = 'https://www.bfmtv.com/mediaplayer/videos-bfm-paris/'


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    item = Listitem()
    item.label = plugin.localize(LABELS['All videos'])
    item.set_callback(
        list_videos,
        item_id=item_id)
    yield item


@Route.register
def list_videos(plugin, item_id):

    resp = urlquick.get(
        URL_REPLAY_BFMPARIS,
        headers={'User-Agent': web_utils.get_random_ua})
    videos_soup = bs(resp.text, 'html.parser')
    list_videos_datas = videos_soup.find_all(
        'article',
        class_=re.compile('art-c modulx3'))
    for video_datas in list_videos_datas:
        if 'https' not in video_datas.find('a')['href']:
            video_url = 'https:' + video_datas.find('a')['href']
        else:
            video_url = video_datas.find('a')['href']
        video_image = video_datas.find('img')['data-original']
        video_title = video_datas.find('img')['alt']

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

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

    resp = urlquick.get(video_url)

    data_account = re.compile(
        r'data-account="(.*?)"').findall(resp.text)[0]
    data_video_id = re.compile(
        r'data-video-id="(.*?)"').findall(resp.text)[0]
    data_player = re.compile(
        r'data-player="(.*?)"').findall(resp.text)[0]

    return resolver_proxy.get_brightcove_video_json(
        plugin,
        data_account,
        data_player,
        data_video_id,
        download_mode,
        video_label)


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    resp = urlquick.get(
        URL_LIVE_BFM_PARIS,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)

    live_soup = bs(resp.text, 'html.parser')
    data_live_soup = live_soup.find(
        'div', class_='next-player')
    data_account = data_live_soup['data-account']
    data_video_id = data_live_soup['data-video-id']
    data_player = data_live_soup['data-player']
    return resolver_proxy.get_brightcove_video_json(
        plugin,
        data_account,
        data_player,
        data_video_id)
