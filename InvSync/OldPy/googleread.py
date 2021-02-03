import xlrd as xr
import configparser
import os, sys
import pygsheets
import ftplib
from datetime import datetime
import googleapiclient
import requests
import re
import pandas


paint_tags = {}

readlist = ['Lot Title', 'Lot Description', 'Reserve', 'Genres']

core_image_src = 'Paintings'

fields = ['Handle', 'Title', 'Body (HTML)', 'Vendor', 'Type', 'Tags', 'Published', 'Option1 Name',
           'Option1 Value', 'Variant Grams', 'Variant Inventory Qty', 'Variant Inventory Policy',
           'Variant Fulfillment Service', 'Variant Price', 'Variant Requires Shipping', 'Variant Taxable',
           'Image Src', 'Image Position', 'Gift Card']

const_info = {'Vendor': 'Ukrainianvintage',
              'Published': 'TRUE',
              'Option1 Name': 'Title',
              'Option1 Value': 'Default Title',
              'Variant Grams': 0.0,
              'Variant Inventory Qty': 1,
              'Variant Inventory Policy': 'deny',
              'Variant Fulfillment Service': 'manual',
              'Variant Requires Shipping': 'TRUE',
              'Variant Taxable': 'TRUE',
              'Gift Card': 'FALSE'}


# формирование колонки Handle
def make_handle(data):
    res = []
    for item in data:
        name = item[0].lower()
        match = re.findall(r'\b\w{1,}\b', name)
        res.append('-'.join(match))
    return res


def make_title(data):
    res = []
    for item in data:
        res.append(item[0])
    return res


def make_price(data):
    res = []
    for item in data:
        res.append(item[0])
    return res


def make_body(data):
    title = re.findall(r'TITLE.*', data)[0]
    size = re.findall(r'SIZE.*', data)[0]
    medium = re.findall(r'MEDIUM.*', data)[0]
    hp = re.findall(r'HAND PAINTED.*', data)[0]
    condition = re.findall(r'CONDITION.*', data)[0]
    return '<p>*** ABOUT THIS PAINTING ***<br> * ' + title + '<br> * ' + size +\
                 '<br> * ' + medium + '<br> * ' + hp + '<br> * ' + condition +\
                 '</p> <p>Dear friends all our vintage paintings are in single copy that why you will be sole ' \
                   'owner. Maybe you will find something simillar but you will never find this one whoever in the ' \
                   'world :)' +\
                '<br> For more details about product,<br> Phone (WhatApp, Viber, Telegram) : +380956090337<br>' +\
                'Mail : ukrainianvintage [!at] gmail.com<br> Website: samovary-vishivanku.com.ua/<br> Presentation:' +\
                'https://drive.google.com/open?id=1i3s4o9dC1MnL9dwm0vdPxaG-jtMPFLcq<br> Video about our ofline' +\
                'shop: https://youtu.be/N9GV-hmYX7g</p> <p>Please visit our Storefront to see' +\
                'more:https://www.etsy.com/shop/UkrainianVintageCo/items</p> <p>We have expirience in antiquary' +\
                'more that 30 years. That\'s why we have huge amount of<br> painting,art & collectibles,<br> original' +\
                'painting, oil painting<br> original abstract, soviet painting<br> art work, kitchen decor, ' +\
                'landscape painting,' +\
                'vintage oil painting,<br> forest landscape, landscape art<br> soviet oil painting, impressionist ' +\
                'art, nature' +\
                'painting, soviet ukrainian art, soviet russian art, signed artwork, meadow landscape, oil portrait, original' +\
                'portrait, vintage portrait, portrait painting, portrait art, USSR<br> Ukrainian artists, gouache, soviet' +\
                'propaganda, bolsheviks, October Revolution, fields landscape, summer landscape, winter landscape,' +\
                'mountain landscape.<br> So, if you need smth just tell us!)</p>'


def make_types(data):
    res_type = []
    res_tags = []
    for item in data:
        res_type.append(item[0])
        try:
            res_tags.append(paint_tags[item[0]])
        except:
            res_tags.append('')
    return res_type, res_tags


def read_tags():
    global paint_tags
    gc = pygsheets.authorize()
    sh = gc.open('paint_tags')
    wks = sh.worksheet_by_title('Лист1')
    types = wks.get_values((2, 1), (wks.rows, 1), returnas='matrix')
    tags = wks.get_values((2, 2), (wks.rows, 2), returnas='matrix')
    res = {}
    for i in range(0, len(types)):
        res.update({types[i][0]: tags[i][0]})
    paint_tags = res


def get_pages():
    # авторизация и открытие источника
    gc = pygsheets.authorize()
    sh = gc.open('Inventory_0609')
    return [item.title for item in sh._sheet_list]


def img_list(datadict):
    img_folders, img_srcs = [], []
    for item in datadict.keys():
        lst = datadict[item]
        path = re.match(r'.{1,}/', lst[0])
        path = path.group(0)
        img_lst = []
        for img in lst:
            img_lst.append(img[len(path):])
        img_folders.append(path)
        img_srcs.append(';'.join(img_lst))
    return img_folders, img_srcs


def get_df(pagename):
    """ возвразает данные, необходимые для синхронизации Shopify в виде DataFrame """
    read_tags()
    print('Авторизация')
    gc = pygsheets.authorize()
    sh = gc.open('Inventory_0609')
    wks = sh.worksheet_by_title(pagename)
    print('Чтение данных')
    headers = wks.get_values((1, 1), (1, 11), returnas='matrix')
    headers = headers[0].copy()
    data = {}
    for i in range(1, 12):
        if (headers[i - 1] != '') and (headers[i - 1] in readlist):
            print(headers[i - 1])
            data_col = wks.get_values((2, i), (wks.rows, i), returnas='matrix')
            data.update({headers[i - 1]: data_col})

    # чтение данных
    handles = make_handle(data['Lot Title'])

    titles = make_title(data['Lot Title'])

    prices = make_price(data['Reserve'])

    bodies = []
    for item in data['Lot Description']:
        bodies.append(make_body(item[0]))

    types, tags = make_types(data['Genres'])

    print('Возврат результата')
    count = [str(i + 1) for i in range(len(bodies))]
    size = len(handles)
    res_dict = {'Title': titles, 'Body': bodies, 'Type': types, 'Tags': tags, 'Variant Price': prices, 'count': count}
    for item in res_dict.keys():
        if len(res_dict[item]) < size:
            res_dict[item].extend([''] * (size - len(res_dict[item])))
    for item in const_info.keys():
        res_dict.update({item: [const_info[item]] * size})

    return pandas.DataFrame(res_dict, index=handles)

