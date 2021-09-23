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
            html = fc.chrome(url='https://irs.tools.investis.com/clients/fi/anora/shareholder/ShareHolder.html?culture=en-US')

            if not html:
                raise Exception('Get html failed')

            soup = BeautifulSoup(html, 'lxml')

            # get the holders
            data_list1 = []
            for idx, tr in enumerate(soup.find_all('div', {'class': 'parent-cmpny'})):
                tds = tr.find_all('span')

                if len(str(tds[2].contents[0])) <= 5:
                    # get the holders
                    data_list1.append({
                        'no.': tds[2].contents[0],
                        'shareholder_name': tds[3].contents[0],
                        'number_of_shares': tds[7].contents[0],
                        'percent_of_total': tds[11].contents[0],
                        'Change': tds[15].contents[0].strip(),
                        'Change %': tds[19].contents[0].strip(),
                        'Market value (EUR)': tds[23].contents[0],
                    })
                else:
                    # get the total amount
                    data_list1.append({
                        'no.': None,
                        'shareholder_name': tds[2].contents[0],
                        'number_of_shares': tds[6].contents[0],
                        'percent_of_total': tds[10].contents[0],
                        'Change': tds[14].contents[0].strip(),
                        'Change %': tds[18].contents[0].strip(),
                        'Market value (EUR)': tds[22].contents[0],
                    })

            data = data_list1

            table = pandas.DataFrame.from_dict(data, orient='columns')

            update_str = fc.update(item[1], html, "span.ui-selectmenu-text")

            fc.end(table, item, update=update_str)

        except Exception as e:
            logger.error(f'{e}')
            fc.end_err(item, err_info=e)


