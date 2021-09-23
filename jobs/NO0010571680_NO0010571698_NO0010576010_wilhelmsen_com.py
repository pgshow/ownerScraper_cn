#!/usr/bin/python
# -*- coding: UTF-8 -*-
import time

from loguru import logger
import fc
import pandas
import pluginBase
from bs4 import BeautifulSoup


class SubPlugin(pluginBase.Plugin):
    """
    include 3 project and each project has 2 tables
    """
    def __init__(self):
        super().__init__()

    def run_job(self, item):
        logger.info(f"Start the plugin")
        self.crawl(item)

    def crawl(self, item):
        try:
            html1 = fc.chrome(url='https://ir.asp.manamind.com/products/html/shareholders.do;jsessionid=F6C100B25DA9D92FC44562D894BBC061?key=wilhelmsen_std&lang=en')

            time.sleep(30)

            html2 = fc.chrome(url='https://ir.asp.manamind.com/products/html/shareholders.do;jsessionid=EC529F1BEA96B528480B81482F8667CF?key=wilhB_std&lang=en')

            if 'table' not in html1 or 'table' not in html2:
                raise Exception(f"Can't find table in {item[1]} - {item[0]}")

            table1 = fc.extract_table(html1, [0])
            table2 = fc.extract_table(html2, [0])

            update_str1 = fc.update(item[1], html1, "-p.updated")
            update_str2 = fc.update(item[1], html2, "-p.updated")

            key = ["Investor", "Number of shares", "% of total"]

            table1 = fc.set_key_names(table1, key)
            table1 = fc.clear_table(item[1], table1)

            table2 = fc.set_key_names(table2, key)
            table2 = fc.clear_table(item[1], table2)

            fc.end(table1, item, update=update_str1, suffix=1, stock_type='Class A')
            fc.end(table2, item, update=update_str2, suffix=1, stock_type='Class B')

        except Exception as e:
            logger.error(f'{e}')
            fc.end_err(item, err_info=e)


