#!/usr/bin/python
# -*-coding:utf-8-*-

import os
import sys
import json
import time
import hashlib
import requests

from cipher3 import Cipher

STD_OUT_ENCODING = sys.stdout.encoding.lower()
HOST = 'transapp.btic.org.cn:8512'
CHECK_UPDATE_PATH = "/ssgj/v1.0.0/checkupdate"
ALL_BUS_INDEX_URL = 'http://' + HOST + CHECK_UPDATE_PATH + "?version=0"
UPDATE_PATH = "/ssgj/v1.0.0/update"
UPDATE_LINE_URL = 'http://' + HOST + UPDATE_PATH + "?id={0}"
UPDATE_LINE_STATE_URL = 'http://' + HOST + \
    '/ssgj/bus.php?versionid=6&encrypt=1&datatype=json&no=2&type=1&' + \
    'id={0}&city=%E5%8C%97%E4%BA%AC'


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


class MobileBus(object):

    def __init__(self, debug=False):
        self._debug = debug
        self._session = requests.Session()
        self._bus_index = None

    def debug(self, info):
        if self._debug:
            print(info)

    @staticmethod
    def get_token(str_input):
        temp = hashlib.sha1(str_input.encode()).hexdigest()
        return hashlib.md5(temp.encode()).hexdigest()

    def get_all_bus_index(self):
        modify_time = 0
        now = int(time.time())
        if os.path.exists(BUS_INDEX_FILE_NAME) and (now - int(os.stat(
                BUS_INDEX_FILE_NAME).st_mtime) > 3600 * 24):
            self.debug("load bus index info from file")
            with open(BUS_INDEX_FILE_NAME, "r") as jsonFile:
                json_result = json.load(jsonFile)
        else:
            self.debug("request from web...")
            HEADERS["TIME"] = "%d" % now
            key = "%s%s%s%d%s" % (SECRET_KEY, PLAT_FROM,
                                  CID, now, CHECK_UPDATE_PATH)
            HEADERS["ABTOKEN"] = self.get_token(key)
            self._session.headers.update(HEADERS)
            r = self._session.get(ALL_BUS_INDEX_URL)
            if r.status_code != 200:
                print("%s return %d" % (ALL_BUS_INDEX_URL, r.status_code))
                return False

            json_result = r.json()
            with open(BUS_INDEX_FILE_NAME, "w") as jsonFile:
                json.dump(json_result, jsonFile, ensure_ascii=False)

        self._bus_index = json_result
        return True

    def get_line_id(self, line_name, reverse):

        lines = self._bus_index['lines']['line']
        for line in lines:
            status = line['status']
            if not status:
                continue

            line_id = line['id']
            line_name_json = line['linename']
            if line_name_json.find(line_name + "(") == 0:
                if reverse:
                    reverse = False
                    continue
                return line_id
        return 0

    def get_line_stations(self, line_id):

        url = UPDATE_LINE_URL.format(line_id)
        now = int(time.time())
        HEADERS["TIME"] = "%d" % now
        key = "%s%s%s%d%s" % (SECRET_KEY, PLAT_FROM, CID, now, UPDATE_PATH)
        token = self.get_token(key)
        HEADERS["ABTOKEN"] = token

        self._session.headers.update(HEADERS)
        r = self._session.get(url)
        if r.status_code != 200:
            print("%s return %d" % (url, r.status_code))
            return None

        ret_json = r.json()
        if ret_json["errcode"] != "200":
            print("%s return errcode = %s, errmsg = %s" %
                  (url, ret_json["errcode"], ret_json["errmsg"]))
            return None
        if len(ret_json['busline']) > 1:
            print("warning: more than one busline")

        bus_line = ret_json['busline'][0]
        line_id = bus_line['lineid']

        cipher = Cipher('%s%s' % (CUSTOM, line_id))
        base_info = ""
        line_name = cipher.decrypt(bus_line['linename']).decode()
        self.debug(line_name)

        base_info += "%s\n" % (line_name)
        self.debug("%s" % (bus_line['time']))
        base_info += "%s\n" % (bus_line['time'])

        ret_stations = []
        stations = bus_line['stations']['station']
        for station in stations:
            station_no = int(cipher.decrypt(station['no']))
            station_name = cipher.decrypt(station['name']).decode()
            lon = float(cipher.decrypt(station['lon']))
            lat = float(cipher.decrypt(station['lat']))
            self.debug("%d %s %s %s" %
                       (station_no, station_name, lon, lat))

            ret_stations.append({
                'no': station_no,
                'name': station_name,
                'x': lon,
                "y": lat
            })
        return ret_stations, base_info

    def get_line_state(self, line_id):

        url = UPDATE_LINE_STATE_URL.format(line_id)
        now = int(time.time())
        HEADERS["TIME"] = "%d" % now
        key = "%s%s%s%d" % (SECRET_KEY, PLAT_FROM, CID, now)
        token = self.get_token(key)
        HEADERS["ABTOKEN"] = token
        self._session.headers.update(HEADERS)

        response = self._session.get(url)
        if response.status_code != 200:
            print("%s return %d" % (url, response.status_code))
            return None

        ret_json = response.json()["root"]
        if ret_json["status"] != "200":
            print("%s return status = %s, message = %s" %
                  (url, ret_json["status"], ret_json["message"]))
            return None

        bus_data = ret_json['data']['bus']
        buses = {}
        for bus in bus_data:
            key = 'aibang%s' % bus['gt']
            d = Cipher(key).decrypt

            next_station_num = int(d(bus['nsn']))
            next_station_distance = int(bus['nsd'])
            next_station_arriving_time = int(bus['nst'])
            lat = d(bus['x'])
            lon = d(bus['y'])

            station_id = next_station_num - (next_station_distance > 0)

            thisBus = {
                'nsd': next_station_distance,
                'nst': next_station_arriving_time,
                'x': lat,
                'y': lon
            }
            if station_id in buses.keys():
                buses[station_id].append(thisBus)
            else:
                buses[station_id] = [thisBus]
        return buses

    def report(self, stations, buses):

        result = ""
        if 0 in buses.keys():
            for bus in buses[0]:
                self.debug("is going on")
                result += "    is going on\n"

        number = 0
        for station in stations:
            no = station['no']
            station_name = station['name']
            x = station['x']
            y = station['y']
            result += "%d %s\n" % (no, station_name)
            self.debug("%d %s %s %s" % (no, station_name, x, y))

            if no in buses.keys():
                for bus in buses[no]:
                    nst = bus['nst']
                    x = bus['x']
                    y = bus['y']
                    if nst > 0:
                        time_local = time.localtime(nst)
                        arriving_time = time.strftime("%H:%M", time_local)
                        self.debug("    after %d meters " % (bus['nsd']) +
                                   "will arrive at next station(%s)(%s %s)" % (
                            arriving_time, float(x), float(y)))
                        result += "    距离下一站 %d 米，预计 %s 到达\n" % (
                            bus['nsd'], arriving_time)
                        number += 1
                    else:
                        self.debug("    arrived")
                        result += "    已到达\n"
                        number += 1

        result += "查到 %d 辆车" % number
        return result

    def query(self, name, reverse):
        name = name.strip()
        self.debug("name = {0}, reverse = {1}".format(name, reverse))

        if not self.get_all_bus_index():
            return "cat't get all line index", False

        line_id = self.get_line_id(name, reverse)
        if not line_id:
            return "can't get line id from name({0})".format(name), False
        self.debug('line_id: {0}'.format(line_id))

        stations, info = self.get_line_stations(line_id)
        if not stations:
            return "can't get stations correctly, line name = %s, id = %s" % (
                name, line_id), False

        buses = self.get_line_state(line_id)
        if not buses:
            return "can't get buses correctly, line name = %s, id = %s" % (
                name, line_id), False

        result = self.report(stations, buses)
        return info + result, True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        name = sys.argv[1]
    else:
        name = "1"

    reverse = False
    if len(sys.argv) > 2 and sys.argv[-1] == 'r':
        reverse = True

    bus = MobileBus()
    result, succ = bus.query(name, reverse)
    print(result)
