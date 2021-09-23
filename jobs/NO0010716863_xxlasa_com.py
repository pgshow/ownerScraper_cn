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
            html = fc.fetch(url='http://xxlasa.com/investor/the-share/top-20-shareholders/')

            if not html:
                raise Exception('Get html failed')

            soup = BeautifulSoup(html, 'lxml')

            # get the first table
            data_list1 = []
            for idx, tr in enumerate(soup.select('tbody > tr')):
                if idx == 0 or idx == 1:
                    continue

                tds = tr.find_all('td')

                if tds[3].contents[0].strip() == "":
                    break

                data_list1.append({
                    'No.': tds[0].contents[0].strip(),
                    'number_of_shares': tds[1].contents[0].strip(),
                    'percent_of_total': tds[2].contents[0].strip(),
                    'shareholder_name': tds[3].contents[0].strip(),
                    'Account': tds[4].contents[0].strip(),
                    'Nationality': tds[5].contents[0].strip(),
                })

            table1 = pandas.DataFrame.from_dict(data_list1, orient='columns')

            # get the second table
            data_list2 = []
            for idx, tr in enumerate(soup.select('tbody > tr')):
                tds = tr.find_all('td')

                if tds[5].contents[0].strip() != "":
                    # ignore upper table's information
                    continue

                if not tds[3].contents[0].strip() or 'shareholder' in tds[3].contents[0].lower():
                    continue

                data_list2.append({
                    'No.': tds[0].contents[0].strip(),
                    'number_of_shares': tds[1].contents[0].strip(),
                    'percent_of_total': tds[2].contents[0].strip(),
                    'shareholder_name': tds[3].contents[0].strip(),
                    'Nationality': tds[4].contents[0].strip(),
                })

            table2 = pandas.DataFrame.from_dict(data_list2, orient='columns')

            soup = BeautifulSoup(html, 'lxml')
            date_list = soup.select_one('section.entry-content > p:nth-child(3)').text.split('–')

            update_str1 = fc.update(item[1], date_list[0], 9)
            update_str2 = fc.update(item[1], date_list[1], 9)

            fc.end(table1, item, update=update_str1, suffix=1, stock_type='Major shareholders from shareholder register')
            fc.end(table2, item, update=update_str2, suffix=2, stock_type='Major shareholders from beneficial ownership')

        except Exception as e:
            logger.error(f'{e}')
            fc.end_err(item, err_info=e)


