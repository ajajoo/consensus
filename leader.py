import sys
import os
import re
import numpy as np
import subprocess
#import paramiko
import getpass
import socket
import SocketServer
from subprocess import Popen, PIPE
import time

def raiseError(message="", exit = False, exitCode = 1):
    print message
    if exit:
        sys.exit(exitCode)

def checkArgValidity():
    if len(sys.argv)<7:
        raiseError(message="Too few arguments.", exit = True)
    if len(sys.argv)>7:
        raiseError(message="Too many arguments.", exit = True)
    
    arg = sys.argv[2]   #ports
    if (arg.isdigit()==False):
        raiseError(message="Port should be integer.", exit = True)
    elif 1023<int(arg)<65536:
        pass
    else:
        raiseError(message="Port is out of range.", exit = True)
    
    arg = sys.argv[4]   #hostFile
    numHost = sum(1 for line in open(arg))
    if numHost<1:
        raiseError(message="Hostfile is empty", exit = True)
    
    arg = sys.argv[6]   #maxCrashes
    if (arg.isdigit()==False):
        raiseError(message="Number of max crash should be integer.", exit = True)
    elif 0<int(arg)<numHost-2:
        pass
    else:
        raiseError(message="Max crash is out of range.", exit = True)

    return int(sys.argv[2]), sys.argv[4] ,int(sys.argv[6])

def getLoginInfo():
    uname = raw_input("Please enter user name to be used to login on other: ")
    pwd = getpass.getpass()
    return uname, pwd

def editFile(filePath,lineNums,newLines):
    f =  open(filePath)
    temp = f.readlines()
    f.close()
    for x in range(len(lineNums)):
        temp[lineNums[x]] = newLines[x]
    f = open(filePath,'w')
    for line in temp:
        f.write(line)
    f.close()

class ForkingTCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):# change this appropriately
    	msg = self.request.recv(1024)
        print(msg)
        #self.request.sendall(1)

class ForkingTCPServer(SocketServer.ForkingMixIn, SocketServer.TCPServer): # its necessary to pass ForkingMixIn 
    pass

def setUpMessagePrinter(): 
    server = ForkingTCPServer((socket.gethostname(), 1211), ForkingTCPRequestHandler)
    #server.timeout = 90
    server.max_children = 100
    server.request_queue_size = 100
    #ip, port = server.server_address # Fork a new process with the server -- that process will then fork one more process for each request
    t = os.fork()
    if  t==0:
    	print "Message printer at: ", os.getpid()
    	server.serve_forever()
    return server.server_address


class Host(object):
    def __init__(self, hid, hname, pathToScript):# uname, pwd):
        self.id = hid;
        self.name = hname;
        #return self
    #def execute(self, pathToScript, uname, pwd):
        command = 'python '+pathToScript
        ssh = subprocess.Popen(["ssh", "%s" %self.name, command],shell=False,stdout=None, stderr=None, stdin=None)
        #ssh = paramiko.SSHClient() #ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())#ssh.connect(hostname = self.name, username=uname, password=pwd)#stdin, stdout, stderr = ssh.exec_command(command)#ssh.close()

if __name__ == '__main__':
    lPort, hostFile, maxCrashes = checkArgValidity()
    #uname, pwd = getLoginInfo()
    processScript = os.getcwd()+'/process.py'
    mHost, mPort = setUpMessagePrinter()
    hosts = {}
    with open(hostFile, 'r') as hf:
        for line in hf:
            x = line.split()
            hosts[int(x[0])] = x[1]
    editFile(processScript,[0,1,2,3,4],['lPort = '+str(lPort)+'\n','mPort = '+str(mPort)+'\n','mHost = \"'+str(mHost)+'\"\n','otherHosts = '+str(hosts)+'\n','waitTill = '+str(time.time()+5)+'\n'])
    for hid in hosts:
        Host(hid, hosts[hid], processScript)# uname, pwd)
