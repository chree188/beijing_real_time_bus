#!/usr/bin/python
# -*-coding:utf-8-*-

import os
import sys
import json
import time
import hashlib
import requests
from cipher import Cipher
from string import Template
from colorama import init
from colorama import Fore, Back, Style

host = 'transapp.btic.org.cn:8512'
checkUpdatePath = "/ssgj/v1.0.0/checkupdate"
allBusIndexUrl = 'http://' + host + checkUpdatePath + "?version=0"
updatePath = "/ssgj/v1.0.0/update"
updateLineUrl = 'http://' + host + updatePath + "?id=$lineId"
updateLineStateUrl = 'http://' + host + '/ssgj/bus.php?versionid=6&encrypt=1&datatype=json&no=2&type=1&id=$lineId&city=%E5%8C%97%E4%BA%AC'


busIndexFileName = "all_index.json"
secretKey = "bjjw_jtcx"
platForm = "android"
cid = "67a88ec31de7a589a2344cc5d0469074"
custom = "aibang"

headers = {
"PKG_SOURCE" : "1",
"NETWORK" : "gprs",
"UA" : "Unknown,Unknown,Unknown,Unknown,Unknown,Unknown",
"IMSI" : "Unknown",
"CUSTOM" : "%s" % custom,
"PLATFORM" : "%s" % platForm,
"CID" : "%s" % cid,
"IMEI" : "Unknown",
"CTYPE" : "json",
"UID" : "",
"VID" : "6",
"SID" : "",
"PID" : "5",
"SOURCE" : "1",
"HEADER_KEY_SECRET" : "%s" % secretKey,
"Host" : "%s" % host,
"Connection" : "Keep-Alive",
"Accept-Encoding" : "gzip",
"User-Agent" : "okhttp/3.3.1"
}

# "TIME" : "1518615547",
# "ABTOKEN" : "d6b53963ec654f913fa30280a4ef6d65",
session = requests.Session()
stdOutEncoding = sys.stdout.encoding.lower()


def getToken(strInput):
    temp = hashlib.sha1(strInput).hexdigest()
    return hashlib.md5(temp).hexdigest()


#1) get all bus lines name and id
def getAllBusIndex():
    mtime = 0
    now = int(time.time())
    if os.path.exists(busIndexFileName):
        mtime = int(os.stat("all_index.json").st_mtime)

    if now - mtime > 3600 * 24:
        print "request from web..."
        headers["TIME"] = "%d" % now
        key = "%s%s%s%d%s" % (secretKey, platForm, cid, now, checkUpdatePath)
        headers["ABTOKEN"] = getToken(key)
        session.headers.update(headers)
        result = session.get(allBusIndexUrl)
        if result.status_code != 200:
            print "%s return %d" % (allBusIndexUrl, result.status_code)
            return None
        jsonResult = result.json()
        with open(busIndexFileName, "w+") as jsonFile:
            json.dump(jsonResult, jsonFile)
    else:
        print "load bus index info from file"
        with open(busIndexFileName, "r") as jsonFile:
            jsonResult = json.load(jsonFile)
    return jsonResult

def getLineId(busIndexs, name, reverse):
    lines = busIndexs['lines']['line']
    for line in lines:
        lineName = line['linename']
        lineId = line['id']
        if lineName.find(name + "(") == 0:
            if reverse:
                reverse = False
                continue
            print "%s" % (lineName)
            return lineId
    return 0


def getLineStations(lineId):
    templStr = Template(updateLineUrl)
    url = templStr.substitute(lineId=lineId)
    now = int(time.time())
    headers["TIME"] = "%d" % now
    key = "%s%s%s%d%s" % (secretKey, platForm, cid, now, updatePath)
    token = getToken(key)
    headers["ABTOKEN"] = token
    session.headers.update(headers)
    result = session.get(url)
    if result.status_code != 200:
        print "%s return %d" % (url, result.status_code)
        return None
    retJson = result.json()
    if retJson["errcode"] != "200":
        print "%s return errcode = %s, errmsg = %s" % (url, retJson["errcode"], retJson["errmsg"])
        return None
    if len(retJson['busline']) > 1:
        print "warning have more than one busline"
    busLine = retJson['busline'][0]
    lineId = busLine['lineid']

    cipher = Cipher('%s%s' % (custom, lineId))

    #路线坐标
    #coord = busLine['coord']

    lineName = cipher.decrypt(busLine['linename'])
    print "%s" % (busLine['time'])

    retStations = []
    stations = busLine['stations']['station']
    for station in stations:
        stationNo = int(cipher.decrypt(station['no']))
        stationName = cipher.decrypt(station['name'])
        lon = cipher.decrypt(station['lon'])
        lat = cipher.decrypt(station['lat'])
        # print "%d %s %s %s" % (stationNo, stationName, lon, lat)
        retStations.append({
        'no'  : stationNo,
        'name': stationName,
        'x' : lon,
        "y" : lat
        })
    return retStations


def getLineState(lineId):
    templStr = Template(updateLineStateUrl)
    url = templStr.substitute(lineId=lineId)
    now = int(time.time())
    headers["TIME"] = "%d" % now
    key = "%s%s%s%d" % (secretKey, platForm, cid, now)
    token = getToken(key)
    headers["ABTOKEN"] = token
    session.headers.update(headers)
    result = session.get(url)
    if result.status_code != 200:
        print "%s return %d" % (url, result.status_code)
        return None
    retJson = result.json()["root"]
    if retJson["status"] != "200":
        print "%s return status = %s, message = %s" % (url, retJson["status"], retJson["message"])
        return None
    busNum = retJson['num']
    busData = retJson['data']['bus']
    buses = {}
    for bus in busData:
        key = 'aibang%s' % bus['gt']
        d = Cipher(key).decrypt

        # nextStationName = d(bus['ns'])
        nextStationNum = int(d(bus['nsn']))
        nextStationDistance = int(bus['nsd'])
        nextStationArrivingTime = int(bus['nst'])
        # stationDistance = d(bus['sd'])
        # stationArrivingTime = d(bus['st'])
        lat = d(bus['x'])
        lon = d(bus['y'])

        # timeLocal = time.localtime(nextStationArrivingTime)
        # arrivingTimeStr = time.strftime("%H:%M", timeLocal)
        if nextStationDistance > 0:
            stationId = nextStationNum - 1
        else:
            stationId = nextStationNum

        thisBus = {
                'nsd': nextStationDistance,
                'nst': nextStationArrivingTime,
                'x' : lat,
                'y' : lon
                }
        if buses.has_key(stationId):
            buses[stationId].append(thisBus)
        else:
            buses[stationId] = [thisBus]
    return buses

def showBusInfo(stations, buses):
    if buses.has_key(0):
        for bus in buses[0]:
            print Fore.YELLOW + "is going on"

    for station in stations:
        no = station['no']
        name = station['name']
        x = station['x']
        y = station['y']
        out = "%d %s %s %s" % (no, name, x, y)
        if stdOutEncoding == "utf8" or stdOutEncoding == "utf-8":
            print out
        else:
            print out.decode('utf-8').encode('gb2312')

        if buses.has_key(no):
            for bus in buses[no]:
                nst = bus['nst']
                x = bus['x']
                y = bus['y']
                if nst > 0:
                    timeLocal = time.localtime(nst)
                    arrivingTime = time.strftime("%H:%M", timeLocal)
                    print Fore.YELLOW + "    after %d meters will arrive at next station(%s)(%s %s)" % (bus['nsd'], arrivingTime, x, y)
                else:
                    print Fore.RED + "    arrived at"

def run(name, reverse):
    print "name = %s, reverse = %d" % (name, reverse)

    busIndexs = getAllBusIndex()
    if busIndexs == None:
        print "cat't get all line index"
        sys.exit(1)

    lineId = getLineId(busIndexs, name, reverse)
    if lineId == 0:
        print "can't get line id from name(%s)" % name
        sys.exit(2)
    
    stations = getLineStations(lineId)
    if stations == None or len(stations) == 0:
        print "get stations have errors, line name = %s, id = %s" % (name, lineId)
        sys.exit(3)

    buses = getLineState(lineId)
    if buses == None or len(buses) == 0:
        print "get stations have errors, line name = %s, id = %s" % (name, lineId)
        sys.exit(4)
    
    init(autoreset=True)
    showBusInfo(stations, buses)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        name = sys.argv[1]
        name = name.decode('gbk').encode('utf-8')
    else:
        name = u"300内"

    reverse = False
    if len(sys.argv) > 2 and sys.argv[2].find('r') >= 0:
        reverse = True
    
    run(name, reverse)