# Cryostat monitoring
Cryostat monitoring is a program that monitors cooldown and warmup processes and
sends messages on a Discord channel when the desired temperatures have been reached.


## Installation
Install the necessary packages:

pip install -r requirements.txt

Configure the config.ini file. You can start from config_template.ini and change
the MQTT hostname to the IP address of your specific temperature controller API.
Then, enter the URL of the Discord channel to which you want to send the messages
as well as the access token of the Discord user you want to send them with.
Infos about how to find the channel id and the access token can be found here:
[Video](https://youtu.be/DArlLAq56Mo)
If you want, you can also change the default threshold temperatures for the
different steps during the cooldown and warmup processes.


## Usage
Run the cryostat_monitoring.py program to open up a simple user interface.
It will ask you to choose which program mode you want to start. Available modes are:
1. Full Cooldown
2. Cooldown to 4K
3. Warmup
4. Condensing
5. Cold Insert
6. Circulation Mode

These modes all monitor the temperatures until they reach the specified threshold
and then send a message. For example, Full Cooldown monitors the still temparture until
it is cold enough for condensation, then the MXC until it reaches base temperature.
After that, it enters a Circulation Mode, which continually monitors the MXC temperature
and return a warning when it heats up too much.