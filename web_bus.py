#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import urllib
import requests
from string import Template
from bs4 import BeautifulSoup
from colorama import init
from colorama import Fore, Back, Style


GET_ID_URL = "http://www.bjbus.com/home/ajax_rtbus_data.php?act=getLineDir&selBLine=$line"
GET_STATION_URL = "http://www.bjbus.com/home/ajax_rtbus_data.php?act=getDirStation&selBLine=$line&selBDir=$uuid"
GET_BUS_URL = "http://www.bjbus.com/home/ajax_rtbus_data.php?act=busTime&selBLine=$line&selBDir=$uuid&selBStop=$local_station"

HEADER = {
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
    'Connection': 'Keep-Alive',
    'Host': 'www.bjbus.com'
}

STD_OUT_ENCODING = sys.stdout.encoding.lower()


class WebBus(object):
    def __init__(self, show_info = True):
        self._showInfo = show_info
        self._session = requests.Session()
        self._session.headers.update(HEADER)

    def print_info(self, info):
        if self._showInfo:
            print info

    def query(self, name, reverse):
        if isinstance(name, unicode):
            line_name = urllib.quote(name.encode('utf-8'))
        elif isinstance(name, str):
            line_name = urllib.quote(name)
        else:
            return "can not support your input: %s(neither unicode or str)" % (name), False

        uuid = self.get_line_uuid(line_name, reverse)
        if uuid is None:
            return "can not get bus line info by name: %s" % (name), False

        # self.get_all_stations(name, uuid)
        # init colorama
        if self._showInfo:
            init(autoreset=True)

        return self.get_bus_state(line_name, uuid), True

    def get_line_uuid(self, name, reverse):
        temp_url = Template(GET_ID_URL)
        url = temp_url.substitute(line = name)
        result = self._session.get(url)
        if result.status_code != 200:
            print "ERROR: %s return %d" % (url, result.status_code)
            return None

        result.encoding = 'utf-8'
        content = result.text
        soup = BeautifulSoup(content, "html.parser")
        bus_lines = soup.find_all('a')

        if len(bus_lines) == 1:
            bus_line = bus_lines[0]
        elif len(bus_lines) == 2:
            if reverse:
                bus_line = bus_lines[1]
            else:
                bus_line = bus_lines[0]
        else:
            print "can't get bus line by name(%s)" % name
            return None

        uuid = bus_line["data-uuid"]
        # title = line.text.strip().strip(')').split('(')
        # lineName = title[0]
        # direction = title[1]
        # self.print_info("%s %s %s" % (uuid, lineName, direction))
        return uuid

    def get_all_stations(self, line_name, uuid):
        stations = []
        temp_url = Template(GET_STATION_URL)
        url = temp_url.substitute(line=line_name, uuid=uuid)
        result = self._session.get(url)
        if result.status_code != 200:
            print "%s return %d" % (url, result.status_code)
            return []
        
        result.encoding = 'utf-8'
        content = result.text
        soup = BeautifulSoup(content, "html.parser")
        all_stations = soup.find_all('a')
        for station in all_stations:
            seq = station["data-seq"]
            name = station.text
            station_info = "%s %s" % (seq, name)
            print station_info
            stations.append(station_info)
        
        return stations

    def get_bus_state(self, line_name, uuid, local_station ='1'):
        templ_str = Template(GET_BUS_URL)
        url = templ_str.substitute(line=line_name, uuid=uuid, local_station=local_station)
        response = self._session.get(url)
        if response.status_code != 200:
            return "%s return %d" % (url, response.status_code)
        
        response.encoding = 'utf-8'
        content = response.text
        test_json = json.loads(content)
        html = test_json['html']
        # seq = testJson['seq']
        soup = BeautifulSoup(html, "html.parser")

        result = ""
        header = soup.find_all(attrs={"class":"inquiry_header"})[0]
        title = header.find(id="lh")
        self.print_info(title.text)
        result += title.text + "\n"

        bus_info = header.find(id="lm")
        self.print_info(bus_info.text)
        result += bus_info.text + "\n"

        inner = header.find_all(attrs={"class":"inner"})[0]
        p = inner.find_all('p')
        text = p[0].text.encode("utf-8", "ignore")
        pos1 = text.find('\xc2\xa0')
        pos2 = text.find('\xc2\xa0', pos1 + 2)
        if pos1 > 0 and pos2 > pos1:
            bus_time = text[pos1+2 : pos2].strip().decode("utf-8")
            self.print_info(bus_time)
            result += bus_time + "\n"

        # print soup.prettify()
        cc_stops = soup.find_all(id="cc_stop")[0]
        stations = cc_stops.find_all("div")
        # count = len(stations)
        number = 0
        for station in stations:
            title = station.text
            id = station["id"]
            if len(title) > 0:
                self.print_info("%s %s" % (id, title))
                result += "%s %s\n" % (id, title)
            
            buss = station.find_all(attrs={"class": "buss"})
            if len(buss) > 0:
                self.print_info(Fore.RED + '    arrived at...')
                result += u"    arrived at\n"
                number += 1
            
            busc = station.find_all(attrs={"class": "busc"})
            if len(busc) > 0:
                self.print_info(Fore.YELLOW + '    running...')
                result += u"    驶往下一站\n"
                number += 1

        result += u"查到 %d 辆车" % number
        return result


if __name__ == '__main__':
    if len(sys.argv) > 1:
        line = sys.argv[1]
        if STD_OUT_ENCODING == "utf8" or STD_OUT_ENCODING == "utf-8":
            line = line.decode('utf-8')
        else:
            line = line.decode('gb2312').encode('utf-8')
    else:
        line = '1'

    rev = False
    if len(sys.argv) > 2 and sys.argv[2].find('r') >= 0:
        rev = True

    bus = WebBus(False)
    info, success = bus.query(line, rev)
    print info
