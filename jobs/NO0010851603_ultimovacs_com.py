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
        logger.info(f"Start the plugin: {self.__module__}")
        self.crawl(item)

    def crawl(self, item):
        try:
            html = fc.fetch(url='https://ultimovacs.com/investors/share-information')

            if not html:
                raise Exception('Get html failed')

            soup = BeautifulSoup(html, 'lxml')

            # get the holders
            data_list1 = []
            for idx, tr in enumerate(soup.select('div.shareholder')):
                if idx == 0:
                    continue

                tds = tr.find_all('span')

                data_list1.append({
                    'shareholder_name': fc.simple_clear_html(tds[0].contents[0]),
                    'number_of_shares': fc.simple_clear_html(tds[1].contents[0]),
                    'percent_of_total': fc.simple_clear_html(tds[2].contents[0]),
                })

            data = data_list1

            table = pandas.DataFrame.from_dict(data, orient='columns')

            update_str = fc.update(item[1], html, r'p.shareholder-date-modified')

            fc.end(table, item, update=update_str)

        except Exception as e:
            logger.error(f'{e}')
            fc.end_err(item, err_info=e)


