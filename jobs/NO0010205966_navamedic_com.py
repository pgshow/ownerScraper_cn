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
            html = fc.fetch(url='https://navamedic.com/investors/navamedic-share/shareholders/')

            if not html:
                raise Exception('Get html failed')

            soup = BeautifulSoup(html, 'lxml')

            # get the holders
            data_dict = {'shareholder_name': [], 'percent_of_total': [], 'number_of_shares': []}
            rules = ['div[class="small-4 large-4 col-1 col-comm shareholder-line"]',
                     'div[class="small-4 large-4 col-2 col-comm"]',
                     'div[class="small-4 large-4 col-3 col-comm"]', ]

            for column in soup.select(rules[0]):
                data_dict['shareholder_name'].append(column.contents[0].strip())

            for column in soup.select(rules[1]):
                data_dict['percent_of_total'].append(column.contents[0].strip())

            for column in soup.select(rules[2]):
                data_dict['number_of_shares'].append(column.contents[0].strip())

            data = data_dict

            table = pandas.DataFrame(data)

            update_str = ''

            fc.end(table, item, update=update_str)

        except Exception as e:
            logger.error(f'{e}')
            fc.end_err(item, err_info=e)


