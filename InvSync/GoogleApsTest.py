from gdaccess import load_images, list_images, get_df
from sfyaccess import syncitems

paint_tags_file = 'paint_tags'
paint_tags_sheet_name = 'Лист1'
main_folder = 'ImgTemp'
pagename = 'TestSheet1'

df_images = list_images('TestSheet1', update=True)
df_images.to_excel('images.xlsx')
load_images(pagename, main_folder)

# получение главной таблицы
main_df = get_df(pagename)
main_df.to_excel('mainparse.xlsx')

# синхронизация Shopify
syncitems(pagename, main_df, main_folder, df_images)





