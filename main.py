#!/usr/bin/python
# -*- coding: UTF-8 -*-

import inspect
import json
import pkgutil
import os
import time
import fc
import pandas
from loguru import logger

import pluginBase
from pluginBase import Plugin
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED


class PluginCollection:
    def __init__(self, plugin_package):
        self.plugin_package = plugin_package
        self.reload_plugins()

    def reload_plugins(self):
        self.plugins = []
        self.seen_paths = []
        print()
        print(f">>> Find plugins in {self.plugin_package} package")
        print()
        self.walk_package(self.plugin_package)

    def get_all_plugins(self):
        return self.plugins

    def walk_package(self, package):
        imported_package = __import__(package, fromlist=['blah'])

        for _, pluginname, ispkg in pkgutil.iter_modules(imported_package.__path__, imported_package.__name__ + '.'):
            if not ispkg:
                plugin_module = __import__(pluginname, fromlist=['blah'])
                clsmembers = inspect.getmembers(plugin_module, inspect.isclass)
                for (_, c) in clsmembers:
                    if issubclass(c, Plugin) and (c is not Plugin):
                        print(f'        {c.__module__}.{c.__name__}')
                        self.plugins.append(c())

        all_current_paths = []
        if isinstance(imported_package.__path__, str):
            all_current_paths.append(imported_package.__path__)
        else:
            all_current_paths.extend([x for x in imported_package.__path__])

        for pkg_path in all_current_paths:
            if pkg_path not in self.seen_paths:
                self.seen_paths.append(pkg_path)

                child_pkgs = [p for p in os.listdir(pkg_path) if os.path.isdir(os.path.join(pkg_path, p))]
                for child_pkg in child_pkgs:
                    self.walk_package(package + '.' + child_pkg)


def run(item, plugins):
    try:
        # this part is only for debug
        # if isinstance(item[5], float) or '~' not in item[5]:
        #     logger.warning('debug is open')
        #     return

        url = item[3]
        if isinstance(url, float) or url.endswith('.pdf'):
            return

        if pandas.isna(item[6]) or isinstance(item[6], float):
            logger.warning(f"{item[1]} - {item[0]} is not set yet")
            return
        else:
            logger.info(f"Getting table from: {item[1]} - {item[0]}")

        # change the ExtractRule data of the Excel to json
        # func_json = json.loads(item[6].replace("\'", "\""))
        func_json = json.loads(item[6])

        if 'p' in func_json:
            """Use a plugin to do the whole job"""
            plugin = pluginBase.get_func(my_plugins, func_json['p'])
            plugin(item)

        else:
            """use functions to clear the table"""
            # use fetch or chrome function get the html
            if isinstance(func_json['m'], list):
                # if the method has param
                html = getattr(fc, func_json['m'][0])(func_json['m'][1])
            else:
                html = getattr(fc, func_json['m'])(url)

            time.sleep(8)

            if 'table' not in html:
                raise Exception(f"Can't find table in {item[1]} - {item[0]}")

            # run each functions before get the table
            if 'pre' in func_json:
                for pre_item in func_json['pre']:
                    k = list(pre_item.keys())[0]  # func name
                    v = list(pre_item.values())[0]  # func param
                    if v is None:
                        html = getattr(fc, k)(html)
                    else:
                        html = getattr(fc, k)(html, v)

            # get the table
            table = fc.extract_table(html, func_json['t'])

            # get the update time of the holders
            update_str = fc.update(item[1], html, func_json['u'])

            # run each functions to clear the table
            for f_item in func_json['f']:
                k = list(f_item.keys())[0]  # func name
                v = list(f_item.values())[0]  # func param
                if v is None:
                    table = getattr(fc, k)(table)
                else:
                    table = getattr(fc, k)(table, v)

            # get the update time of the holders
            table = fc.set_key_names(table, func_json['k'])
            table = fc.clear_table(item[1], table)

            fc.end(table, item, update=update_str)
    except Exception as e:
        logger.error(f'{item[1]} - {item[0]} :{e}')
        fc.end_err(item, err_info=e)


my_plugins = PluginCollection('jobs').get_all_plugins()
sheet = pandas.read_excel(io='Link to top shareholders.xlsx')

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=6) as t:
        all_task = [t.submit(run, row, my_plugins) for index, row in sheet.iterrows()]
        wait(all_task, return_when=ALL_COMPLETED)

    os.system("")
    print(f'>>> Scanning finished <<<')
