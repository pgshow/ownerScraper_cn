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
            html = fc.fetch(url='https://www.the-kingfish-company.com/share-information')

            if not html:
                raise Exception('Get html failed')

            soup = BeautifulSoup(html, 'lxml')

            # get the holders
            data_list1 = []
            for idx, tr in enumerate(soup.select('div[role="gridcell"] div[data-testid="mesh-container-content"]')):
                tds = tr.find_all('p')

                if not tds or '%' not in str(tds[2].contents[0]):
                    continue

                data_list1.append({
                    'shareholder_name': fc.simple_clear_html(tds[0].contents[0]),
                    'number_of_shares': fc.simple_clear_html(tds[1].contents[0]),
                    'percent_of_total': fc.simple_clear_html(tds[2].contents[0]),
                })

            data = data_list1

            table = pandas.DataFrame.from_dict(data, orient='columns')

            update_str = fc.update(item[1], html, "//p[contains(text(), 'As of ')]")

            fc.end(table, item, update=update_str)

        except Exception as e:
            logger.error(f'{e}')
            fc.end_err(item, err_info=e)


