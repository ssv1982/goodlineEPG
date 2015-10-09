#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import lxml.html as html
import datetime
import urllib3
from urllib3 import PoolManager, Timeout, Retry
import threading
import queue
urllib3.disable_warnings()

num_yandex_threads = 10


def worker(numThread, pr_w, numHeadThread, lock, q_y):
    while True:
        item = q_y.get()
        #lock.acquire()
        prog_name, descr_url = pr_w[item]
        #lock.release()
        print('Thread', numHeadThread,
              'SubThread', numThread,
              'Programm:', prog_name)
        descr = getDescription(descr_url)
        #lock.acquire()
        pr_w[item] = (prog_name, descr[0], descr[1])
        #lock.release()
        q_y.task_done()
        print('Thread', numHeadThread,
              'SubThread', numThread,
              'Programm:', prog_name, 'DONE')


def getUrl(url):
    """Возвращает содержимое страницы по переданном url"""
    http = PoolManager()
    r = http.request('GET', url,
                     timeout=Timeout(connect=1.0, read=2.0),
                     retries=Retry(5, redirect=False)
                     )
    return html.fromstring(r.data)


def getDescription(url):
    """получение описания програмы
    возвращается список (описание,тип программы)"""
    description = ''
    type_prog = ''
    doc = getUrl(url)
    descr = doc.find_class("b-tv-program-description__description")
    type_prog = doc.find_class("tv-program-meta__program-type-name")[0].text
    if len(descr) > 0:
        descr = descr[0]
        descr = descr.getchildren()
        description = descr[0].text

    return (description,
            type_prog)


def getProgramm(numThread, channel, bdate=datetime.date.today() -
                datetime.timedelta(days=datetime.date.today().weekday()),
                num_days=14):
    """получение программы на несколько дней"""
    prog_week = {}

    q_y = queue.Queue()
    lock = threading.Lock()

    for i in range(num_days):
        dt = bdate+datetime.timedelta(days=i)
        url = "https://tv.yandex.ru/64/channels/" + \
            str(channel)+"?date="+str(dt)+"&period=all-day"
        getProgrammDay(channel, dt, url, prog_week)
    print('Thread', numThread, 'list programm recieved')
    for i in range(num_yandex_threads):
        t = threading.Thread(target=worker,
                             args=(i, prog_week, numThread, lock, q_y))
        t.daemon = True
        t.start()
    for item in prog_week.keys():
        q_y.put(item)

    q_y.join()

    return prog_week


def getProgrammDay(channel, dt, url, pr_w):
    tv = getUrl(url)
    tv.make_links_absolute(url)
    programm = tv.find_class("b-tv-channel-schedule__items").pop()
    if programm is None:
        return
    dt_prev = datetime.datetime(1, 1, 1)
    for child in programm.getchildren():
        qq = child.getchildren()
        for child2 in qq:
            ww = child2.getchildren()
            prog_name = ww[1].getchildren().pop().text
            descr_url = child2.attrib['href']
            tmp = ww[0].text
            time=None
            #print(tmp)
            h, m = tmp.split(':')
            time = datetime.datetime(1, 1, 1, int(h), int(m))

            dt = datetime.datetime.combine(dt, time.time())
            if dt_prev > dt:
                dt = dt+datetime.timedelta(days=1)
            # info = getDescription(child2.attrib['href'])
            pr_w[dt] = (prog_name, descr_url)
            # print(pr_w[dt])
            dt_prev = dt


# print(getProgramm(837))
