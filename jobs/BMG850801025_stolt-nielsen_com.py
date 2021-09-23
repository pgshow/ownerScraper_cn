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
            html = fc.fetch(url='https://www.stolt-nielsen.com/en/investors/share-information/#')

            if not html:
                raise Exception('Get html failed')

            soup = BeautifulSoup(html, 'lxml')

            # the html struct is listed by P tag
            data_dict = {'shareholder_name': [], 'county': [], 'percent_of_total': [], 'number_of_shares': []}
            for key_id, td in enumerate(soup.select('main > table td')):
                ps = td.find_all('p')

                for p in ps:
                    if str(p.contents[0].strip()) == "":
                        continue

                    data_dict[list(data_dict.keys())[key_id]].append(
                        p.contents[0].strip(),
                    )

            data = data_dict

            table = pandas.DataFrame(data)

            update_str = fc.update(item[1], html, "//p[contains(text(), 'Limited, as at')]")

            fc.end(table, item, update=update_str)

        except Exception as e:
            logger.error(f'{e}')
            fc.end_err(item, err_info=e)
