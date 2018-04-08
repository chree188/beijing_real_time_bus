#!/usr/bin/python
# -*-coding:utf-8-*-

import os
import sys
import json
import time
import hashlib
import requests

from cipher import Cipher
from colorama import init
from colorama import Fore, Back, Style
from string import Template

HOST = 'transapp.btic.org.cn:8512'
CHECK_UPDATE_PATH = "/ssgj/v1.0.0/checkupdate"
ALL_BUS_INDEX_URL = 'http://' + HOST + CHECK_UPDATE_PATH + "?version=0"
UPDATE_PATH = "/ssgj/v1.0.0/update"
UPDATE_LINE_URL = 'http://' + HOST + UPDATE_PATH + "?id=$line_id"
UPDATE_LINE_STATE_URL = 'http://' + HOST + \
                     '/ssgj/bus.php?versionid=6&encrypt=1&datatype=json&no=2&type=1&id=$line_id&city=%E5%8C%97%E4%BA%AC'


BUS_INDEX_FILE_NAME = "mobile_all_lines.json"
SECRET_KEY = "bjjw_jtcx"
PLAT_FROM = "android"
CID = "67a88ec31de7a589a2344cc5d0469074"
CUSTOM = "aibang"

HEADERS = {
    "PKG_SOURCE": "1",
    "NETWORK": "gprs",
    "UA": "Unknown,Unknown,Unknown,Unknown,Unknown,Unknown",
    "IMSI": "Unknown",
    "CUSTOM": "%s" % CUSTOM,
    "PLATFORM": "%s" % PLAT_FROM,
    "CID": "%s" % CID,
    "IMEI": "Unknown",
    "CTYPE": "json",
    "UID": "",
    "VID": "6",
    "SID": "",
    "PID": "5",
    "SOURCE": "1",
    "HEADER_KEY_SECRET": "%s" % SECRET_KEY,
    "Host": "%s" % HOST,
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "User-Agent": "okhttp/3.3.1"
}

# "TIME": "1518615547",
# "ABTOKEN": "d6b53963ec654f913fa30280a4ef6d65",
STD_OUT_ENCODING = sys.stdout.encoding.lower()


class MobileBus(object):
    
    def __init__(self, show_info = True):
        self._show_info = show_info
        self._session = requests.Session()
        # self._session.headers.update(HEADERS)
        self._bus_index = None

    def print_info(self, info):
        if self._show_info:
            print info

    @staticmethod
    def get_token(str_input):
        temp = hashlib.sha1(str_input).hexdigest()
        return hashlib.md5(temp).hexdigest()

    def get_all_bus_index(self):
        modify_time = 0
        now = int(time.time())
        if os.path.exists(BUS_INDEX_FILE_NAME):
            modify_time = int(os.stat(BUS_INDEX_FILE_NAME).st_mtime)

        if now - modify_time > 3600 * 24:
            self.print_info("request from web...")
            HEADERS["TIME"] = "%d" % now
            key = "%s%s%s%d%s" % (SECRET_KEY, PLAT_FROM, CID, now, CHECK_UPDATE_PATH)
            HEADERS["ABTOKEN"] = self.get_token(key)
            self._session.headers.update(HEADERS)
            r = self._session.get(ALL_BUS_INDEX_URL)
            if r.status_code != 200:
                print "%s return %d" % (ALL_BUS_INDEX_URL, r.status_code)
                return False

            json_result = r.json()
            with open(BUS_INDEX_FILE_NAME, "w+") as jsonFile:
                json.dump(json_result, jsonFile)
        else:
            self.print_info("load bus index info from file")
            with open(BUS_INDEX_FILE_NAME, "r") as jsonFile:
                json_result = json.load(jsonFile)

        self._bus_index = json_result
        return True

    def get_line_id(self, line_name, reverse):

        lines = self._bus_index['lines']['line']
        for line in lines:
            status = line['status']
            if status != "0":
                continue
            
            line_id = line['id']
            line_name_json = line['linename']
            if line_name_json.find(line_name + "(") == 0:
                if reverse:
                    reverse = False
                    continue
                # self.print_info("%s" % (lineName))
                return line_id
        return 0

    def get_line_stations(self, line_id):
        
        template_str = Template(UPDATE_LINE_URL)
        url = template_str.substitute(line_id=line_id)

        now = int(time.time())
        HEADERS["TIME"] = "%d" % now
        key = "%s%s%s%d%s" % (SECRET_KEY, PLAT_FROM, CID, now, UPDATE_PATH)
        token = self.get_token(key)
        HEADERS["ABTOKEN"] = token

        self._session.headers.update(HEADERS)
        r = self._session.get(url)
        if r.status_code != 200:
            print "%s return %d" % (url, r.status_code)
            return None
        
        ret_json = r.json()
        if ret_json["errcode"] != "200":
            print "%s return errcode = %s, errmsg = %s" % (url, ret_json["errcode"], ret_json["errmsg"])
            return None
        if len(ret_json['busline']) > 1:
            print "warning have more than one busline"
        
        bus_line = ret_json['busline'][0]
        line_id = bus_line['lineid']

        cipher = Cipher('%s%s' % (CUSTOM, line_id))
        
        #路线坐标
        #coord = busLine['coord']

        base_info = ""
        line_name = cipher.decrypt(bus_line['linename'])
        if STD_OUT_ENCODING == "utf8" or STD_OUT_ENCODING == "utf-8":
            self.print_info(line_name)
        else:
            self.print_info(line_name.decode('utf-8'))
        base_info += "%s\n" % (line_name.decode("utf-8"))

        self.print_info("%s" % (bus_line['time']))
        base_info += "%s\n" % (bus_line['time'])

        ret_stations = []
        stations = bus_line['stations']['station']
        for station in stations:
            station_no = int(cipher.decrypt(station['no']))
            station_name = cipher.decrypt(station['name'])
            lon = cipher.decrypt(station['lon'])
            lat = cipher.decrypt(station['lat'])
            # self.print_info("%d %s %s %s" % (stationNo, stationName, lon, lat))
            ret_stations.append({
                'no': station_no,
                'name': station_name,
                'x': lon,
                "y": lat
            })
        return ret_stations, base_info

    def get_line_state(self, line_id):

        template_str = Template(UPDATE_LINE_STATE_URL)
        url = template_str.substitute(line_id=line_id)
        now = int(time.time())
        HEADERS["TIME"] = "%d" % now
        key = "%s%s%s%d" % (SECRET_KEY, PLAT_FROM, CID, now)
        token = self.get_token(key)
        HEADERS["ABTOKEN"] = token
        self._session.headers.update(HEADERS)

        response = self._session.get(url)
        if response.status_code != 200:
            print "%s return %d" % (url, response.status_code)
            return None

        ret_json = response.json()["root"]
        if ret_json["status"] != "200":
            print "%s return status = %s, message = %s" % (url, ret_json["status"], ret_json["message"])
            return None

        # bus_num = ret_json['num']
        bus_data = ret_json['data']['bus']
        buses = {}
        for bus in bus_data:
            key = 'aibang%s' % bus['gt']
            d = Cipher(key).decrypt

            # nextStationName = d(bus['ns'])
            next_station_num = int(d(bus['nsn']))
            next_station_distance = int(bus['nsd'])
            next_station_arriving_time = int(bus['nst'])
            # stationDistance = d(bus['sd'])
            # stationArrivingTime = d(bus['st'])
            lat = d(bus['x'])
            lon = d(bus['y'])

            # timeLocal = time.localtime(nextStationArrivingTime)
            # arrivingTimeStr = time.strftime("%H:%M", timeLocal)
            if next_station_distance > 0:
                station_id = next_station_num - 1
            else:
                station_id = next_station_num

            thisBus = {
                    'nsd': next_station_distance,
                    'nst': next_station_arriving_time,
                    'x': lat,
                    'y': lon
            }
            if buses.has_key(station_id):
                buses[station_id].append(thisBus)
            else:
                buses[station_id] = [thisBus]
        return buses

    def report(self, stations, buses):

        result = ""
        if buses.has_key(0):
            for bus in buses[0]:
                self.print_info(Fore.YELLOW + "is going on")
                result += "is going on\n"

        number = 0
        for station in stations:
            no = station['no']
            station_name = station['name']
            x = station['x']
            y = station['y']
            out = "%d %s %s %s" % (no, station_name, x, y)
            result += "%d %s\n" % (no, station_name)
            if STD_OUT_ENCODING == "utf8" or STD_OUT_ENCODING == "utf-8":
                self.print_info(out)
            else:
                self.print_info(out.decode('utf-8').encode('gb2312'))

            if buses.has_key(no):
                for bus in buses[no]:
                    nst = bus['nst']
                    x = bus['x']
                    y = bus['y']
                    if nst > 0:
                        time_local = time.localtime(nst)
                        arriving_time = time.strftime("%H:%M", time_local)
                        self.print_info(Fore.YELLOW + "    after %d meters will arrive at next station(%s)(%s %s)" % (bus['nsd'], arriving_time, x, y))
                        result += u"    距离下一站 %d 米\n".encode("utf-8") % (bus['nsd'])
                        number += 1
                    else:
                        self.print_info(Fore.RED + "    arrived at")
                        result += u"    arrived at\n".encode("utf-8")
                        number += 1

        result += u"查到 %d 辆车".encode("utf-8") % number
        return result

    def query(self, name, reverse):
        name = name.strip()
        self.print_info("name = %s, reverse = %d" % (name, reverse))

        if not self.get_all_bus_index():
            return "cat't get all line index", False

        line_id = self.get_line_id(name, reverse)
        if line_id == 0:
            return "can't get line id from name(%s)" % name, False
        
        stations, info = self.get_line_stations(line_id)
        if stations is None or len(stations) == 0:
            return "get stations have errors, line name = %s, id = %s" % (name, line_id), False

        print line_id
        buses = self.get_line_state(line_id)
        if buses is None or len(buses) == 0:
            return "get stations have errors, line name = %s, id = %s" % (name, line_id), False
        
        if self._show_info:
            init(autoreset=True)
        
        result = self.report(stations, buses)
        return info + result.decode("utf-8"), True


if __name__ == "__main__":
    print STD_OUT_ENCODING

    if len(sys.argv) > 1:
        name = sys.argv[1]
        if STD_OUT_ENCODING == "utf8" or STD_OUT_ENCODING == "utf-8":
            name = name.decode('utf-8')
        else:
            name = name.decode('gb2312').encode('utf-8')
    else:
        name = u"夜1"

    reverse = False
    if len(sys.argv) > 2 and sys.argv[2].find('r') >= 0:
        reverse = True
    
    bus = MobileBus(False)
    result, succ = bus.query(name, reverse)
    print result
