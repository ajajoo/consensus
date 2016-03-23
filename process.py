lPort = 5345
mPort = 53939
mHost = "128.10.12.131"
otherHosts = {1: 'xinu01.cs.purdue.edu', 2: 'xinu02.cs.purdue.edu', 3: 'xinu03.cs.purdue.edu', 4: 'xinu04.cs.purdue.edu', 5: 'xinu05.cs.purdue.edu', 6: 'xinu06.cs.purdue.edu', 7: 'xinu07.cs.purdue.edu', 8: 'xinu08.cs.purdue.edu', 9: 'xinu09.cs.purdue.edu', 10: 'xinu10.cs.purdue.edu'}
waitTill = 1458704772.1
maxMsgLen = 1024
import sys
import os
from socket import *
from select import select
import SocketServer
from subprocess import Popen, PIPE
import time
myName = gethostname()
emptyVal = -2
myId = emptyVal
currentValues = {}
received = 0
state = 0   #

def sendLog(msg,level):
    if level<1:
        return
    #print(msg)
    msg = time.strftime("%H:%M:%S", time.localtime(time.time())) + " -- HID: "+str(myId)+" -- "+msg
    sock = socket(AF_INET,SOCK_STREAM)
    sock.connect((mHost, mPort))
    try:
        sock.sendall(msg)
    finally:
        sock.close()

def setUpCommonParameters():    # deletes self from host dict and sets myId
    global myId
    for i in otherHosts:
        if otherHosts[i] == myName:
            del otherHosts[i]
            myId = i
            break

def sendToAll(value):
    for host in otherHosts.values():
        sendTo(host,value)

def sendTo(hName, value):
    s = socket(AF_INET,SOCK_DGRAM)
    data = str(myId)+" "+str(value)
    s.sendto(data, (hName,lPort))
    s.close()
    sendLog("sending: "+ str(value) +" to : "+hName,0)

def recvMsg(sock):
    msg, addr = sock.recvfrom(maxMsgLen)
    msg = msg.split()
    senderId = int(msg[0])
    value = int(msg[1])
    currentValues[senderId] = value
    sendLog("recvd: "+ str(value) +" from : "+str(senderId),0)

def propose(hName, value):
    sendLog("starting propose",0)
    currentValues[myId] = value
    if hName == "":
        sendToAll(value)
    else:
        sendTo(hName, value)

if __name__ == "__main__":
        # formatting global parameters
    setUpCommonParameters()
        # making udp socket to listen
    listner = socket(AF_INET, SOCK_DGRAM)
    listner.bind((myName,lPort))
    sendLog("binded",0)
        #sleeping to ensure that every one gets binded before anyone starts sending
    time.sleep(3*len(otherHosts))
    propose("",myId)
        #entering into infi loop
    timeout = 1*len(otherHosts)
    timeoutAt = time.time()+timeout
    while time.time()<timeoutAt:
        reader, writer, excep = select([listner],[],[],timeout)
        if reader:
            recvMsg(reader[0])
    sendLog("Leader is "+str(max(currentValues.values())),2)
    sendLog("currentVal is: "+str(currentValues.values()),0)


