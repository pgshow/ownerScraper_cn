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
            html = fc.chrome(url='https://ir.q4europe.com/Solutions/Europris/3742/shareholders.aspx?initialWidth=1160&childId=pym-shareholder&parentTitle=Europris%20ASA%20-%20Share%20Information%20-%20Share%20Information&parentUrl=https%3A%2F%2Finvestor.europris.no%2Fshare-information%2Fshare-information%2Fdefault.aspx')

            if not html:
                raise Exception('Get html failed')

            soup = BeautifulSoup(html, 'lxml')

            # get the holders
            data_list1 = []
            for idx, tr in enumerate(soup.find_all('div', {'class': 'shareholders-content_item grid--no-gutter'})):
                tds = tr.find_all('span')
                data_list1.append({
                    'shareholder_name': tds[0].contents[0],
                    'number_of_shares': tds[1].contents[0],
                    '% of Top 20': tds[2].contents[0],
                    'percent_of_total': tds[3].contents[0],
                    'Type': tds[4].contents[0],
                    'Country': tds[5].contents[0],
                })

            # get the total amount
            data_list2 = []
            update_cell = None
            for idx, tr in enumerate(soup.find_all('div', {'class': 'shareholders-totals_item grid--no-gutter'})):
                tds = tr.find_all('span')

                if idx == 2:
                    update_cell = str(tds[1].contents[0])  # the update time is in the last row
                    continue

                data_list2.append({
                    'shareholder_name': tds[0].contents[0],
                    'number_of_shares': tds[1].contents[0],
                })

            data = data_list1 + data_list2

            table = pandas.DataFrame.from_dict(data, orient='columns')

            update_str = fc.update(item[1], update_cell, 9)

            fc.end(table, item, update=update_str)

        except Exception as e:
            logger.error(f'{e}')
            fc.end_err(item, err_info=e)


