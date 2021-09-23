#!/usr/bin/python
# -*- coding: UTF-8 -*-

def get_func(plugins, func_name):
    for plugin in plugins:
        if plugin.__module__.endswith(func_name):
            return plugin.run_job


class Plugin:
    def __init__(self):
        pass

    def run_job(self, item):
        raise NotImplementedError
