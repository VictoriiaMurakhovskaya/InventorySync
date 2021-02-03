from __future__ import print_function
import pygsheets
import re
import pandas
import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from getfilelistpy import getfilelist
import pandas as pd
from OldPy.listdrive import list_images
import os
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account


SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'
main_folder = 'ImgTemp'
pagename = 'TestSheet1'
inventoryfile = 'Test051020'
readlist = ['Lot Number', 'Lot Title', 'Lot Description', 'Reserve', 'Genres']
core_image_src = 'Test'
paint_tags_file = 'paint_tags'
paint_tags_sheet_name = 'Лист1'


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

################################################
# начало секции функции, импортируемых из модуля
################################################


def list_images(mainfolder, update=False):
    """ функция возвращающая таблицу изображений
        mainfolder - папка, по которой нужно экспортировать данные
        update - флаг
                если Истина - запрос к Google Disk
                если Ложь - попытка чтения данных из Pickle
                если невозможно - запрос к Google Disk с дальнейшим обновлением Pickle таблицы """
    if not update:
        if os.path.exists('img_table.pkl'):
            df = pd.read_pickle('img_table.pkl')
            return df.loc[df['rootfolder'] == mainfolder]
    df = make_img_table(mainfolder)
    update_pkl(df, folder=mainfolder)
    return df


def load_images(pname, folder):
    """ метод, производящий загрузку изображений из указанной подпапки в Paintings
        в заданную папку """
    df_images = list_images(pname, update=True)

    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    subfolders = df_images['foldername'].unique()

    if not os.path.exists(folder):
        os.mkdir(folder)

    if not os.path.exists(folder + '/' + pname ):
        os.mkdir(folder + '/' + pname )

    for f in subfolders:
        if not os.path.exists(folder + '/' + pname + '/' + f):
            os.mkdir(folder + '/' + pname + '/' + f)

    for index, row in df_images.iterrows():
        request = service.files().get_media(fileId=row['fileid'])
        filename = folder + '/' + pname + '/' + row['foldername'] + '/' + row['filename']
        fh = io.FileIO(filename, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()


def get_df(pagename):
    """ функция, которая возвращает данные, необходимые для синхронизации Shopify в виде DataFrame """
    read_tags(paint_tags_file, paint_tags_sheet_name)
    print('Авторизация')
    gc = pygsheets.authorize()
    sh = gc.open(inventoryfile)
    wks = sh.worksheet_by_title(pagename)
    print('Чтение данных')
    headers = wks.get_values((1, 1), (1, 11), returnas='matrix')
    headers = headers[0].copy()
    data = {}
    for i in range(1, 12):
        if (headers[i - 1] != '') and (headers[i - 1] in readlist):
            data_col = wks.get_values((2, i), (wks.rows, i), returnas='matrix')
            data.update({headers[i - 1]: data_col})

    # чтение данных
    numbers = make_price(data['Lot Number'])

    handles = make_handle(data['Lot Title'])

    titles = make_title(data['Lot Title'])

    prices = make_price(data['Reserve'])

    bodies = []
    for item in data['Lot Description']:
        bodies.append(make_body(item[0]))

    types, tags = make_types(data['Genres'], read_tags(paint_tags_file, paint_tags_sheet_name))

    print('Возврат результата')
    count = [str(i + 1) for i in range(len(bodies))]
    size = len(handles)
    res_dict = {'Number': numbers, 'Title': titles, 'Body': bodies, 'Type': types, 'Tags': tags, 'Variant Price': prices, 'count': count}
    for item in res_dict.keys():
        if len(res_dict[item]) < size:
            res_dict[item].extend([''] * (size - len(res_dict[item])))
    for item in const_info.keys():
        res_dict.update({item: [const_info[item]] * size})

    return pandas.DataFrame(res_dict, index=handles)


###############################################
# конец секции функции, импортируемых из модуля
###############################################


def make_handle(data):
    """ формирование колонки Handle в DataFrame
    """
    res = []
    for item in data:
        name = item[0].lower()
        match = re.findall(r'\b\w{1,}\b', name)
        new_handle = '-'.join(match)
        counter = 2
        trial = new_handle
        while trial in res:
            trial = new_handle + '(' + str(counter) + ')'
            counter += 1
        res.append(trial)
    return res


def make_title(data):
    """ формирование колонки заголовка в DataFrame"""
    res = []
    for item in data:
        res.append(item[0])
    return res


def make_price(data):
    """ формирование колонки цена в DataFrame """
    res = []
    for item in data:
        res.append(item[0])
    return res


def make_body(data):
    """формирование колонки описания в DataFrame """
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


def make_types(data, tags_dict):
    """ возвращает списки жанров и тегов к ним """
    res_type = []
    res_tags = []
    for item in data:
        res_type.append(item[0])
        try:
            res_tags.append(tags_dict[item[0]])
        except:
            res_tags.append('')
    return res_type, res_tags


def read_tags(paint_tags_file, sheetname):
    """ читает из Google таблицы в словарь жанры/теги к ним """
    gc = pygsheets.authorize()
    sh = gc.open(paint_tags_file)
    wks = sh.worksheet_by_title(sheetname)
    types = wks.get_values((2, 1), (wks.rows, 1), returnas='matrix')
    tags = wks.get_values((2, 2), (wks.rows, 2), returnas='matrix')
    res = {}
    for i in range(0, len(types)):
        res.update({types[i][0]: tags[i][0]})
    return res


def get_pages():
    """ возвращает перечень листов в основной Google таблице """
    gc = pygsheets.authorize()
    sh = gc.open(inventoryfile)
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


def update_pkl(df, folder):
    """ метод обновляет хранящиеся данные после запроса к Google Disk """
    if os.path.exists('img_table.pkl'):
        dfsave = pd.read_pickle('img_table.pkl')
        new = dfsave.loc[df['rootfolder'] != folder]
        new.merge(df, how='left')
    else:
        new = df.copy()
    new.to_pickle('img_table.pkl')


def make_img_table(foldername):
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)

    page_token = None
    while True:
        response = service.files().list(q="name = '" + foldername + "'",
                                        spaces='drive',
                                        fields='nextPageToken, files(id, name)',
                                        pageToken=page_token).execute()
        for file in response.get('files', []):
            id = file.get('id')
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

    if id:
        resource = {
            "oauth2": creds,
            "id": id,
            "fields": "files(name, id)",
        }
        return make_listing(resource)
    else:
        return None


def folder_name(folder_dict, id):
    for item in folder_dict.keys():
        if folder_dict[item] == id:
            return item
    return None


def make_listing(resource):
    """ метод чтения каталога изображений с дальнейшей записью в PKL-файл """
    res = getfilelist.GetFileList(resource)
    foldernames = res['folderTree']['names']
    folderids = res['folderTree']['folders']
    rootfolder = foldernames[0]
    folders_dict = {foldernames[i]: folderids[i] for i in range(1, len(foldernames))}
    filesstructure = res['fileList']
    files_dict = {}
    for item in filesstructure:
        if item['files']:
            flist = item['files']
            ftree = item['folderTree']
            foldername = folder_name(folders_dict, ftree[-1])
            files_dict.update({foldername: flist})

    df_rootfolder, df_foldername, df_folder_id, df_filename, df_file_id = [], [], [], [], []
    for fldr in folders_dict.keys():
        for item in files_dict[fldr]:
            df_foldername.append(fldr)
            df_folder_id.append(folders_dict[fldr])
            df_filename.append(item['name'])
            df_file_id.append(item['id'])
    df_rootfolder = [rootfolder] * len(df_file_id)
    df = pd.DataFrame({'rootfolder': df_rootfolder, 'foldername': df_foldername, 'folderid': df_folder_id,
                       'filename': df_filename, 'fileid': df_file_id})
    return df



