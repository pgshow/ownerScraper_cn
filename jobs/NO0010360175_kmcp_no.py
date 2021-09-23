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
            html = fc.fetch(url='https://www.kmcp.no/en/investors/the+share')

            if not html:
                raise Exception('Get html failed')

            soup = BeautifulSoup(html, 'lxml')

            # get the holders
            data_list1 = []
            for idx, tr in enumerate(soup.select('div.shareholders-list > div')):
                tds = tr.find_all('div')

                if idx == len(soup.select('div.shareholders-list > div')) - 1:
                    # the last one is total info
                    data_list1.append({
                        'shareholder_name': tds[1].contents[0],
                        'number_of_shares': tds[3].contents[0],
                        'percent_of_total': tds[2].contents[0],
                    })
                else:
                    data_list1.append({
                        'shareholder_name': tds[0].contents[0],
                        'number_of_shares': tds[4].contents[0],
                        'percent_of_total': tds[3].contents[0],
                    })

            data = data_list1

            table = pandas.DataFrame.from_dict(data, orient='columns')

            update_str = fc.update(item[1], html, "-//p[contains(text(), 'Last updated: ')]")

            fc.end(table, item, update=update_str)

        except Exception as e:
            logger.error(f'{e}')
            fc.end_err(item, err_info=e)


