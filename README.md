# openhab-findmyiphone-api
Python script to allow OpenHAb (openhab.org) to send a "Find My iPhone Alert" to Apple devices.

<h1>Prerequisite</h1>

* OpenHab 2.1 installed on Raspberry Pi (or similar)
* OpenHab REST installed
* Apple iCloud User Account
* Python 2.7 installed
* Know your OpenHab root URL/IP and port. In this doc, I assume http://openhabianpi.local:8080/

<h1>Instructions</h1>

1. Add the apple.items file into openhab-conf/items and verify they have been added to your setup in Paper UI

2. Place the apple.py and myopenhab.py file into the openhab-conf/script folder.

3. Run the python script from shell to set up:

/usr/bin/python /etc/openhab2/scripts/apple.py setup

4. Add your account (option 1)

5. Refresh Device List (option 5)

<h1>Use</h1>

* apple.py
* parameters:
  * none = refresh data
  * setup = configure accounts
  * play_sound deviceid = trigger find my iphone alert by passing in device ID

*Use in OH Rule*

<pre>
rule "Find iPhone"
when
		Item apple_find_iphone received command ON
	then

		val resp =  executeCommandLine("/usr/bin/python /etc/openhab2/scripts/apple.py play_sound xxxx", 10000)
		logInfo("Apple", "Playing sound on iPhone.")		

end
</pre>
