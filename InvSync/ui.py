import pygsheets
import re
from OldPy.listdrive import make_file_dict

core_image_src = 'Paintings'

table_b_name = 'TableB'

table_b = {'Handle': 1,
           'Title': 2,
           'Body (HTML)': 3,
           'Vendor': 4,
           'Type': 5,
           'Tags': 6,
           'Published': 7,
           'Option1 Name': 8,
           'Option1 Value': 9,
           'Variant Grams': 15,
           'Variant Inventory Qty': 17,
           'Variant Inventory Policy': 18,
           'Variant Fulfillment Service': 19,
           'Variant Price': 20,
           'Variant Requires Shipping': 22,
           'Variant Taxable': 24,
           'Image Src': 26,
           'Image Position': 27,
           'Gift Card': 29}

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

paint_tags = {}

readlist = ['Lot Title', 'Lot Description', 'Reserve', 'Genres']


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


def work_with_wks(wks, wks_write):
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

    images = make_file_dict(wks.title)

    # формирование новых объектов для записи
    write_list = []
    for count in range(4):
        write_dict = {}
        for item in table_b.keys():
            if item == 'Handle':
                value = handles[count]
            elif item == 'Title':
                value = titles[count]
            elif item == 'Body (HTML)':
                value = bodies[count]
            elif item == 'Type':
                value = types[count]
            elif item == 'Tags':
                value = tags[count]
            elif item == 'Variant Price':
                value = prices[count]
            else:
                try:
                    value = const_info[item]
                except:
                    value = ''
            write_dict.update({item: value})
        write_list.append(write_dict)

    # создание заголовков
    for item in table_b.keys():
        wks_write.update_value((1, table_b[item]), item)

    # запись
    count = 1
    row_count = 2 # начинаем писать после строки заголовков

    print('Начало записи ' + str(len(write_list)) + 'строк')
    for row in write_list:
        #wks_write.unlink()

        # запись основных значений
        for item in table_b.keys():
            wks_write.update_value((row_count, table_b[item]), row[item])

        # запись заголовка строки для вставки в следующие
        handle = handles[count - 1]
        print(handle)

        if str(count) in images.keys():
            # есть изображения
            wks_write.update_value((row_count, table_b['Image Src']), images[str(count)][0])
            wks_write.update_value((row_count, table_b['Image Position']), '1')
            if len(images[str(count)]) > 1:
                row_count += 1
                imageCount = 2
                for im in images[str(count)][1:]:
                    wks_write.update_value((row_count, table_b['Image Src']), images[str(count)][imageCount - 1])
                    wks_write.update_value((row_count, table_b['Image Position']), str(imageCount))
                    imageCount += 1
                    row_count += 1
        else:
            # впишем пустые строки
            wks_write.update_value((row_count, table_b['Image Src']), '')
            wks_write.update_value((row_count, table_b['Image Position']), '')
            row_count += 1
        count += 1
        #wks_write.link()


def read_gs():
    # авторизация и открытие источника
    gc = pygsheets.authorize()
    sh = gc.open('Inventory_0609')
    wks = sh.worksheet_by_title(sh._sheet_list[0].title)

    # запись в целевой файл (создание нового и дозапись существующего)
    # записи обновляются, начиная с первой
    try:
        new_gs = gc.open(table_b_name)
    except:
        print('Результирующая таблица не найдена. Создан новый документ')
        res = gc.sheet.create(table_b_name)
        new_gs = gc.open_by_key(res['spreadsheetId'])

    try:
        b_gs = new_gs.worksheet_by_title(sh._sheet_list[0].title)
    except:
        print('Лист в документе не найден, создан новый')
        b_gs = new_gs.add_worksheet(sh._sheet_list[0].title, cols=29)

    try:
        new_gs.del_worksheet(new_gs.worksheet_by_title('Лист1'))
    except:
        pass

    work_with_wks(wks, b_gs)


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


def main():
    read_tags()
    read_gs()


if __name__ == '__main__':
    main()

