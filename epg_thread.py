#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import struct
import os
import datetime
import lxml.etree
import tempfile
from zipfile import ZipFile
import urllib.request
import queue
import threading
import yandex

num_worker_threads = 10

tv_sootv = {'156': {'chID': 837, 'timeshift': 0, 'title': 'Первый канал HD'},
            '1': {'chID': 582, 'timeshift': 0, 'title': 'Россия 1'},
            '161': {'chID': 578, 'timeshift': 0, 'title': 'ТНТ'},
            '160': {'chID': 573, 'timeshift': 0, 'title': 'Домашний'},
            '4': {'chID': 44, 'timeshift': 0, 'title': 'НТВ'},
            '167': {'chID': 602, 'timeshift': 0, 'title': 'РЕН-ТВ'},
            '5': {'chID': 496, 'timeshift': 0, 'title': 'СТС'},
            '7': {'chID': 515, 'timeshift': 0, 'title': 'Россия 2'},
            '169': {'chID': 1000, 'timeshift': 0, 'title': 'ОТР'},
            '9': {'chID': 636, 'timeshift': 0, 'title': 'Россия К'},
            '11': {'chID': 829, 'timeshift': 180, 'title': 'Звезда'},
            '13': {'chID': 955, 'timeshift': 0, 'title': 'Мой город'},
            '15': {'chID': 245, 'timeshift': 0, 'title': '5 Канал'},
            '14': {'chID': 144, 'timeshift': 60, 'title': 'ТВ3'},
            '18': {'chID': 772, 'timeshift': 180, 'title': 'Карусель'},
            '19': {'chID': 186, 'timeshift': 120, 'title': 'Дисней'},
            '20': {'chID': 66, 'timeshift': 0, 'title': 'Детский'},
            '23': {'chID': 567, 'timeshift': 0, 'title': 'Nickelodeon '},
            '6': {'chID': 517, 'timeshift': 0, 'title': 'ТВЦ'},
            }


def do_work(key, val, result, n_th):
        result[key] = yandex.getProgramm(n_th, val)
        # print(key)


def worker(numTread):
    while True:
        item = q.get()
        print('Поток', numTread, ':', item, 'Канал:', tv_sootv[item]['title'])
        do_work(item, tv_sootv[item], yandex_descriptions, numTread)
        q.task_done()
        print('Поток', numTread,
              'Канал:', tv_sootv[item]['title'],
              ': Закончен. Осталось в очереди:', q.qsize())


ts = datetime.datetime.now()


url = "http://bolshoe.tv/altdynplaylist/"
req = urllib.request.urlopen(url).read()
root_logo = lxml.etree.fromstring(req)
logo = {}
m3u = open('GoodLine_http.m3u', 'w')
m3u_udp = open('GoodLine.m3u', 'w')
m3u.write('#EXTM3U\n')
m3u_udp.write('#EXTM3U\n')

tracklist = root_logo.findall('{http://xspf.org/ns/0/}trackList')[0]
for track in tracklist.findall('{http://xspf.org/ns/0/}track'):
    psfile = track.findall('{http://xspf.org/ns/0/}psfile')[0]
    image = track.findall('{http://xspf.org/ns/0/}image')[0]
    logo[psfile.text] = image.text.replace(' ', '%20')
    title = track.findall('{http://xspf.org/ns/0/}title')[0]
    location = track.findall('{http://xspf.org/ns/0/}location')[0]
    txt = '#EXTINF:-1 tvg-name="' + psfile.text + '" ,' + title.text+'\n'
    m3u.write(txt)
    m3u_udp.write(txt)
    m3u_udp.write(location.text+'\n')
    m3u.write('http://192.168.98.1:4022/' +
              location.text.replace('://@', '/') + '\n')

m3u.close()
m3u_udp.close()


yandex_descriptions = {}
print('Загрузка описаний передач для', len(tv_sootv), 'каналов')

q = queue.Queue()
for i in range(num_worker_threads):
    t = threading.Thread(target=worker, args=(i, ))
    t.daemon = True
    t.start()
for item in tv_sootv.keys():
    q.put(item)

q.join()

print('Все описания загружены.')


def getFiletime(dt):
    microseconds = dt / 10
    seconds, microseconds = divmod(microseconds, 1000000)
    days, seconds = divmod(seconds, 86400)
    return datetime.datetime(1601, 1, 1) + datetime.timedelta(days,
                                                              seconds,
                                                              microseconds)


url = "http://bolshoe.tv/tv.zip"
req = urllib.request.urlopen(url).read()
tmpdir = tempfile.TemporaryDirectory()

tv_zip = open(tmpdir.name+'/'+'tv.zip', 'wb')
tv_zip.write(req)
tv_zip.close()
z = ZipFile(tmpdir.name+'/'+'tv.zip')
z.extractall(tmpdir.name)
files = z.namelist()
f_list = []
for q in files:
    (name, ext) = q.split('.')
    if name not in f_list:
        f_list.append(name)
z.close()

print('Обработана программа GoodLine')

root = lxml.etree.Element('tv')

for cn in sorted(logo.keys()):
    chanel = lxml.etree.SubElement(root, "channel")
    chanel.set("id", "id_"+cn)
    dn = lxml.etree.SubElement(chanel, "display-name")
    dn.set('lang', 'ru')
    dn.text = cn
    icon = lxml.etree.SubElement(chanel, "icon")
    icon.set('src', logo.get(cn, ''))

# for cn in f_list:
for cn in sorted(logo.keys()):
    file = open(tmpdir.name+'/'+cn+'.ndx', 'rb')
    file2 = open(tmpdir.name+'/'+cn+'.pdt', 'rb')
    programme_prev = 0
    byte = file.read(2)

    progs_desc = yandex_descriptions.get(cn)

    num = struct.unpack('h', byte)[0]
    for i in range(num-1):
        tmp = file.read(2)
        byte = file.read(8)
        off = struct.unpack('H', file.read(2))[0]
        tm = struct.unpack('L', byte)[0]
        tm = getFiletime(tm)
        time = tm.strftime('%Y%m%d%H%M%S +0000')
        file2.seek(off, os.SEEK_SET)
        num_name = struct.unpack('h', file2.read(2))[0]
        title = struct.unpack(str(num_name)+'s', file2.read(num_name))[0]

        programme = lxml.etree.SubElement(root, "programme")
        programme.set('start', time)
        title_xml = lxml.etree.SubElement(programme, "title")
        title_xml.set('lang', 'ru')
        title_xml.text = title.decode('cp1251')
        programme.set('channel', 'id_'+cn)

        if progs_desc is not None:
            descr = progs_desc.get(tm)
            if descr is not None:
                category = lxml.etree.SubElement(programme, "category")
                category.set('lang', 'ru')
                category.text = descr[2]
                description = lxml.etree.SubElement(programme, "desc")
                description.set('lang', 'ru')
                description.text = descr[1]
                sub_title = lxml.etree.SubElement(programme, "sub-title")
                sub_title.set('lang', 'ru')
                sub_title.text = descr[0]

        if i > 0:
            programme_prev.set('stop', time)

        programme_prev = programme
    file.close()
    file2.close()

xml = open('GoodLine_EPG.xml', 'wb')
xml.write(lxml.etree.tostring(root,
                              pretty_print=True,
                              encoding='utf-8',
                              xml_declaration=True))
tmpdir.cleanup()
tf = datetime.datetime.now()
dif = tf - ts
print(ts, '---', tf, '=', dif)
