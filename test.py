#!/usr/bin/python
# -*- coding: UTF-8 -*-

import json
nn = round(10.00, 2)
print(nn)

p = {
    'm': 'fetch',
    'u': r"//th[@class='has-text-align-left' and contains(text(), 'shareholders')]",
    't': [0],
    'f': [
        {'del_rows_end': 2},
    ],
    'k': ['Investor', 'Number of shares', '% of total']
}

f = {
    'func': 'teck'
}


str = json.dumps(p)
print(str)