from tkinter import Tk, Listbox, END, EXTENDED, Button, Frame, LEFT, TOP, RIGHT
from OldPy.googleread import get_pages, get_df
from sfyaccess import readsfdata
from OldPy.listdrive import list_images
import pickle
from tkinter import messagebox as mb


def add_items():
    for item in pages.curselection():
        selected.insert(END, pages.get(item))
        pages.delete(item)


def del_items():
    for item in selected.curselection():
        pages.insert(END, selected.get(item))
        selected.delete(item)


def syncbases():
    syncpages = {}
    for item in selected.get(0, selected.size() - 1):
        syncpages.update({item: get_df(item)})
        readsfdata(item, syncpages[item])


def syncimages():
    for item in selected.get(0, selected.size() - 1):
        print(list_images(item, update=False))


def sync_pages():
    read_pages = get_pages()
    pages.delete(0, END)
    selected.delete(0, END)
    for item in read_pages:
        pages.insert(END, item)
    mb.showinfo(title='Message', message='Pages list has been updated')


def on_closing():
    listfile = open('SheetsPickle.pkl', 'ab')
    listpages = pages.get(0, pages.size()-1)
    pickle.dump(listpages, listfile)
    listfile.close()
    window.destroy()

try:
    listfile = open('SheetsPickle.pkl', 'rb')
    read_pages = pickle.load(listfile)
except:
    print('Чтение из Google')
    read_pages = get_pages()

window = Tk()
window.geometry("380x350")

listframe = Frame(window)
pages = Listbox(listframe, width=25, height=15, selectmode=EXTENDED)
pages.pack(side=LEFT)

for item in read_pages:
    pages.insert(END, item)

moveframe = Frame(listframe)
Button(moveframe, text='>', width=2, command=add_items).pack(side=TOP)
Button(moveframe, text='<', width=2, command=del_items).pack(side=TOP)
moveframe.pack(side=LEFT, padx=10)

selected = Listbox(listframe, width=25, height=15)
selected.pack(side=RIGHT)

buttonframe = Frame(window)

Button(buttonframe, text='Страницы', width=15, command=sync_pages).pack(side=LEFT)
Button(buttonframe, text='Изображения', width=15, command=syncimages).pack(side=LEFT)
Button(buttonframe, text='Синхронизировать', width=15, command=syncbases).pack(side=LEFT)

listframe.pack(side=TOP, padx=10, pady=20)
buttonframe.pack(side=TOP)

window.protocol("WM_DELETE_WINDOW", on_closing)
window.mainloop()

