from OldPy.listdrive import list_images
import os
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account


SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = '../credentials.json'
main_folder = 'ImgTemp'
pagename = 'TestVERN'


def load_images(pname, folder):
    df_images = list_images(pname, update=False)

    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    subfolders = df_images['foldername'].unique()

    if not os.path.exists(folder):
        os.mkdir(folder)

    os.chdir(folder)

    for f in subfolders:
        if not os.path.exists(f):
            os.mkdir(f)

    for index, row in df_images.iterrows():
        request = service.files().get_media(fileId=row['fileid'])
        filename = row['foldername'] + '/' + row['filename']
        fh = io.FileIO(filename, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()


def main():
    load_images(pagename, main_folder)


if __name__ == '__main__':
    main()
