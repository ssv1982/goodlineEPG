#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# import urllib.request
import lxml.html as html
import datetime
from urllib3 import PoolManager, Timeout, Retry
import ssl


def getDescription(url):
    description = ''
    type_prog = ''
    http = PoolManager()
    r = http.request('GET', url,
                     timeout=Timeout(connect=1.0, read=2.0),
                     retries=Retry(3, redirect=False)
                     )

#    req = urllib.request.urlopen(url).read()
    doc = html.fromstring(r.data)
    descr = doc.find_class("b-tv-program-description__description")
    type_prog = doc.find_class("tv-program-meta__program-type-name")[0].text
    if len(descr) > 0:
        descr = descr[0]
        descr = descr.getchildren()
        description = descr[0].text

    return (description,
            type_prog)

# channel_list = [837, 582]
# channel_prog_week = {}
# today = datetime.date.today()
# monday = today - datetime.timedelta(days=today.weekday())
# for ch in channel_list:
def getProgramm(channel,bdate = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday()),num_days=7):
    prog_week = {}
    for i in range(num_days):
        dt = bdate+datetime.timedelta(days=i)
        print('============', dt, '=================')
        url = "https://tv.yandex.ru/64/channels/"+str(channel)+"?date="+str(dt)+"&period=all-day"
        print(url)
        http = PoolManager()
        r = http.request('GET', url,
                         timeout=Timeout(connect=1.0, read=2.0),
                         retries=Retry(3, redirect=False)
                         )
#        req = urllib.request.urlopen(url).read()

        tv = html.fromstring(r.data)
        tv.make_links_absolute(url)
        programm = tv.find_class("b-tv-channel-schedule__items").pop()
        dt_prev = datetime.datetime(1, 1, 1)
 #       print(dt)
        for child in programm.getchildren():
            qq = child.getchildren()
            for child2 in qq:
                ww = child2.getchildren()
                info = getDescription(child2.attrib['href'])
                # print(child2.attrib['href'])
                time = datetime.datetime.strptime(ww[0].text, '%H:%M')
                prog_name = ww[1].getchildren().pop().text
                dt = datetime.datetime.combine(dt, time.time())
                if dt_prev > dt:
                    dt = dt+datetime.timedelta(days=1)
    #            print(dt, '---',
    #                  prog_name,
    #                  '---',
    #                  info[0],
    #                  '---',
    #                  info[1]
    #                  )
                print(dt, '---', prog_name)
                prog_week[dt] = (prog_name, info[0], info[1])
                dt_prev = dt
    #channel_prog_week[ch] = prog_week
    return prog_week

#print(getProgramm(837))
