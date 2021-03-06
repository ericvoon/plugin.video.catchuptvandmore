# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Original work (C) JUL1EN094, SPM, SylvainCecchetto
    Copyright (C) 2016  SylvainCecchetto

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
from resources.lib import resolver_proxy

from bs4 import BeautifulSoup as bs

import re
import urlquick

# TO DO
# Get First-diffusion (date of replay Video)
# Add search button


URL_ROOT = 'https://www.publicsenat.fr'

URL_LIVE_SITE = URL_ROOT + '/direct'

URL_CATEGORIES = URL_ROOT + '/recherche/type/episode/field_theme/%s?sort_by=pse_search_date_publication'
# categoriesId


CATEGORIES = {
    'politique-4127': 'Politique',
    'societe-4126': 'Société',
    'debat-4128': 'Débat',
    'parlementaire-53511': 'Parlementaire'
}


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
    for category_id, category_name in CATEGORIES.iteritems():
        category_url = URL_CATEGORIES % category_id

        item = Listitem()
        item.label = category_name
        item.set_callback(
            list_videos,
            item_id=item_id,
            category_url=category_url,
            page='1')
        yield item


@Route.register
def list_videos(plugin, item_id, category_url, page):

    replay_paged_url = category_url + '&paged=' + page
    resp = urlquick.get(replay_paged_url)
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = root_soup.find_all(
        'div', class_=re.compile('views-row views-row-'))

    for video_datas in list_videos_datas:
        if len(video_datas.find_all('div', class_='wrapper-duree')) > 0:
            list_texts = video_datas.find_all('div', class_='field-item even')
            if len(list_texts)>2:
                video_title = list_texts[1].text + ' - ' + list_texts[2].text
            elif len(list_texts)>1:
                video_title = list_texts[1].text
            else:
                video_title = ''
            video_image = video_datas.find('img').get('src')
            video_plot = ''
            if len(list_texts)>3:
                video_plot = list_texts[3].text
            video_duration = int(video_datas.find_all('div', class_='wrapper-duree')[0].text[:-3]) * 60
            video_url = URL_ROOT + video_datas.find_all('a')[1].get('href')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = video_image
            item.info['duration'] = video_duration
            item.info['plot'] = video_plot

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

    yield Listitem.next_page(
        item_id=item_id,
        category_url=category_url,
        page=str(int(page) + 1))


@Resolver.register
def get_video_url(
        plugin, item_id, video_url, download_mode=False, video_label=None):

    resp = urlquick.get(
        video_url,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    video_id = re.compile(
        r'www.dailymotion.com/embed/video/(.*?)[\?\"]').findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(
        plugin, video_id, download_mode, video_label)


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    resp = urlquick.get(
        URL_LIVE_SITE,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    video_id = re.compile(
        r'www.dailymotion.com/embed/video/(.*?)[\?\"]').findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, video_id, False)
