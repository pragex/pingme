#!/usr/bin/python3
import signal
from re import match
import time
import socket
import smtplib
from datetime import datetime
from email.message import EmailMessage
from multiping import multi_ping, MultiPingError

port = 587  # For starttls

demonised = False
version = 1.07
senderEmail = ""  # Your email server
receiverEmail = ""
smtpServer = ""
smtpUsername = ""
smtpPassword = ""
interval = 60
hosts = [""]
downHosts = {}


class GracefulKiller:
    killNow = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exitGracefully)
        signal.signal(signal.SIGTERM, self.exitGracefully)

    def exitGracefully(self, signum, frame):
        self.killNow = True


def getIP(fqdn):
    """
    This method returns the first IP address string
    that responds as the given domain name
    """

    if match(r'^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$', fqdn):
        return fqdn

    try:
        data = socket.gethostbyname(fqdn)
        return repr(data)
    except socket.error:
        return False


def sendMessage(toEmail, message, headAdd=""):
    msg = EmailMessage()
    msg['Subject'] = 'OVH - Surveillance des Hôtes' + headAdd
    msg['From'] = senderEmail
    msg['To'] = toEmail
    msg.set_content(message)

    with smtplib.SMTP(smtpServer, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls()
        server.ehlo()  # Can be omitted
        server.login(smtpUsername, smtpPassword)
        server.send_message(msg)


def runPing(killer, addrs, retries=3):
    if retries < 1:
        retries = 1

    responses = noResponses = []

    while retries > 0:
        retries -= 1

        try:
            responses, noResponses = multi_ping(addrs, timeout=10, retry=5)
        except MultiPingError as e:
            print("PingMe Error : ", end='', flush=True)
            print(e, flush=True)
            exit(1)

        except Exception as e:
            print("PingMe Error : ", end='', flush=True)
            print(e, flush=True)
            print("Check your IP address", flush=True)
            exit(1)

        if not noResponses:
            break

        wait = time.time()
        while not killer.killNow and time.time() - 5 > wait:
            time.sleep(0.1)

        if killer.killNow:
            return

    if noResponses:
        notify = False

        for host in noResponses:
            if host not in downHosts:
                downHosts[host] = time.time()
                notify = True

        if notify:
            if demonised:
                print("Host down : " + ", ".join(downHosts.keys()), flush=True)
                sendMessage(receiverEmail, ("Hôte injoignables: "
                                            + ", ".join(downHosts.keys()), " DOWN"))
            else:
                print("[{:%Y-%m-%d %H:%M:%S}] Host down : ".format(datetime.now())
                      + ", ".join(downHosts.keys()), flush=True)

    downTime = {}
    for host in responses:
        if host in downHosts:
            downTime[host] = int(time.time() - downHosts[host])
            del downHosts[host]

    if downTime:
        strHosts = ", ".join(["{} (downtime={}secs)".format(ip, dt) for ip, dt in downTime.items()])

        if demonised:
            print("Host up : " + strHosts, flush=True)
            sendMessage(receiverEmail, "Hôte redevenus joignables: " + strHosts, " UP")
        else:
            print("[{:%Y-%m-%d %H:%M:%S}] Host up : ".format(datetime.now()) + strHosts, flush=True)


if __name__ == '__main__':
    sendMessage("myemail@domain", "PingMe service START : " + ", ".join(hosts))

    print("*** Pingme {} ***".format(version), flush=True)
    if demonised:
        print("Host to ping : " + ", ".join(hosts), flush=True)
    else:
        print("[{:%Y-%m-%d %H:%M:%S}] Host to ping : ".format(datetime.now()) + ", ".join(hosts), flush=True)

    killer = GracefulKiller()
    cycle = time.time()

    while not killer.killNow:
        if time.time() - interval > cycle:
            cycle = time.time()
            runPing(killer, hosts, 4)

        time.sleep(0.1)

    # print("[{:%Y-%m-%d %H:%M:%S}] Exit".format(datetime.now()))
    sendMessage("myemail@domain", "PingMe service STOP : " + ", ".join(hosts))
    print("Exit", flush=True)


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