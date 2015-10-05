#! /usr/bin/env python3
import struct
import os
import datetime
import lxml.etree
import tempfile
from zipfile import ZipFile
import urllib.request


def getFiletime(dt):
    microseconds = dt / 10
    seconds, microseconds = divmod(microseconds, 1000000)
    days, seconds = divmod(seconds, 86400)
    return datetime.datetime(1601, 1, 1) + datetime.timedelta(days, seconds, microseconds)



url="http://bolshoe.tv/altdynplaylist/"
req = urllib.request.urlopen(url).read()

root_logo = lxml.etree.fromstring(req)
logo = {}
tracklist=root_logo.findall('{http://xspf.org/ns/0/}trackList')[0]
for track in tracklist.findall('{http://xspf.org/ns/0/}track'):
    psfile=track.findall('{http://xspf.org/ns/0/}psfile')[0]
    image=track.findall('{http://xspf.org/ns/0/}image')[0]
    logo[psfile.text]=image.text.replace(' ','%20')

url="http://bolshoe.tv/tv.zip"
req = urllib.request.urlopen(url).read()
tmpdir=tempfile.TemporaryDirectory()

tv_zip=open(tmpdir.name+'/'+'tv.zip','wb')
tv_zip.write(req)
tv_zip.close()
z = ZipFile(tmpdir.name+'/'+'tv.zip')
z.extractall(tmpdir.name)
files=z.namelist()
f_list=[]
for q in files:
    (name,ext)=q.split('.')
    if name not in f_list:
        f_list.append(name)
z.close()

root = lxml.etree.Element('tv')

for cn in f_list:
    chanel=lxml.etree.SubElement(root, "channel")
    chanel.set("id","id_"+cn)
    dn=lxml.etree.SubElement(chanel, "display-name")
    dn.set('lang','ru')
    dn.text=cn
    icon=lxml.etree.SubElement(chanel, "icon")
    icon.set('src',logo.get(cn,''))


for cn in f_list:
    file = open(tmpdir.name+'/'+cn+'.ndx','rb')
    file2 =open(tmpdir.name+'/'+cn+'.pdt','rb')

    byte = file.read(2)

    num=struct.unpack('h',byte)[0]
    for i in range(num-1):
        tmp = file.read(2)
        byte = file.read(8)
        off=struct.unpack('H',file.read(2))[0]
        tm=struct.unpack('L',byte)[0]
        tm=getFiletime(tm)
        time=tm.strftime('%Y%m%d%H%M%S +0000')
        file2.seek(off,os.SEEK_SET)
        num_name=struct.unpack('h',file2.read(2))[0]
        title=struct.unpack(str(num_name)+'s',file2.read(num_name))[0]

        programme=lxml.etree.SubElement(root, "programme")
        programme.set('start',time)
        title_xml=lxml.etree.SubElement(programme, "title")
        title_xml.set('lang','ru')
        title_xml.text=title.decode('cp1251')
        programme.set('channel','id_'+cn)

        if i>0:
            programme_prev.set('stop',time)

        programme_prev=programme
    file.close()
    file2.close()

xml=open('GoodLine_EPG.xml','wb')
xml.write(lxml.etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True))
tmpdir.cleanup()