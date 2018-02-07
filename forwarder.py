from multiprocessing import Process, Manager, Event
import select
import socket
import sys
import time

BUFFER_SIZE = 4096
QUEUE_SIZE = 128
RULE_FILE = 'entries.csv'
DEBUG_MODE = False

def readRules():
    # use dictionary to keep track of rules
    rules = {}
    ruleFile = open(RULE_FILE, 'r')
    # skip reading the first line of the rules file since it's just column descriptors
    # read a line from the rule file and strip the newline char at the end of each line
    ruleData = ruleFile.readlines()

    for rule in ruleData:
        # remove quotes and newline chars from each line in the .csv file and tokenize using comma as the delimiter
        rule = rule.replace('\"', '')

        appName, port, localIP, localPort = rule.rstrip().split(',')

        if port not in rules:
            rules[port] = ['%s:%s' % (localIP, localPort)]
        # if multiple IP addresses are specified for a listening port, assume we want to perform loading balancing
        # on the port
        else:
            # add the local IP/port combination to the forwarding entry associated with the port
            rules[port].append('%s:%s' % (localIP, localPort))

        # read the next line
        data = ruleFile.readline().rstrip()

    return rules

def forwardingPort(listeningPort, forwardingDestinations, stdin):
    # if multiple IP addresses are specified as forwarding destinations for the same port, forwarder operates as a load
    # balancer
    count = 0
    numofDestinations = len(forwardingDestinations)

    try:
        # create a server socket
        listenSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # allow port to be reused immediately if previous execution has left it in a TIME_WAIT state
        listenSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # set socket to non-blocking
        listenSocket.setblocking(0)
        # bind socket to port (using '' sets the socket to listen on all interfaces)
        listenSocket.bind(('', listeningPort))
        # set socket to listen for connection requests
        listenSocket.listen(QUEUE_SIZE)
        print 'forwarder listening for connections on port %s, press enter to shut down the server' % listeningPort
    except socket.error, message:
        print 'Failed to create socket. Error code: ' + str(message[0]) + '-' + message[1]

    # use an epoll object to monitor incoming/outgoing connections from the listening port
    epoll = select.epoll()
    # register listening port with the epoll object
    epoll.register(listenSocket.fileno(), select.EPOLLIN | select.EPOLLET)
    # register stdin (keyboard) with the incoming epoll object
    epoll.register(stdin, select.EPOLLIN | select.EPOLLET)
    # the forwarder maintains an incoming/outgoing pair of sockets to facilitate communication between clients and the
    # actual server
    sockets = {}
    # use this dictionary to map the relationship between socket pairs
    connectionTable = {}

    listening = True

    while listening:
        events = epoll.poll(1)
        for fileno, event in events:
            # if event came from the listening socket, a client is attempting to connect
            if fileno == listenSocket.fileno():
                # accept the incoming socket
                incomingSocket, connectionInfo = listenSocket.accept()

                # get client IP/port info
                clientIP = incomingSocket.getpeername()[0]
                clientPort = incomingSocket.getpeername()[1]
                destinationIP, destinationPort = forwardingDestinations[count % numofDestinations].split(':')
                count += 1
                if DEBUG_MODE:
                    print 'new connection from %s:%s, forwarding connection to %s' % \
                          (clientIP, clientPort, forwardingDestinations[count % numofDestinations])
                    print 'next connection will be forwarded to %s' % forwardingDestinations[count % numofDestinations]

                # tell epoll we're interested when the incoming socket has data to read from
                epoll.register(incomingSocket.fileno(), select.EPOLLIN | select.EPOLLET)
                # tell epoll to keep notifying us when it detects events on the listening socket
                epoll.modify(listenSocket.fileno(), select.EPOLLIN | select.EPOLLET)
                # add socket to incoming list so we can access it later
                sockets[incomingSocket.fileno()] = incomingSocket

                # create outgoing socket
                outgoingSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                outgoingSocket.connect((destinationIP, int(destinationPort)))
                # add socket to outgoing list so we can access it later
                sockets[outgoingSocket.fileno()] = outgoingSocket
                # tell epoll we're interested when the outgoing socket has data ready to be sent back to the client
                epoll.register(outgoingSocket.fileno(), select.EPOLLIN | select.EPOLLET)

                # register the new socket pair in the connection table
                connectionTable[incomingSocket.fileno()] = outgoingSocket.fileno()
                connectionTable[outgoingSocket.fileno()] = incomingSocket.fileno()
            # if enter on the keyboard was pressed, stop the forwarder gracefully
            elif fileno == stdin:
                listening = False
                listenSocket.close()
            # if incoming data is not on listening socket or keyboard, it's from one of our incoming/outgoing sockets
            elif event & select.EPOLLIN:
                # read data from socket
                data = sockets[fileno].recv(BUFFER_SIZE)

                # if we get an empty string after calling recv() one side has disconnected
                if len(data) == 0:
                    if DEBUG_MODE:
                        print 'closing connection to %s:%s' % \
                          (sockets[fileno].getpeername()[0], sockets[fileno].getpeername()[1])
                    # close both sides associated with the forwarding connection
                    sockets[connectionTable[fileno]].close()
                    sockets[fileno].close()
                    # unregister sockets from epoll
                    epoll.unregister(connectionTable[fileno])
                    epoll.unregister(fileno)
                    # remove sockets from dictionary
                    sockets.pop(connectionTable[fileno], None)
                    sockets.pop(fileno, None)
                    # remove forwarding entries
                    connectionTable.pop(connectionTable[fileno], None)
                    connectionTable.pop(fileno, None)
                # if the string isn't empty, forward the data using the socket specified in the connection table
                else:
                    sockets[connectionTable[fileno]].send(data)
                    # tell epoll we're interested when the socket has data waiting to be read again
                    epoll.modify(fileno, select.EPOLLIN | select.EPOLLET)

def startForwarder():
    rules = readRules()

    # print out rules read from file
    ruleNumber = 1
    print 'the port forwarder will be initialized with the following rules:'
    for port in rules:
        print '#%s - forward traffic from port %s to:' % (ruleNumber, port)
        for forwardDestination in rules[port]:
            print '   %s' % forwardDestination
        ruleNumber += 1

    forwardingPortProcesses = []

    # spawn process to listen on each port defined in rule file
    for port in rules:
        forwardingPortProcess = Process(target=forwardingPort, args=(int(port), rules[port], sys.stdin.fileno(),))
        forwardingPortProcesses.append(forwardingPortProcess)

    for process in forwardingPortProcesses:
        process.start()
    for process in forwardingPortProcesses:
        process.join()

    print 'keyboard press detected, stopping port forwarder'

if __name__ == '__main__':
    startForwarder()
