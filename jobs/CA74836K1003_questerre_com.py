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
            html = fc.fetch(url='https://www.questerre.com/investor-centre/shareholder-information/')

            if not html:
                raise Exception('Get html failed')

            soup = BeautifulSoup(html, 'lxml')

            # get the holders
            data_list1 = []
            for idx, tr in enumerate(soup.select('div.elementor.elementor-23  div.elementor-widget-container  section[data-element_type="section"]')):
                tds = tr.select('p')

                data_list1.append({
                    'shareholder_name': fc.simple_clear_html(tds[0].contents[0]),
                    'number_of_shares': fc.simple_clear_html(tds[1].contents[0]),
                })

            data = data_list1

            table = pandas.DataFrame.from_dict(data, orient='columns')

            update_str = ''

            fc.end(table, item, update=update_str)

        except Exception as e:
            logger.error(f'{e}')
            fc.end_err(item, err_info=e)


