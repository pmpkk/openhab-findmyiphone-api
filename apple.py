#
# Use the Apple FindMyIphone API to send sound to devices
#

import json
import base64, getpass
import requests
import time
import urlparse
import sys
from myopenhab import openhab
from myopenhab import mapValues
from myopenhab import getJSONValue


#   API Gateway
API_ROOT_URL = 'https://fmipmobile.icloud.com/fmipservice/device/'

class appleFMIP(object):
    """
    
    A wrapper for the Apple FindMyIphone API

    """
    def __init__(self):

        self.debug = True 
        self.oh = openhab()
        self.loadCredentials()


    def loadCredentials(self):

        try:
            self.accounts = json.loads(self.oh.getState('apple_accounts'))
        except:
            self.accounts = {}
        try:
            self.devices = json.loads(self.oh.getState('apple_device_list'))
        except:
            self.devices = {}


    def call(self, path, account, mode=None, headers=None, payload=None):
        """
        Call the API at the given path.
        """
        
        if headers is None:
            headers = {
                'X-Apple-Realm-Support': '1.0',
                'Authorization': 'Basic %s' % base64.b64encode("%s:%s" % (account, self.accounts[account]['password'])),
                'X-Apple-Find-API-Ver': '3.0',
                'X-Apple-AuthScheme': '%s' % 'UserIDGuest',
                'User-Agent': 'FindMyiPhone/500 CFNetwork/758.4.3 Darwin/15.5.0',
            }

        if mode == "POST":
            r = requests.post(API_ROOT_URL + account + '/' + path,  headers=headers, data=payload)
            if(r.status_code < 200 and r.status_code > 299):
                print "Response Code = " + str(r.status_code)
                print r.content
            return r.json()
        elif mode == "PUT":
            r = requests.put(API_ROOT_URL + account + '/' + path,  headers=headers, data=payload)
            if(r.status_code < 200 and r.status_code > 299):
                print "Response Code = " + str(r.status_code)
                print r.content
            return r.json()
        else:
            r = requests.get(API_ROOT_URL + account + '/' + path,  headers=headers)
            if(r.status_code < 200 and r.status_code > 299):
                print "Response Code = " + str(r.status_code)
                print r.content
            return r.json()
      
    def updateDevices(self):
        """
        Get List of Devices.
        """
        
        print "-- Calling Service: Update Devices"

        try:
            devices = {}

            for account in self.accounts:
                print "Getting devices for " + account + ":"

                resp = self.call("initClient", account, "POST")

                if (self.debug): print resp

                if('content' in resp):
                    deviceList = getJSONValue(resp, ['content'])
                    print "Apple responded with %s devices." % len(deviceList)

                    devices[account] = { 'name': self.accounts[account]['name'], 'deviceList': deviceList }
                else:
                    print " \033[91m-> Error connecting to Apple: Invalid Credentials\033[0;0m"

            self.devices = devices
            self.oh.sendCommand('apple_device_list', json.dumps(devices, sort_keys=True, indent=4, separators=(',', ': ')))

        except:
            print " -> Error Get Devices: " + str(sys.exc_info()[1])

    def verifyAccount(self, account):
        """
        Check if account credentials are good
        """
        
        print "-- Calling Service: Authentication"

        try:

            resp = self.call("initClient", account, "POST")

            if (self.debug): print resp

            if('content' in resp):
                deviceList = getJSONValue(resp, ['content'])
                print " -> Your account has %s associated devices." % len(deviceList)
                print " -> Authentication successful. Adding account credentials to OpenHab."

                self.accounts[account]['name'] = getJSONValue(resp, ['userInfo', 'firstName']) + ' ' + getJSONValue(resp, ['userInfo', 'lastName'])
                self.saveCredentials()

            else:
                print " \033[91m-> Error connecting to Apple: Invalid Credentials\033[0;0m"
                self.loadCredentials()

        except:
            print " \033[91m-> Error Authentication: " + str(sys.exc_info()[1]) + "\033[0;0m"
            self.loadCredentials()

    def saveCredentials(self):
        """
        Save current tokens to the openhab.
        """
        self.oh.sendCommand('apple_accounts', json.dumps(self.accounts, sort_keys=True, indent=4, separators=(',', ': ')))

    def getDeviceAccount(self, id):
        """
        Get account from device id
        """

        deviceAccount = ""

        for account in self.accounts:
            for device in self.devices[account]['deviceList']:
                if(device['id'] == id):
                    deviceAccount = account

        if(deviceAccount == ""):
            if self.debug: print "\033[91mDevice not found.\033[0;0m"
        else:
            if self.debug: print "Account for device is " + deviceAccount

        return deviceAccount

    def playSound(self, id):
        """
        Play sound ID
        """

        print "-- Calling Service: Play Sound"

        try:

            account = self.getDeviceAccount(id)

            headers = {
                'Accept':'*/*',
                'Authorization': 'Basic %s' % base64.b64encode("%s:%s" % (account, self.accounts[account]['password'])),
                'Accept-Encoding':'gzip, deflate',
                'Accept-Language':'en-us',
                'Content-Type':'application/json; charset=utf-8',
                'X-Apple-AuthScheme':'UserIDGuest',
            }

            data = { 
                'device': id, 
                'subject': 'ViPuRo',
            }

            resp = self.call("playSound", account, "POST", headers, json.dumps(data))
            if resp:
                print "Successfully sent command to Apple."
            else:
                print " \033[91m-> Error Playing Sound (Unknown).\033[0;0m"

            if (self.debug): print resp

        except:
            print " \033[91m-> Error Playing Sound: " + str(sys.exc_info()[1]) + "\033[0;0m"

    def addAccount(self):

        new_username = raw_input('Apple ID: ')
        new_password = getpass.getpass()

        if(new_username in self.accounts):
            self.accounts[new_username]['password'] = new_password
        else:
            self.accounts[new_username] = { 'password': new_password }

        #Try getting device list
        self.verifyAccount(new_username)

    def removeAllAccounts(self):

        self.accounts = {}
        self.saveCredentials()

        self.oh.sendCommand('apple_device_list', "{}")

        print "All accounts have been removed from OpenHAB."

    def setup(self):
        """
        Play sound ID
        """

        print "\033[0;93m-----------------------------\033[0m"
        print "\033[0;93m SETUP MENU\033[0m"

        q = "0"
        while True:

            print "\033[0;93m-----------------------------\033[0m"

            if (len(self.accounts) == 0):
                print "\033[91mNo account set up yet. Please enter your credentials to add an account.\033[0;0m"
            else:
                print "%s account(s) set up:" % len(self.accounts)
                for account in self.accounts:
                    print "  Apple ID = \033[0;37m" + account + "\033[0m"
                    if(account in self.devices):
                        if('deviceList' in self.devices[account]):
                            for device in self.devices[account]['deviceList']:
                                print "    \033[0;36m" + device['name'].ljust(20) + "\033[0m \t\033[0;35m" ,
                                print device['deviceDisplayName'].ljust(20) + "\033[0m" ,
                                if q == "8": print device['id'].ljust(20) + "\033[0m" ,
                                print ""
                        else:
                            print "      \033[91mHmm. There are no devices for this account. Try getting devices for all accounts.\033[0;0m"
                    else:
                        print "      \033[91mHmm. There are no devices for this account. Try getting devices for all accounts.\033[0;0m"

            print "\033[0;93m-----------------------------"
            print "Options:"
            print " 1 - Add new or update existing account in OpenHAB"
            print " 2 - Remove all accounts & devices from OpenHAB"
            print " 5 - Get devices for all accounts from Apple and update OpenHAB"
            print " 8 - Show device IDs"
            print " 9 - Exit\033[0m"
            q = raw_input('What would you like to do? [1-9] ')
            if (q == "9"):
                print "Good bye!"
                break
            if (q == "1"):
                self.addAccount()
            if (q == "2"):
                self.removeAllAccounts()
            if (q == "5"):
                self.updateDevices()

    def updateConnectionDateTime(self):
        self.oh.sendCommand('apple_lastConnectionDateTime',time.strftime("%Y-%m-%dT%H:%M:%S+0000",time.gmtime(time.time())))     

def main():

    t1 = time.time()

    c = appleFMIP()

    args = sys.argv
    
    if(len(args) == 1):
        print '\033[91mNo parameters specified\033[0;0m'
    else:
        if(args[1] == "update_devices"):
            c.updateDevices()
        if(args[1] == "get_device_account"):
            c.getDeviceAccount(args[2])
        if(args[1] == "play_sound"):
            c.playSound(args[2])
        if(args[1] == "setup"):
            c.setup()

    c.updateConnectionDateTime()

    t2 = time.time()
    print "Done in " + str(t2-t1) + " seconds"

if __name__ == '__main__':
    main()
