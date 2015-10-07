#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import lxml.html as html
import urllib.request

url="https://tv.yandex.ru/64/channels/837?date=2015-10-07&period=all-day"
req = urllib.request.urlopen(url).read()

tv = html.fromstring(req)
tv.make_links_absolute(url)
programm=tv.find_class("b-tv-channel-schedule__items").pop()
#print(len(programm.getchildren()))

for child in programm.getchildren():
    qq=child.getchildren()
    for child2 in qq:
        ww=child2.getchildren()
        print(child2.attrib['href'])
        print(ww[0].text,'---',ww[1].getchildren().pop().text)
