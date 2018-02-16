#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
import urllib
import requests
import cookielib
from string import Template
from bs4 import BeautifulSoup
from colorama import init
from colorama import Fore, Back, Style


getUuidUrl = "http://www.bjbus.com/home/ajax_rtbus_data.php?act=getLineDir&selBLine=$line"
getStationsUrl = "http://www.bjbus.com/home/ajax_rtbus_data.php?act=getDirStation&selBLine=$line&selBDir=$uuid"
getBusUrl = "http://www.bjbus.com/home/ajax_rtbus_data.php?act=busTime&selBLine=$line&selBDir=$uuid&selBStop=$localStation"

headers = {
'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
'Connection': 'Keep-Alive',
'Host': 'www.bjbus.com'
}

cookiesFile = 'bus.cookies'
session = requests.Session()
session.headers.update(headers)


def getLineUuid(line, reverse):
    session.cookies = cookielib.LWPCookieJar(filename = cookiesFile)
    if os.path.exists(cookiesFile):
        session.cookies.load(ignore_discard=True)

    templStr = Template(getUuidUrl)
    url = templStr.substitute(line=line)
    result = session.get(url)
    if result.status_code != 200:
        print "%s return %d" % (url, result.status_code)
        return 0
    result.encoding = 'utf-8'
    content = result.text
    soup = BeautifulSoup(content, "html.parser")
    lines = soup.find_all('a')
    if len(lines) == 1:
        line = lines[0]
    elif len(lines) == 2:
        if reverse:
            line = lines[0]
        else:
            line = lines[1]
    else:
        print "can't get bus line by name(%s)" % line
        return None
    uuid = line["data-uuid"]
    title = line.text.strip().strip(')').split('(')
    name = title[0]
    direction = title[1]
    # print "%s %s %s" % (uuid, name, direction)
    session.cookies.save(ignore_discard=True, ignore_expires=True)
    return uuid


def getAllStations(line, uuid):
    stations = []
    s = Template(getStationsUrl)
    url = s.substitute(line=line, uuid=uuid)
    result = session.get(url)
    if result.status_code != 200:
        print "%s return %d" % (url, result.status_code)
        return []
    result.encoding = 'utf-8'
    content = result.text
    soup = BeautifulSoup(content, "html.parser")
    allStations = soup.find_all('a')
    for station in allStations:
        seq = station["data-seq"]
        name = station.text
        station = "%s %s" % (seq, name)
        print station
        stations.append(station)
    return stations


def getBusState(line, uuid, localStation):
    templStr = Template(getBusUrl)
    url = templStr.substitute(line=line, uuid=uuid, localStation=localStation)
    result = session.get(url)
    if result.status_code != 200:
        print "%s return %d" % (url, result.status_code)
        return 0
    result.encoding = 'utf-8'
    content = result.text
    testJson = json.loads(content)
    html = testJson['html']
    seq = testJson['seq']
    soup = BeautifulSoup(html, "html.parser")
    
    header = soup.find_all(attrs={"class":"inquiry_header"})[0]
    title = header.find(id="lh")
    print title.text

    info = header.find(id="lm")
    print info.text

    inner = header.find_all(attrs={"class":"inner"})[0]
    p = inner.find_all('p')
    text = p[0].text.encode("utf-8", "ignore")
    pos1 = text.find('\xc2\xa0')
    pos2 = text.find('\xc2\xa0', pos1 + 2)
    if pos1 > 0 and pos2 > pos1:
        busTime = text[pos1+2 : pos2].strip()
        print busTime

    ccStops = soup.find_all(id="cc_stop")[0]
    stations = ccStops.find_all("div")
    count = len(stations)
    for station in stations:
        title = station.text
        id = station["id"]
        if len(title) > 0:
            print "%s %s" % (id, title)
        
        buss = station.find_all(attrs={"class": "buss"})
        if len(buss) > 0:
            print Fore.RED + '    arrived at...'
        busc = station.find_all(attrs={"class": "busc"})
        if len(busc) > 0:
            print Fore.YELLOW + '    running...'


if __name__ == '__main__':
    if len(sys.argv) > 1:
        line = sys.argv[1]
        line = line.decode('gbk').encode('utf-8')
    else:
        line = '300内'

    line = urllib.quote(line)
    reverse = False
    if len(sys.argv) > 2 and sys.argv[2].find('r') >= 0:
        reverse = True

    uuid = getLineUuid(line, reverse)
    if uuid == None:
        print "can't get line %s" % (line)
        sys.exit(1)

    # getAllStations(line, uuid)
    # init colorama
    init(autoreset=True)
    getBusState(line, uuid, '1')

