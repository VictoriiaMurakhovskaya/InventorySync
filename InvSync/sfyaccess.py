from __future__ import print_function
import shopify
from base64 import b64encode
import sys
from transliterate import translit, get_available_language_codes

API_KEY = '5c16c575308fecf94f4753800dd40731'
PASSWORD = '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'
SHOP_NAME = 'UAVintageTest'
API_VERSION = '2020-10'
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']


def syncitems(pagename, df, imgfolder, df_images):
    # полный перечень коллекций из GSheet
    collects = df['Type'].unique()
    collects = [item.title() for item in collects if item]

    # авторизация в Shopify
    shop_url = "https://%s:%s@%s.myshopify.com/admin/api/%s" % (API_KEY, PASSWORD, SHOP_NAME, API_VERSION)
    shopify.ShopifyResource.set_site(shop_url)

    # синхронизация коллекций
    sfcollects = [item.title for item in shopify.CollectionListing.find(fields='collection_id, title')]

    # получение коллекций для дальнейшей работы
    sfcollects = shopify.CollectionListing.find(fields='id, title')
    collect_dict = {}
    for item in sfcollects:
        collect_dict.update({item.title: item})

    # получение продуктов для дальнейшней работы
    google_handles = list(df.index)
    products_list = shopify.Product.find(fields='id, handle')
    sfyproducts = [item.handle for item in products_list]
    products_dict = {item.handle: item.id for item in products_list}
    count = 1

    for item in google_handles:
        if item not in sfyproducts:
            # создание нового элемента
            sfyproduct = shopify.Product()
            sfyproduct.title = df.at[item, 'Title']
            sfyproduct.handle = item
        else:
            # обновление существующего элемента
            sfyproduct = shopify.Product.find(products_dict[item])

        # обновление реквизитов элемента
        sfyproduct.body_html = df.at[item, 'Body']
        sfyproduct.product_type = df.at[item, 'Type']
        sfyproduct.tags = df.at[item, 'Tags']
        sfyproduct.vendor = df.at[item, 'Vendor']

        # сохранение реквизитов, которые хранятся в Variant
        variant = shopify.Variant({'price': df.at[item, 'Variant Price']})
        sfyproduct.variants = [variant]

        # сохранение продукта
        try:
            sfyproduct.save()
        except:
            print('First product save' + str(item))

        # добавление изображений
        try:
            img_list = df_images.loc[
            (df_images['rootfolder'] == pagename) & (df_images['foldername'] == df.at[item, 'Number'])]
        except:
            print('Image choice error')
            print(df.at[item, 'Number'])
        to_attach = []
        for index, row in img_list.iterrows():
            filename = imgfolder + '/' + pagename + '/' + row['foldername'] + '/' + row['filename']
            with open(filename, "rb") as f:
                to_attach.append(shopify.Image({'product_id': sfyproduct.id}))
                fname = translit(filename.split("/")[-1:][0], 'ru', reversed=True)
                encoded = f.read()
                to_attach[-1].attach_image(encoded, filename=fname)
                res = to_attach[-1].save()
        sfyproduct.images = to_attach
        try:
            sfyproduct.save()
        except:
            print(row['foldername'])
        count += 1


def sync_collections(col_names):
    # авторизация в Shopify
    shop_url = "https://%s:%s@%s.myshopify.com/admin/api/%s" % (API_KEY, PASSWORD, SHOP_NAME, API_VERSION)
    shopify.ShopifyResource.set_site(shop_url)
    # получение коллекций для дальнейшей работы
    sfcollects = shopify.CollectionListing.find(fields='id, title')
    for item in sfcollects:
        cc = shopify.CustomCollection.find(item.id)
        print(cc.published_scope)

    # for item in col_names:
    #         newcollection = shopify.CustomCollection()
    #         newcollection.title = item
    #         newcollection.save()
