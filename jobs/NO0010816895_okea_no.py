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
            html = fc.chrome(url='https://www.okea.no/investor/share-information/')

            if not html:
                raise Exception('Get html failed')

            soup = BeautifulSoup(html, 'lxml')

            # get the holders
            data_list1 = []
            for idx, tr in enumerate(soup.select('div.shareholders-table > div.shareholder')):
                tds = tr.find_all('div')
                data_list1.append({
                    'shareholder_name': tds[0].contents[2].strip(),
                    'number_of_shares': tds[2].contents[2].strip(),
                    '% of Top 20': tds[4].contents[2].strip(),
                    'percent_of_total': tds[6].contents[2].strip(),
                    'Type': tds[8].contents[2].strip(),
                    'Country': tds[10].contents[2].strip(),
                })

            data = data_list1

            table = pandas.DataFrame.from_dict(data, orient='columns')

            update_str = ''

            fc.end(table, item, update=update_str)

        except Exception as e:
            logger.error(f'{e}')
            fc.end_err(item, err_info=e)


