### Introduction
Due to existing bug of Cisco UCM sometimes JTAPI control of some devices may be lost by application user. It is especially sensitive when you have call recording software using JTAPI such as Zoom Callrec. This script will check which phones Zoom have lost control and compare it to current device status on CUCM. If device is active it will reassign such device for callrec user.
Also you can use functions from this script to manually tie or untie device from application user.

### Setup
Python 3 with modules: `netmiko, textfsm, zeep`.

Actual version of WSDL schema must be placed to 'axl' directory. These files you can obtain as part of Cisco AXL Toolkit from your CallManager. Example files are for 11.5 version.

Add to your cron like for example  
`*/10 * * * * root cd /opt/scripts/zoom-cucm-fixer && /root/.virtualenvs/cucm/bin/python zoom_cucm_fixer.py >> log.txt`

### vars.conf definition
```
[cucm]
ip = cucm # Address of CUCM with "Cisco AXL Web Service" running
axluser = axladmin # User with "Standard AXL API access" role assigned
axlpassword = 123 # Password of user

[zoom]
zoomhost = zoom # Address of zoom server if SSH connection is used
zoomuser = admin # Username of user to connect over SSH
zoompass = 123 # Password of user
zoomsupass = 123 # You need define root password if order to run callrec-status command. Not secure! Use local method instead
zoomconnectmode = local # You can run retrieve status locally (local) or over SSH (ssh)
checkafter = True # Check for broken devices after reassignment. Required to make sure problems are fixed
viewonly = False # Retrieve broken devices without fixing
```

### Bugs and requests
You can contact me at conftdowr@gmail.com.