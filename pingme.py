#!/usr/bin/python3

import signal
import sys
import os.path
from re import match
import time
import socket
import argparse
import smtplib
import configparser
from datetime import datetime
from email.message import EmailMessage
# from multiping import multi_ping, MultiPingError


demonised = False
version = 1.08
downHosts = {}


class Unavail:
    hosts = {}

    def __init__(self):
        pass

    def pop(self):
        if item['host'] in unavail:
            popUnavail(unavail)

        if unavail[item['host']] != -1:
            downtime = int(time.time() - unavail[item['host']])

            if options['email'] is not False:
                kwargs = {
                    'subject': "ceci est un test",
                    'body': "1 ceci est un test"
                }

                kwargs.update(options['email'])

                sendEmail(**kwargs)

        del unavail[item['host']]

    def push(self):
        if item['host'] not in unavail:
            pushUnavail(unavail)

            if first:
                unavail[item['host']] = -1  # is not open
            else:
                unavail[item['host']] = time.time()
                if options['email'] is not False:
                    kwargs = {
                        'subject': "ceci est un test",
                        'body': "2 ceci est un test"
                    }

                    kwargs.update(options['email'])

                    sendEmail(**kwargs)



class GracefulKiller:
    killNow = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exitGracefully)
        signal.signal(signal.SIGTERM, self.exitGracefully)

    def exitGracefully(self, signum, frame):
        self.killNow = True


def scanPort(host, port):
    """
    This method returns True if the port listen to request.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)

    try:
        sock.connect((host, port))
    except socket.error:
        return False
    finally:
        sock.close()

    return True


class Email:
    """cvxcv"""

    def __init__(self, server, port, username, password, starttls=False):
        """cvxcv"""
        pass

    def send(self, subject, sender, to, body,  cc=None, bcc=None):
        """Permet l'envoi de courriel"""
        error = False
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = to

        if cc:
            msg['Cc'] = cc
        if bcc:
            msg['Bcc'] = bcc
        msg.set_content(body)

        with smtplib.SMTP(server, port) as ssmtp:
            try:
                ssmtp.ehlo()  # Can be omitted
                if starttls is True:
                    ssmtp.starttls()
                ssmtp.ehlo()  # Can be omitted
                ssmtp.login(username, password)
                ssmtp.send_message(msg)
            except smtplib.SMTPServerDisconnected:
                error = True

        return not error

# def ping(killer, addrs, retries=3):
#     return False

# def runPing(killer, addrs, retries=3):
#     if retries < 1:
#         retries = 1

#     responses = noResponses = []

#     while retries > 0:
#         retries -= 1

#         try:
#             responses, noResponses = multi_ping(addrs, timeout=10, retry=5)
#         except MultiPingError as e:
#             print("PingMe Error : ", end='', flush=True)
#             print(e, flush=True)
#             exit(1)

#         except Exception as e:
#             print("PingMe Error : ", end='', flush=True)
#             print(e, flush=True)
#             print("Check your IP address", flush=True)
#             exit(1)

#         if not noResponses:
#             break

#         wait = time.time()
#         while not killer.killNow and time.time() - 5 > wait:
#             time.sleep(0.1)

#         if killer.killNow:
#             return

#     if noResponses:
#         notify = False

#         for host in noResponses:
#             if host not in downHosts:
#                 downHosts[host] = time.time()
#                 notify = True

#         if notify:
#             if demonised:
#                 print("Host down : " + ", ".join(downHosts.keys()), flush=True)
#                 sendMessage(receiverEmail, ("H??te injoignables: "
#                                             + ", ".join(downHosts.keys()), " DOWN"))
#             else:
#                 print("[{:%Y-%m-%d %H:%M:%S}] Host down : ".format(datetime.now())
#                       + ", ".join(downHosts.keys()), flush=True)

#     downTime = {}
#     for host in responses:
#         if host in downHosts:
#             downTime[host] = int(time.time() - downHosts[host])
#             del downHosts[host]

#     if downTime:
#         strHosts = ", ".join(["{} (downtime={}secs)".format(ip, dt) for ip, dt in downTime.items()])

#         if demonised:
#             print("Host up : " + strHosts, flush=True)
#             sendMessage(receiverEmail, "H??te redevenus joignables: " + strHosts, " UP")
#         else:
#             print("[{:%Y-%m-%d %H:%M:%S}] Host up : ".format(datetime.now()) + strHosts, flush=True)


def parseConfig(filename):
    """Read the config file"""

    opts = {}

    try:
        config = configparser.ConfigParser()
        config.read(filename)

        # Read email options
        if 'email' in config.sections():
            opts['email'] = {}
            opts['email']['server'] = config.getboolean('email', 'send_email')
            opts['email']['port'] = config.getint('email', 'port', fallback=25)
            # opts['email']['subject'] = config.get('email', 'send_email', fallback="Pingme email")
            opts['email']['starttls'] = config.getboolean('email', 'starttls', fallback=False)
            opts['email']['server'] = config.get('email', 'server').lower()
            opts['email']['username'] = config.get('email', 'username')
            opts['email']['password'] = config.get('email', 'password')
            opts['email']['sender'] = config.get('email', 'from').lower()
            opts['email']['to'] = config.get('email', 'to').lower()
            opts['email']['cc'] = config.get('email', 'cc', fallback="").lower()
            opts['email']['bcc'] = config.get('email', 'bcc', fallback="").lower()
        else:
            opts['email'] = False

        # Read hosts informations
        opts['hosts'] = []
        for section in config.sections():
            if section.lower() in ('email', ):
                continue

            if not config.getboolean(section, 'active', fallback=True):
                continue

            opts['hosts'].append({
                'title': section,
                'name': config.get(section, 'name', fallback="") or section,
                'scan_port': config.getboolean(section, 'scan_port', fallback=False),
                'ping': config.getboolean(section, 'ping', fallback=False),
                'host': config.get(section, 'host'),
                'port': config.getint(section, 'port', fallback=80),
            })

    except configparser.Error as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.stderr.flush()
        return False

    return opts




def main():
    """Main method"""
    parser = argparse.ArgumentParser(description='Check if a port for a host is open or close and send a alert.')
    parser.add_argument('--config', '-c', default='pingme.ini', help='path to config file')
    parser.add_argument('--log', '-l', default=None, help='path to log file')
    parser.add_argument('--demonised', '-d', action='store_true', help='path to log file')

    args = parser.parse_args()
    error = False

    # Check config file
    if not os.path.exists(args.config):
        sys.stderr.write(f"Error: unable to read config file '{args.config}'\n")
        sys.stderr.flush()
        error = True

    # Check log file
    if args.log is not None and not os.path.exists(args.log):
        sys.stderr.write(f"Error: unable to read log file '{args.log}'\n")
        sys.stderr.flush()
        error = True

    options = parseConfig(args.config)

    # Stop the programm
    if error:
        sys.exit(1)

    # sendMessage("myemail@domain", "PingMe service START : " + ", ".join(hosts))

    sys.stdout.write(f"Pingme {version} (Press Ctrl+c to stop)...\n")
    sys.stdout.flush()

    # if demonised:
    #     print("Host to ping : " + ", ".join(hosts), flush=True)
    # else:
    #     print("[{:%Y-%m-%d %H:%M:%S}] Host to ping : ".format(datetime.now()) + ", ".join(hosts), flush=True)

    killer = GracefulKiller()
    # cycle = time.time()

    # For Ctrl+c signal.
    first = True
    unavail = Unavail()

    while not killer.killNow:
        for item in options['hosts']:
            sys.stdout.write(f"Scan port : {item['host']}:{item['port']}  ")

            if scanPort(item['host'], item['port']):
                sys.stdout.write("[open]\n")
                unavail.pop(item)
            else:
                sys.stdout.write("[close]\n")
                unavail.push(item)
            # endif

            sys.stdout.flush()

            if first:
                first = False

        time.sleep(15)

    sys.exit(0)


if __name__ == '__main__':
    main()


# if time.time() - interval > cycle:
#     cycle = time.time()
#     # runPing(killer, hosts, 4)

# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.settimeout(2)                                      #2 Second Timeout
# result = sock.connect_ex(('127.0.0.1',80))
# if result == 0:
#   print 'port OPEN'
# else:
#   print 'port CLOSED, connect_ex returned: '+str(result)

# ***************************************************

# print("[{:%Y-%m-%d %H:%M:%S}] Exit".format(datetime.now()))
    #sendMessage("myemail@domain", "PingMe service STOP : " + ", ".join(hosts))

# import socket

# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.settimeout(2)                                      #2 Second Timeout
# result = sock.connect_ex(('127.0.0.1',80))
# if result == 0:
#   print 'port OPEN'
# else:
#   print 'port CLOSED, connect_ex returned: '+str(result)


# import socket
# from contextlib import closing

# def check_socket(host, port):
#     with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
#         if sock.connect_ex((host, port)) == 0:
#             print("Port is open")
#         else:
#             print("Port is not open")