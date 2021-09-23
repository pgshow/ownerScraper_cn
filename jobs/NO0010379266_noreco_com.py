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
            html = fc.fetch(url='https://www.noreco.com/the-noreco-share')

            if not html:
                raise Exception('Get html failed')

            soup = BeautifulSoup(html, 'lxml')

            # get the holders
            data_list1 = []
            for idx, tr in enumerate(soup.select('ul#table-3 > li')):
                if idx == 0:
                    continue

                tds = tr.find_all('span')

                if len(tds) != 3:
                    continue

                data_list1.append({
                    'shareholder_name': tds[0].contents[0].strip(),
                    'number_of_shares': tds[1].contents[0].strip(),
                    'percent_of_total': tds[2].contents[0].strip(),
                })

            data = data_list1

            table = pandas.DataFrame.from_dict(data, orient='columns')

            update_str = fc.update(item[1], html, "//div[contains(text(), 'shareholders of Noreco as of')]")

            fc.end(table, item, update=update_str)

        except Exception as e:
            logger.error(f'{e}')
            fc.end_err(item, err_info=e)


