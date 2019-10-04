#/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import configparser

from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport
from zeep.exceptions import Fault
from zeep.plugins import HistoryPlugin
from requests import Session
from requests.auth import HTTPBasicAuth
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from lxml import etree
from datetime import datetime

Timestart = datetime.now()
disable_warnings(InsecureRequestWarning)
Search = []

vars = configparser.ConfigParser()
varfile = 'vars.conf'
vars.read(varfile)
axluser = vars['cucm']['axluser']
axlpassword = vars['cucm']['axlpassword']
cucmhost = vars['cucm']['ip']
path = os.path.dirname(os.path.abspath( __file__ ))
wsdl = os.path.join(path, 'axl', 'AXLAPI.wsdl')
riswsdl = 'https://{}:8443/realtimeservice2/services/RISService70?wsdl'.format(cucmhost)
location = 'https://{host}:8443/axl/'.format(host=cucmhost)
binding = "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding"

def show_history():
    for item in [history.last_sent, history.last_received]:
        print(etree.tostring(item["envelope"], encoding="unicode", pretty_print=True))

def cucm_rt_phones(model = 255, name = '', num = '', ip = '', max = 1000, Print = True):
    StateInfo = ''
    if name != '':
        SelectBy = 'Name'
        SelectItems = {'item': name}
    elif num != '':
        SelectBy = 'DirNumber'
        SelectItems = {'item': num}
    elif ip != '':
        SelectBy = 'IPV4Address'
        SelectItems = {'item': ip}
    else:
        SelectBy = 'Name'
        SelectItems = {}
    CmSelectionCriteria = {
        'MaxReturnedDevices': max,
        'DeviceClass': 'Phone',
        'Model': '255',
        'Status': 'Registered',
        'SelectBy': SelectBy,
        'SelectItems': SelectItems
    }
    session = Session()
    session.verify = False
    session.auth = HTTPBasicAuth(axluser, axlpassword)
    transport = Transport(cache=SqliteCache(), session=session, timeout=5)
    history = HistoryPlugin()
    client = Client(wsdl=riswsdl, transport=transport, plugins=[history])

    def show_history():
        for item in [history.last_sent, history.last_received]:
            print(etree.tostring(item["envelope"], encoding="unicode", pretty_print=True))

    Out = []
    i = 0
    try:
        resp = client.service.selectCmDevice(CmSelectionCriteria=CmSelectionCriteria, StateInfo=StateInfo)
        result = resp['SelectCmDeviceResult']['CmNodes']['item']
        for node in result:
            if node['CmDevices'] != None:
                 for device in node['CmDevices']['item']:
                    OutIp = device['IPAddress']['item'][0]['IP']
                    OutModel = device['Model']
                    OutDesc = device['Description']
                    OutNum = device['DirNumber'].replace('-Registered', '')
                    Out.append({'ip': OutIp, 'model': OutModel, 'desc': OutDesc, 'num': OutNum})
                    if Print: print(str(list(Out[i].values())))
                    i += 1
    except Fault:
        show_history()
        return []
    return Out

session = Session()
session.verify = False
session.auth = HTTPBasicAuth(axluser, axlpassword)
transport = Transport(cache=SqliteCache(), session=session, timeout=5)
history = HistoryPlugin()
client = Client(wsdl=wsdl, transport=transport, plugins=[history])
service = client.create_service(binding, location)

def getappuser(userid):
    try:
        resp = service.getAppUser(userid = userid)
        result = resp['return']['appUser']
    except Fault:
        show_history()
        result = {}
    return result

def appuser_add_device(userid, device):
    appuser = getappuser(userid)
    devices = appuser['associatedDevices']['device']
    if device in devices:
        result = 'Unchanged'
    else:
        devices.append(device)
        newdevices = {'device': devices }
        try:
            service.updateAppUser(userid = userid, associatedDevices = newdevices)
            result = 'Success'
        except Fault:
            show_history()
            result = 'Error'
    return result
    
def appuser_remove_device(userid, device):
    appuser = getappuser(userid)
    devices = appuser['associatedDevices']['device']
    if device not in devices:
        result = 'Unchanged'
    else:
        devices.remove(device)
        newdevices = {'device': devices }
        try:
            service.updateAppUser(userid = userid, associatedDevices = newdevices)
            result = 'Success'
        except Fault:
            show_history()
            result = 'Error'
    return result

def ccm_appuser_reassign(userid, phone, number):
    if appuser_remove_device('callrec', phone) == 'Success':
        print('Removed {}, number {}'.format(phone, number))
        if appuser_add_device('callrec', phone) == 'Success':
            print('Added {}, number {}'.format(phone, number))
            result = 'Success'
        else:
            result = 'Error on adding'
    else:
        result = 'Error on removing'
    return result
