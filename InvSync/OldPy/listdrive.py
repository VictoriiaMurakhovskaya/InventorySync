from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from getfilelistpy import getfilelist
import pandas as pd
import os

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']


def list_images(mainfolder, update=False):
    """ основной экспортируемый метод модуля
        mainfolder - папка, по которой нужно экспортировать данные
        update - флаг
                если Истина - запрос к Google Disk
                если Ложь - попытка чтения данных из Pickle
                если невозможно - запрос к Google Disk с дальнейшим обновлением Pickle таблицы """
    if not update:
        if os.path.exists('../img_table.pkl'):
            df = pd.read_pickle('../img_table.pkl')
            return df.loc[df['rootfolder'] == mainfolder]
    df = make_img_table(mainfolder)
    update_pkl(df, folder=mainfolder)
    return df


def update_pkl(df, folder):
    """ метод обновляет хранящиеся данные после запроса к Google Disk """
    if os.path.exists('../img_table.pkl'):
        dfsave = pd.read_pickle('../img_table.pkl')
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
    if os.path.exists('../token.pickle'):
        with open('../token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '../client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('../token.pickle', 'wb') as token:
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
