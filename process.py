lPort = 5345
mPort = 53939
mHost = "128.10.12.131"
otherHosts = {1: 'xinu01.cs.purdue.edu', 2: 'xinu02.cs.purdue.edu', 3: 'xinu03.cs.purdue.edu', 4: 'xinu04.cs.purdue.edu', 5: 'xinu05.cs.purdue.edu', 6: 'xinu06.cs.purdue.edu', 7: 'xinu07.cs.purdue.edu', 8: 'xinu08.cs.purdue.edu', 9: 'xinu09.cs.purdue.edu', 10: 'xinu10.cs.purdue.edu'}
waitTill = 1458704772.1
maxCrashes = 0
maxMsgLen = 1024
import sys
import os
from socket import *
from select import select
import SocketServer
from subprocess import Popen, PIPE
import time
import random
from sets import Set
myName = gethostname()
emptyVal = -2
heartBeat = -3
voteRequest = -4
acceptVoteRequest = -5
rejectVoteRequest = -6
myId = emptyVal
currentValues = {}
currentLeader = emptyVal
acceptedHosts = Set([])
currentState = 0   # 0 for follower 1 for candidate 2 for leader
leader = 2; candidate = 1; follower = 0;
currentTerm = 0 # everyone starts in 0th term
currentElectionRound = 0
timeoutRangeMin = 100 # this is in millisecond
timeoutRangeMax = 500 # this is in millisecond
electionTimeout = 0 # this will be set in main for the first time
heartBeatTimeout = 0 # useful only if I am leader
votedForThisTerm = False

def sendLog(msg,level):
    if level<1:
        return
    #print(msg)
    msg = time.strftime("%H:%M:%S", time.localtime(time.time())) + " -- HID: "+str(myId)+ " --  Current Term: " + str(currentTerm) + " -- " +msg
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

def sendVoteRequestToAll(): 
    for host in otherHosts.keys():
        sendVoteRequestTo(host)

def sendVoteRequestTo(host):
    sendTo(host,voteRequest)

def sendHeartBeatToAll():
g   for host in otherHosts.keys():
        sendHeartBeatTo(host)
    refreshHeartBeatTimeout()

def sendHeartBeatTo(hid):
    if currentState == leader:
        sendTo(hid,heartBeat)

def refreshHeartBeatTimeout():
    global heartBeatTimeout
    heartBeatTimeout = int(round(time.time()*1000)+timeoutRangeMin/2)

def setCurrentTermTo(this): # sets only if this is greater than currentTerm
    global currentTerm
    global votedForThisTerm
    if this > currentTerm:
        currentTerm = this
        votedForThisTerm = False

def setCurrentLeaderTo(this):
    global currentLeader
    if currentLeader != this:
        sendLog("New leader is Node: "+str(this),2)
    currentLeader = this
    setCurrentElectionRoundTo(0)

def setCurrentElectionRoundTo(this):
    global currentElectionRound
    currentElectionRound = this

def setCurrentStateTo(this):
    global currentState
    currentState = this

def refreshElectionTimeout():
    global electionTimeout
    electionTimeout = int(round(time.time()*1000)+random.uniform(timeoutRangeMin,timeoutRangeMax))

def sendToAll(value):
    for host in otherHosts.keys():
        sendTo(host,value)

def sendTo(hid, value):
    hName = otherHosts[hid]
    s = socket(AF_INET,SOCK_DGRAM)
    data = str(myId)+" "+str(currentTerm)+" "+str(value)
    s.sendto(data, (hName,lPort))
    s.close()
    sendLog("sending: "+ str(value) +" to : "+hName,0)

def recvMsg(sock):
    msg, addr = sock.recvfrom(maxMsgLen)
    msg = msg.split()
    sendersId = int(msg[0])
    sendersTerm = int(msg[1])
    sendersValue = int(msg[2])
    sendLog("recvd: "+ str(sendersValue) +" from : "+str(sendersId),0)
    actOnMsg(sendersId, sendersTerm, sendersValue)

def voteFor(this): 
    global votedForThisTerm
    votedForThisTerm = True
    if this != myId:
        sendTo(this,acceptVoteRequest)
    else:
        voteRequestAcceptedBy(myId)
    refreshElectionTimeout()

def voteRequestAcceptedBy(this):
    global acceptedHosts
    global currentElectionRound
    acceptedHosts.add(this)
    if len(acceptedHosts)> ((len(otherHosts)+1)/2):
        if currentElectionRound > maxCrashes:
            becomeLeader()
        else:
            startNewElectionRound()

def becomeLeader():
    setCurrentElectionRoundTo(0)
    setCurrentStateTo(leader)
    setCurrentLeaderTo(myId)
    sendLog("Became leader",2)
    sendHeartBeatToAll()

def actOnMsg(sendersId, sendersTerm, sendersValue):
    if currentTerm>sendersTerm:
        return
    elif currentTerm == sendersTerm:
        if sendersValue == heartBeat:
            refreshElectionTimeout()
            setCurrentStateTo(follower)
            if currentLeader != sendersId:
                setCurrentLeaderTo(sendersId)
        elif sendersValue == voteRequest:
            if votedForThisTerm or currentState == candidate:
                sendTo(sendersId,rejectVoteRequest)
            else:
                voteFor(sendersId)
        elif sendersValue == acceptVoteRequest:
            voteRequestAcceptedBy(sendersId)
    else:
        setCurrentTermTo(sendersTerm)
        setCurrentStateTo(follower)
        if sendersValue == heartBeat:
            refreshElectionTimeout()
            if currentLeader != sendersId:
                setCurrentLeaderTo(sendersId)
        elif sendersValue == voteRequest:
            if votedForThisTerm or currentState == candidate:
                sendTo(sendersId,rejectVoteRequest)
            else:
                voteFor(sendersId)

def initiateElection():
    sendLog("Initiating Election",2)
    setCurrentTermTo(currentTerm + 1)
    setCurrentElectionRoundTo(0)
    setCurrentStateTo(candidate)
    startNewElectionRound()

def startNewElectionRound():
    setCurrentElectionRoundTo(currentElectionRound+1)
    acceptedHosts = Set([])
    voteFor(myId)
    sendVoteRequestToAll()

if __name__ == "__main__":
        # formatting global parameters
    setUpCommonParameters()
        # making udp socket to listen
    listner = socket(AF_INET, SOCK_DGRAM)
    listner.bind((myName,lPort))
    sendLog("binded",0)
        # sleeping to ensure that every one gets binded before anyone starts sending
    time.sleep(2*len(otherHosts)+15)
    refreshElectionTimeout()
    refreshHeartBeatTimeout()
    timeout = 1*len(otherHosts)
    timeoutAt = time.time()+10*60
        # entering into infi loop
    while time.time()<timeoutAt:
        reader, writer, excep = select([listner],[],[],timeout)
        if reader:
            recvMsg(reader[0])
        if electionTimeout<=int(round(time.time()*1000)) and currentState != leader and currentElectionRound == 0:
            initiateElection()
        if currentState == leader and heartBeatTimeout<=int(round(time.time()*1000)):
            sendHeartBeatToAll()
    sendLog("Leader is "+str(max(currentValues.values())),2)
    sendLog("currentVal is: "+str(currentValues.values()),0)


