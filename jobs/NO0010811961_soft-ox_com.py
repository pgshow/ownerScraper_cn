#!/usr/bin/python
# -*- coding: UTF-8 -*-

from loguru import logger
import fc
import pandas
import pluginBase
from bs4 import BeautifulSoup


class SubPlugin(pluginBase.Plugin):
    def __init__(self):
        super().__init__()

    def run_job(self, item):
        logger.info(f"Start the plugin")
        self.crawl(item)

    def crawl(self, item):
        try:
            html = fc.fetch(url='https://soft-ox.com/largest-shareholders/')

            if not html:
                raise Exception('Get html failed')

            soup = BeautifulSoup(html, 'lxml')

            # get the holders
            data_dict = {'shareholder_name': [], 'Investor ID': [], 'percent_of_total': [], 'number_of_shares': []}
            rules = ['div.tm-row-inner > div:nth-child(1) span.tm-list-li-content',
                     'div.tm-row-inner > div:nth-child(2) span.tm-list-li-content',
                     'div.tm-row-inner > div:nth-child(3) span.tm-list-li-content',
                     'div.tm-row-inner > div:nth-child(4) span.tm-list-li-content', ]

            for column in soup.select(rules[0]):
                data_dict['shareholder_name'].append(column.contents[0].strip())

            for column in soup.select(rules[1]):
                data_dict['Investor ID'].append(column.contents[0].strip())

            for column in soup.select(rules[2]):
                data_dict['number_of_shares'].append(column.contents[0].strip())

            for column in soup.select(rules[3]):
                data_dict['percent_of_total'].append(column.contents[0].strip())

            data = data_dict

            table = pandas.DataFrame(data)
            table = fc.del_rows_front(table, 1)

            update_str = fc.update(item[1], html, "//h2[contains(text(), 'shareholders as of')]")

            fc.end(table, item, update=update_str)

        except Exception as e:
            logger.error(f'{e}')
            fc.end_err(item, err_info=e)


