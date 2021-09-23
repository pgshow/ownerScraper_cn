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
            html = fc.fetch(url='https://www.belships.com/annual-report-2017/financial-statements/consolidated/notes/note-20-equity/')

            if not html:
                raise Exception('Get html failed')

            soup = BeautifulSoup(html, 'lxml')

            # get the holders
            data_list1 = []
            for idx, tr in enumerate(soup.select('#main > div:nth-child(4) > table:nth-child(1) > tbody  tr')):
                tds = tr.find_all('td')

                if len(tds) == 3:
                    # total information
                    data_list1.append({
                        'shareholder_name': tds[0].contents[0],
                        'number_of_shares': tds[1].contents[0],
                        'percent_of_total': tds[2].contents[0],
                    })
                else:
                    data_list1.append({
                        'No.': tds[0].contents[0],
                        'shareholder_name': tds[1].contents[0],
                        'number_of_shares': tds[2].contents[0],
                        'percent_of_total': tds[3].contents[0],
                    })

            data = data_list1

            table = pandas.DataFrame.from_dict(data, orient='columns')

            update_str = fc.update(item[1], html, "//h5[contains(text(), ' ASA at ')]")

            fc.end(table, item, update=update_str)

        except Exception as e:
            logger.error(f'{e}')
            fc.end_err(item, err_info=e)


