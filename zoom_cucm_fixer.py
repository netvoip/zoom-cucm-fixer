#/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import configparser
import textfsm
import subprocess

from cucm_axl import cucm_rt_phones, ccm_appuser_reassign
from netmiko import ConnectHandler
from datetime import datetime

Timestart = datetime.now()
path = os.path.dirname(os.path.abspath( __file__ ))
with open(os.path.join(path, 'vars.conf')) as config:
    vars = configparser.ConfigParser()
    vars.read_file(config)
zoomhost = vars['zoom']['zoomhost']
zoomuser = vars['zoom']['zoomuser']
zoompass = vars['zoom']['zoompass']
zoomsupass = vars['zoom']['zoomsupass']
zoomconnectmode = vars['zoom']['zoomconnectmode']
checkafter = vars['zoom']['checkafter'].lower()
viewonly = vars['zoom']['viewonly'].lower()
zoomdict = {'ip': zoomhost, 'device_type': 'linux', 'username': zoomuser, 'password': zoompass}
command = "callrec-status | grep 'Terminal'"

def ssh_surun(command):
    callrec_output = ''
    with ConnectHandler(**zoomdict) as ssh:
        ssh.send_command_timing('su -')
        ssh.send_command_timing(zoomsupass)
        callrec_output = ssh.send_command_timing(command, delay_factor=4)
    return callrec_output

def zoom_find_broken_terminals(callrec_output):
    try:
        with open('zoom_terminals.template') as template:
            fsm = textfsm.TextFSM(template)
            #header = fsm.header
            fsmresult = fsm.ParseText(callrec_output)
            fsmdicts = [dict(zip(fsm.header, row)) for row in fsmresult]
    except:
        fsmdicts = ''
    
    broken_devices = []
    for i in fsmdicts:
        if i['status_inservice'] == 'false':
            a = cucm_rt_phones(name = i['phone'], Print = False)
            if len(a) > 0:
                broken_devices.append(i)
    return broken_devices

def connect_and_get_broken(method):
    if method == 'ssh':
        callrec_output = ssh_surun(command)
    elif method == 'file':
        with open('output.txt', 'r') as file:
            callrec_output = file.read()
    elif method == 'local':
        p1 = subprocess.Popen(["callrec-status"], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["grep", "Terminal"], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        callrec_output = p2.communicate()[0].decode('utf-8')
    broken_devices = zoom_find_broken_terminals(callrec_output)
    return broken_devices

broken_devices = connect_and_get_broken(zoomconnectmode)
if viewonly == 'true':
    if len(broken_devices) > 0:
        print('Problem devices:\n', broken_devices)
else:
    fixed_devices = []
    for i in broken_devices:
        i['result'] = ccm_appuser_reassign('callrec', i['phone'], i['number'])
        fixed_devices.append(i)

if (checkafter == 'true') and (viewonly != 'true'):
    if len(broken_devices) > 0:
        broken_devices = connect_and_get_broken(zoomconnectmode)
        if len(broken_devices) == 0:
            print('No problem devices left!')
        else:
            print('\nProblem devices are still left:')
            print('\n'.join(map(str, broken_devices))) 
