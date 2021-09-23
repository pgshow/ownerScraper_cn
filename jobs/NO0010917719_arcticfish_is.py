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
            html = fc.fetch(url='https://www.arcticfish.is/investor-relations/')

            if not html:
                raise Exception('Get html failed')

            soup = BeautifulSoup(html, 'lxml')

            # get the holders
            data_list1 = []
            for idx, tr in enumerate(soup.select('div[class="et_pb_module dvmd_table_maker dvmd_table_maker_2"]  div[class="dvmd_tm_tblock dvmd_tm_rblock"]')):
                tds = tr.find_all('div')

                data_list1.append({
                    'No.': fc.simple_clear_html(tds[0].contents[0]),
                    'shareholder_name': fc.simple_clear_html(tds[3].contents[0]),
                    'percent_of_total': fc.simple_clear_html(tds[6].contents[0]),
                })

            data = data_list1

            table = pandas.DataFrame.from_dict(data, orient='columns')

            update_str = fc.update(item[1], html, "-//h2[contains(text(), 'Updated ')]")

            fc.end(table, item, update=update_str)

        except Exception as e:
            logger.error(f'{e}')
            fc.end_err(item, err_info=e)


