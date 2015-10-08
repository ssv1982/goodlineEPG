#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
import lxml.html as html
import datetime


def getDescription(url):
    description = ''
    type_prog = ''
    req = urllib.request.urlopen(url).read()
    doc = html.fromstring(req)
    descr = doc.find_class("b-tv-program-description__description")
    type_prog = doc.find_class("tv-program-meta__program-type-name")[0].text
    if len(descr) > 0:
        descr = descr[0]
        descr = descr.getchildren()
        description = descr[0].text

    return (description,
            type_prog)

chanell_list = [837, 582]
chanell_prog_week = {}
today = datetime.date.today()
monday = today - datetime.timedelta(days=today.weekday())
for ch in chanell_list:
    prog_week = {}
    for i in range(7):
        dt = monday+datetime.timedelta(days=i)
        print('============', dt, '=================')
        url = "https://tv.yandex.ru/64/channels/"+str(ch)+"?date="+str(dt)+"&period=all-day"

        req = urllib.request.urlopen(url).read()

        tv = html.fromstring(req)
        tv.make_links_absolute(url)
        programm = tv.find_class("b-tv-channel-schedule__items").pop()
        dt_prev = datetime.datetime(1, 1, 1)
        print(dt)
        for child in programm.getchildren():
            qq = child.getchildren()
            for child2 in qq:
                ww = child2.getchildren()
                info = getDescription(child2.attrib['href'])
                print(child2.attrib['href'])
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
                prog_week[dt] = (prog_name, info[0], info[1])
                dt_prev = dt
    chanell_prog_week[ch] = prog_week
print(chanell_prog_week)
