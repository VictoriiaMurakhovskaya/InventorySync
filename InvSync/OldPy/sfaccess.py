import shopify
API_KEY = '08bf69684e2493c9d8d42debf38fd899'
PASSWORD = 'D16m03c@t'
SHOP_NAME = 'UAVintageTest'
API_VERSION = '2020-07'

shop_url = "https://%s:%s@%s.myshopify.com/admin/api/%s" % (API_KEY, PASSWORD, SHOP_NAME, API_VERSION)
shopify.ShopifyResource.set_site(shop_url)
shop = shopify.Shop.current()