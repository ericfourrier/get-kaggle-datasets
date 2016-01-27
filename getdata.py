#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: efourrier

Purpose : This quick program is designed to download all competions infos on
Kaggle
"""

# Import Packages
import requests
from lxml import html
import re
import time
import pandas as pd


# Constant Variables
regex_size = re.compile(r"\(([a-z 0-9\.]+)\)")
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36'
headers = {'user_agent': user_agent, 'X-Requested-With': 'XMLHttpRequest'}
base_url = 'https://www.kaggle.com'


def generate_urls(competitions_name):
    """ Generate urls containing data from competition names """
    return [generate_url(name) for name in competitions_name]


def get_last(l, default=''):
    """ pop from list and return default if empty list  """
    return l.pop() if len(l) else default

class GetCompetitions(object):
    """ Donwload the full list of competitions on kaggle without """
    def __init__(self):
        self.base_url = 'https://www.kaggle.com'
        self.url_competitions = 'https://www.kaggle.com/competitions/search'
        self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36'
        self.headers = {'user_agent': self.user_agent, 'X-Requested-With': 'XMLHttpRequest'}
        self.payload_c = {'Query': None, 'RewardColumnSort': 'Descending', 'SearchVisibility': 'AllCompetitions',
                           'ShowActive': True, 'ShowCompleted': True, 'ShowProspect': True,
                           'ShowOpenToAll': True, 'ShowPrivate': False, 'ShowLimited': False}
        self.mapping_number = {'kb': 1e3, 'mb': 1e6, 'gb': 1e9}
        self.regex_decimal = re.compile("[0-9]*[\.,]?[0-9]?[0-9]")
        self.regex_competition = re.compile("^https:\/\/www\.kaggle\.com\/c\/([^\/]*)\/")

    def string_to_number(self,s):
            """ Convert string number like '3.1 mb' to the correct float here 3100 based on
            a mapping """
            str_number = self.regex_decimal.search(s).group(0)
            str_number = str_number.replace(',', '.')
            nb = float(str_number)
            regex_mapper = re.compile('|'.join(['(' + k + ')' for k in self.mapping_number.keys()]))
            match = regex_mapper.search(s)
            if match is not None:
                return self.mapping_number[match.group(0)] * nb
            else:
                return nb
    @staticmethod
    def generate_url(name):
        """ Generate url of competition from competition name """
        return 'https://www.kaggle.com/c/{}/data'.format(name)

    def get_competition_name(self, headers=headers):
        """ Get all the competitions name from kaggle """
        competition_page = requests.get(self.url_competitions, params=self.payload_c,
                                        headers=self.headers)
        tree = html.fromstring(competition_page.text)
        list_competitions = tree.xpath('//table[@id="competitions-table"]//tr//td[1]/a/@href')
        # keep only clean competitions
        competitions_name = [s.replace('/c/', '')for s in list_competitions if s.startswith('/c/')]
        return competitions_name

    def get_dataset_url(self, name):
        """ Get a dataset url with some basic infos from a name """
        url = self.generate_url(name)
        page = requests.get(url, headers=self.headers)
        tree = html.fromstring(page.text)
        rows = tree.xpath('//table[@id="data-files"]//tbody')
        list_datasets = []
        for row in rows:
            filename = get_last(row.xpath('.//td[@class="file-name"]/text()'))
            for link in row.xpath('.//td[2]//a'):
                dataset = {}
                dataset['competition_name'] = name
                dataset['filename'] = filename
                dataset['url'] = base_url + get_last(link.xpath('./@href'))
                dataset['name'] = get_last(link.xpath('./@name'))
                dataset['size'] = regex_size.search(get_last(link.xpath('./text()'))).group(1)
                list_datasets.append(dataset)
        return list_datasets

    def get_all_datasets(self, output='DataFrame',random_delay=None):
        """ Get all infos about kaggle datasets """
        list_total_datasets = []
        competition_names = self.get_competition_name()
        for name in competition_names:
            try:
                list_total_datasets += self.get_dataset_url(name)
                print('Infos about datasets from {} downloaded'.format(name))
                if random_delay is not None and isinstance(random_delay,int):
                    time.sleep(random_delay)
            except Exception as e:
                # bad but quick
                print(str(e))
                continue
        if output == 'DataFrame':
            return pd.DataFrame(list_total_datasets)
        else:
            return list_total_datasets

    def clean_dataset(self, df):
            """ Clean the pandas Dataframe of all kaggle datasets """
            df_c = df.copy() # create a copy
            # create extension column
            df_c.loc[:, 'extension'] = df_c.loc[:, 'name'].str.split('.').str[-1]
            # create size normalize column
            df_c.loc[:, 'size_n'] = df_c.loc[:, 'size'].map(lambda s: self.string_to_number(s))
            # create competition name
            df_c.loc[:, 'competition_name'] = df_c.loc[:, 'url'].str.extract(self.regex_competition)
            return df_c
