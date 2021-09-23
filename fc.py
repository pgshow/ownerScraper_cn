#!/usr/bin/python
# -*- coding: UTF-8 -*-

import datetime
import json
import re
import time

import config
import pandas
import copy
import requests
from lxml import etree
from loguru import logger
from retry import retry
from func_timeout import func_set_timeout
from date_extractor import extract_dates
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium_stealth.selenium_stealth import stealth

"""
For the excel profile use
"""


def extract_table(html, sub_num):
    """
    extract tables, tables will combine into one
    """
    tables = pandas.read_html(html, thousands="ª", decimal="ª")

    # converters = {key: str for key in keys}
    # transfer all 3 columns to string
    # tables = pandas.read_html(html, thousands="ª", decimal="ª", converters=converters)
    # tables = pandas.read_html(html)
    return tables[sub_num[0]]


def update(isin, html, rule):
    # change to xpath selector
    soup = BeautifulSoup(html, 'lxml')
    time_str = ""

    def month_start():
        this_month_start = str(datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, 1))
        return clear_make_date(this_month_start)

    def extract_single_update():
        """if only have one date in the page"""
        page_text = soup.get_text()
        text = re.search(r'(updated|Sist oppdatert):? ?([\d./-]+)', page_text, re.I).group(2)

        return clear_make_date(text)

    def extract_single_american_style_date():
        """if only have one date in the page and the month is english"""
        page_text = soup.get_text()
        text = re.search(
            r'(((January|February|March|April|May|June|July|August|September|October|November|December)|((Jan|Feb|Mar|Apr|Aug|Sept|Oct|Nov|Dec)(\.?)))([, ]?)(\d+)((st|nd|rd|th)?)([, ]?)(\d{2,}))',
            page_text, re.I).group(1)

        return clear_make_date(text)

    def extract_by_rule():
        """extract if there has selector rule"""

        rule2 = copy.deepcopy(rule)

        if rule.startswith('-'):
            # remove '-' prefix from the rule
            rule2 = rule2[1:]

        select_time = soup.select(rule2)
        text = select_time[0].get_text()

        if rule.startswith('-'):
            text = re.sub(r'(\d{1,2})[ ,.-](\d{1,2})[ ,.-](\d{2,4})', r"\g<2>.\g<1>.\g<3>", text)  # change the order for date and month, like 31.08.2021

        return clear_make_date(text)

    def extract_by_xpath_style1():
        """extract if there has xpath rule, month first, style 2010-10-30 10.30.21"""
        selector = etree.HTML(html)  # html to etree object
        text = selector.xpath(rule)[0].text

        return clear_make_date(text)

    def extract_by_xpath_style2():
        """extract if there has xpath rule, month is behind day, the style 31.03.21"""
        selector = etree.HTML(html)  # html to etree object
        rule2 = rule[1:]
        text = selector.xpath(rule2)[0].text

        text = re.sub(r'(\d{1,2})[ ,.-](\d{1,2})[ ,.-](\d{2,4})', r"\g<2>.\g<1>.\g<3>", text)  # change the order for date and month, like 31.08.2021

        return clear_make_date(text)

    def clear_make_date(text):
        # clear for date
        text = re.sub(r'([1-3]?[0-9])th of (\w{3,10})', r"\g<1>th \g<2>", text)  # for [ Shareholders as of 30th of July 2021 ]

        text = re.sub(r'([1-3]?[0-9])\. (January|February|March|April|May|June|July|August|September|October|November|December) (202\d)', r"\g<1> \g<2> \g<3>",
                      text)  # for style 14. September 2021

        text = re.sub(r'([1-3]?\d)st', r"\g<1>", text)
        text = re.sub(r'([1-3]?\d)th', r"\g<1>", text)

        # extract date
        date = extract_dates(text)[0]
        return date

    try:
        if rule == 0:
            # no update in the page
            return ""
        elif rule == 1:
            time = extract_single_update()
        elif rule == 2:
            time = extract_single_american_style_date()
        elif rule == 9:
            # directly get the data without extraction
            time = clear_make_date(html)
        elif rule == 'MONTH_START':
            time = month_start()
        elif rule.startswith('//'):
            time = extract_by_xpath_style1()
        elif rule.startswith('-//'):
            time = extract_by_xpath_style2()
        else:
            time = extract_by_rule()

        time_str = time.strftime('%Y-%m-%d')
    except Exception as e:
        logger.error(isin + ' find update error:', e)
        pass

    return time_str


def column_mul(table, factor):
    column = factor[0]
    multiplier = factor[1]
    table[column] = table[column].map(lambda x: x * multiplier)
    return table


def replace_text(text, old_new):
    """
    replace the text
    """
    return text.replace(old_new[0], old_new[1])


def del_by_match_str(table, *s):
    for word in s:
        table.drop(word)
    return table


def del_rows_front(table, n):
    """
    remove some rows from the head
    2 means remove the last two
    """
    table.drop(table.head(n).index, inplace=True)
    return table


def del_rows_end(table, n):
    """
    remove some rows from the end
    2 means remove the last two
    """
    table.drop(table.tail(n).index, inplace=True)
    return table


def del_columns(table, columns):
    """
    could del the specific column by index, accept str or list, example: 0, [0, 1, 2]
    """
    if isinstance(columns, list):
        table = table.drop(table.columns[columns], axis=1)
    else:
        columns_list = [columns]
        table = table.drop(table.columns[columns_list], axis=1)
    return table


def del_columns_end(table, n):
    table = table.iloc[:, :-n]
    return table


def del_columns_by_name(table, *columns):
    return table.drop(list(columns), axis=1)


def set_key_names(table, key_names):
    profile = {}
    # make columns profile to change the words of them
    for i in range(len(key_names)):
        profile[key_names[i]] = config.TABLE_MAIN_KEYS[i]

    table.rename(columns=profile, inplace=True)

    return table


def end(table, item_profile, update, suffix=None, stock_type=None):
    """
    save the table to a json
    """

    table = modify_numbers(table)

    table_json = table.to_json(orient="records", force_ascii=False)
    table_data = json.loads(table_json)

    data = {
        "ticker": item_profile[2],
        "scrape_date": datetime.datetime.now().strftime('%Y-%m-%d'),
        "scrape_url": item_profile[3],
        "shareholder_update": update,
        "shareholders ": table_data,
        "stock_type": stock_type,
        "error": None
    }

    s = json.dumps(data)

    if not suffix:
        path = f"result/{item_profile[2]}_{item_profile[1]}_{datetime.datetime.now().strftime('%Y-%m-%d')}.json"
    else:
        # special suffix for the file
        path = f"result/{item_profile[2]}_{item_profile[1]}_{datetime.datetime.now().strftime('%Y-%m-%d')}_{suffix}.json"

    with open(path, 'w') as f:
        f.write(s)
        f.close()


def end_err(item_profile, err_info):
    """
    save the error to a json
    """
    data = {
        "ticker": item_profile[2],
        "scrape_date": datetime.datetime.now().strftime('%Y-%m-%d'),
        "scrape_url": item_profile[3],
        "shareholder_update": None,
        "shareholders ": None,
        "stock_type": None,
        "error": str(err_info)
    }

    s = json.dumps(data)
    path = f"result/{item_profile[2]}_{item_profile[1]}_{datetime.datetime.now().strftime('%Y-%m-%d')}_error.json"
    with open(path, 'w') as f:
        f.write(s)
        f.close()


def modify_numbers(table):
    # table = table.apply(gender_map, axis=1)
    for index, row in table.iteritems():
        table[index] = table[index].map(gender_map)

    return table


def gender_map(x):
    if not x:
        return x

    x = simple_clear_html(x)

    if isinstance(x, int):
        # 整数转带千分位字符串
        x = "{:,}".format(x)
    elif isinstance(x, float):
        # 浮点数转带千分位字符串
        x = "{:,}".format(x)
    else:
        # 值为字符串的情况
        # 1.拥有量，大于1000的数
        if re.match(r'^\d{1,3}?([. ]\d{3})+$', x):
            # 千分号数字，分隔符（空格和点）
            if re.match(r'[,.]\d{2}$', x):
                # 有小数结尾的千分数需要先取整数部分
                x = x[:-3]

            x = x.replace('.', '')
            x = x.replace(' ', '')

            x = int(x)
            x = "{:,}".format(x)
        # 2.带 % 的百分数 和使用逗号或点分割的浮点数
        elif re.match(r'^[\d., \u00a0]+%$', x) or re.match(r'^\d{1,2}[,.]\d{1,2}$', x):
            x = x.replace('%', '')
            x = x.replace(' ', '')
            x = x.replace('\u00a0', '')
            x = x.replace(',', '.')
            x = str(float(x))
        elif re.match(r'^\d{1,2}\.\d{3,}$', x):
            # 小于100，小数点3位后的浮点数
            # x = str(float(x))
            pass
        elif re.match(r'^\d+$', x):
            # 直接的整数字符串
            x = "{:,}".format(int(x))

    return x


"""
common functions
"""


# clear the table
def clear_table(isin, table):
    exclude_words = ['Investor', 'Total', 'OTHER', 'Top 20', 'shareholder', 'Name']
    try:
        # remove the empty
        table = table.drop(index=table.loc[(table['shareholder_name'].isna())].index)
        table = table.reset_index(drop=True)

        # remove the top row if the shareholder_name include these words
        while is_contain_words(table.iloc[0]['shareholder_name'], exclude_words):
            table = table.drop(index=0)
            table = table.reset_index(drop=True)

        # table = table.drop(index=table.loc[(table['shareholder_name'].str.contains('Investor|Total|OTHER|Top 20|shareholder|Name', case=False))].index)
    except Exception as e:
        logger.error(isin + ' clear table error:', e)
        pass

    # table = table.drop(['Total'], axis=0)
    # table = table.drop(['OTHER'], axis=0)
    # table = table.drop(['Total number owned by top 20'], axis=0)
    # table = table.drop(['Total number of shares'], axis=0)

    return table


# time change to string
def time2str(t):
    return t.strftime('%Y-%m-%d %H_%M_%S')


def fetch_url(url):
    return fetch(url)


@retry(tries=5, delay=10, backoff=2, max_delay=120)
def fetch(url, headers=None):
    if not isinstance(headers, dict):
        headers = dict()

    r = get(url, headers)

    if r.status_code != 200:
        logger.error(f"Fetch {r.url} failed, {r.status_code}")
        return

    return r.text


@func_set_timeout(120)
def get(url, headers):
    headers['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
    return requests.get(url=url, headers=headers, timeout=60, allow_redirects=False)


def chrome_url(url):
    return chrome(url)


def chrome(url):
    """
    Get html by selenium
    """
    options = webdriver.ChromeOptions()
    init_base_cap(options)

    driver = webdriver.Chrome(r"C:\chromedriver.exe", options=options)
    add_stealth_js(driver)

    driver.get(url)

    # time.sleep(5)
    time.sleep(20)

    # WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, '//table')))
    # time.sleep(2)

    html = driver.page_source
    driver.quit()

    return html


def init_base_cap(options):
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-impl-side-painting")
    options.add_argument("--disable-accelerated-2d-canvas")
    options.add_argument("--disable-accelerated-jpeg-decoding")
    options.add_argument("--test-type=ui")
    options.add_argument("--ignore-certificate-errors")

    prefs = {
        'profile.default_content_setting_values': {
            'images': 2,
            'permissions.default.stylesheet': 2,
        }
    }
    options.add_experimental_option("prefs", prefs)


def add_stealth_js(driver):
    stealth(driver,
            languages=["en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Google Inc. (NVIDIA)",
            renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11-27.21.14.7005)",
            fix_hairline=True,
            )


# if string contain any of the words
def is_contain_words(text, words):
    for word in words:
        if word in text.casefold():
            return True


def simple_clear_html(text):
    dr = re.compile(r'<[^>]+>', re.S)
    return dr.sub('', str(text))

