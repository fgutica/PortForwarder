# PortForwarder
 

 

 

 

 


Port forwarding is a very important practice in network design. It allows for hiding the real addressing information of your services, helps you maintain a single entry point into your network and can give you load balancing functionality in order to maximize performance and efficiency. By having a single access point into your network it also makes for easier monitoring and filtering of traffic allowing you to maintain a secure environment.

 For this assignment we have designed, developed and implemented a port forwarder that uses a combination of node.js with python. Our forwarder is also capable of load balancing for the same application or server across multiple machines. Outlined in our document is information on our design, implementation and testing as well as instructions on setting up our forwarder along with the various applications and servers we have tested forwarding with. 

# **Design Methodology**

To make our port forwarder as user friendly as possible, it is controlled and configured through a web front end which enables users to operate it without any knowledge of the underlying components of the forwarder. An understanding of basic port forwarding concepts should be sufficient for most people to use the forwarder successfully.

The following components were created to implement and test our port forwarder’s functionality and are discussed in further detail in the subsequent sections below:

* Web front end written in Node.js

* Port forwarder **forwarder.py** written in Python

* SSL echo server **ssl_server_epoll.py** and client **ssl_client_epoll.py** written in Python 

* Chatroom server application written in C

## **Web Front End**

The Front end to control our web forwarder entries was written in node.js and uses bootstrap for the UI. 

The node.js is able to restart the python application running the port forwarder every time an entry is added, deleted or modified. 

The node app writes to a csv file that the python application reads in order to start each forwarding process.

## **Port Forwarder**

The port forwarding functionality in this project was implemented using Python version 2.7.10. The port forwarder examines the **entries.csv **file generated by the web front end and spawns a process for every unique listening port specified by the .csv file. If multiple IP/port destinations are provided for the same port the port forwarder will operate in load balancing mode, directing clients to the different server destinations in round robin fashion.

The decision to use multiprocessing was done to maximize CPU utilization and avoid utilization bottlenecks that can occur when multithreading, which we saw back in Assignment 1 of the course. Maximizing CPU utilization minimizes the processing time required to forward packets, which in turn minimizes response times during a connection heavy workload on the forwarder.

Each process spawned by the forwarder listens/accepts connections on its specified port and forwards connection traffic between the client and forwarding destination specified in the .csv file. A high level view of the port forwarder is presented in the diagram below:

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_0.png)

When a client connects to a listening port opened by our forwarder, a socket is created to exchange data between the client and the port forwarder. To pass the data onto the server that handles the actual data processing, a second socket is created to exchange data between the port forwarder and the actual server. By passing packets back and forth between this socket pair, we allow clients to communicate to the server and vice versa without the client having to know the server’s real IP address.

To handle forwarded connections in an efficient manner, each process overseeing a listening port consists of an epoll object that monitors for activity on every socket pair that representing a client/server connection. The relationship between socket pairs and their client/server connection is maintained in a connection table that is updated whenever new clients connect or existing clients disconnect normally or abnormally. When a socket has data ready to read, the process checks which side (client or server) the data came from, looks up the corresponding socket in the connection table and forwards the data using the socket. A state diagram summarizing the operating of each forwarding process is presented below:

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_1.png)

## **SSL Echo Server**

To test the port forwarder’s performance when handling a large number of concurrent connections, we created a scalable SSL server using Python 2.7.10. A client to interact with the server was also written based off the code of our Python epoll client in Assignment 2, with tweaks to enable SSL communication instead of communicating over plaintext.

### **Server Design**

The server establishes SSL connections with clients and simply echos messages back from the client as it receives them. A state diagram of the SSL Echo Server’s behavior is presented below:

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_2.png)

As mentioned above, the client that interacts with the SSL Echo Server is based off the epoll client that we previously submitted for Assignment 2, so there is no change in its overall behaviour aside from the fact that is now uses SSL sockets to communicate with the server. The client functions by getting user input on the following parameters:

* Message that should be sent to the server

* Number of times the message should be sent per connection

* Number of client connections to make to the server

### **Client Design**

After obtaining input, it waits until all client connections have been established with the server before each client starts sending their message. With enough clients doing this concurrently, it should place a heavy load on the port forwarder. The state diagram of the SSL client’s behaviour is shown below:

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_3.png)

## **Chatroom Server**

Another application we used for testing our forwarder is a chatroom client-server application. Chat application was designed and implemented in C++ and QT.  The server was implemented using select for io multiplexing.

The client front end was implemented in Qt and written in c++ 

### **Server Design**

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_4.png)

 

### **Client Design**

# ![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_5.png)

# **User Manual**

To reproduce our test results which are discussed in the following section, we have included instructions on how to configure and run each of the programs above. Additional instructions are also provided on how to setup the various server components used in our testing, such as the Apache web servers and SSH server.

## **Web Front End Setup**

On the forwarding computer:

1. Open up a terminal.

2. Execute the command ulimit -n 1000000

3. Execute dnf install node, dnf install nodejs

4. Navigate to the port forwarder root directory where there is a file: "app.js"

5. Execute the command "node app.js"

6. Node server will begin running on port 3001

7. Open a browser and navigate to [http://localhost:3001](http://localhost:3001)

8. There you will see the port forwarder user interface

9. Click "add entry" to add a new entry. 

10. Select entries by clicking on them

11. To delete a selected entry: select one and then click on "Delete selected"

The node js application will automatically start and restart the python port forwarder. 

## **Port Forwarder Setup**

The **forwarder.py **file should be placed in the same folder containing the **app.js **file used in the web front end. It is executed automatically by the web front end so users do not have to do anything further to during regular operation.

However, if you wanted to run the port forwarder as a standalone application simply create an **entries.csv** file containing your port forwarding rules and place it in the same folder as **forwarder.py**. Then run the following command in a terminal window to start the forwarder:

* **python forwarder.py**

## **SSL Echo Server Setup**

To enable SSL functionality between the server and client, we have to create a private key and self-signed certificate. These are provided through in the **server.key **and **server.crt **files included in the **ssl echo server **folder of our submission.

However if you wanted to generate these components yourself, you can use the openSSL library which comes installed by default on Fedora. A 2048-bit RSA private key named **server.key** encrypted with Triple DES can be created by running the commands below:

* **openssl genrsa -des3 -out server.orig.key 2048**

* **openssl rsa -in server.orig.key -out server.key**

The private key and a certificate signing request are needed to generate a self-signed certificate. The certificate signing request is created by running the following command:

* **openssl req -new -key server.key -out server.csr**

Finally, the self signed certificate **server.crt **is created with the command:

* **openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt**

To set up the server, copy the **ssl_server_epoll.py, server.key** and **server.crt **files into a folder on the computer acting as the server. The server is configured to listen on port 8005, however you can change the value of the PORT global variable in **ssl_server_epoll.py** to listen on another port if necessary. Then run the following commands in a terminal window:

* **ulimit -n 1000000** (increases the kernel file descriptor limit to handle many simultaneous connections)

* **python ssl_server_epoll.py**

On another computer, copy the **ssl_client_epoll.py **and **server.crt **files into a folder. The client is configured to connect to 192.168.0.18:1337 for our testing, but you can change the location by modifying the HOSTNAME and PORT global variables in **ssl_client_epoll.py**. To start the client, run the following commands in a terminal window:

* **ulimit -n 1000000** (increases the kernel file descriptor limit to handle many simultaneous connections)

* **python ssl_client_epoll.py**

## **Chatroom Server Setup**

In order to set up the server, compile the server.cpp and server.h and deploy the executable on the desired machine. By default the server runs on port 7000, set in the server.h file. 

Execute the server executable to start the chatroom server

Add an entry in the port forwarder to forward the chatroom clients to the chatroom server as outlined in the port forwarder usage. 

1. To run a client, execute the ChatClient executable from any client machine on the network.![image alt text](image_6.png)

2. You will see a popup asking you for the host information of the chat server you wish to connect to: Enter the necessary credentials. 
![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_7.png)

3. Upon connection you will get notified in the chat section that you are now connected to the host: 

	![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_8.png)

## **Apache Web Server Setup**

Copy all files in the **webserver1 **and **websever2 **folders to the **/var/www/html/** folder of the computer that will function as the corresponding web server. Then install Apache with the following command on Fedora 23:

* **dnf install httpd**

With Apache installed, start the httpd service and confirm that it is running with the following commands:

* **systemctl start httpd**

* **systemctl status httpd**

## **SSH Server Setup**

To enable ssh, run the following commands on the server:

* **systemctl start sshd**

* **systemctl status sshd**

When connecting to the SSH server from a client machine, use the following command:

* **ssh root@192.168.0.18 -p 22222**

The example above assumes that the port forwarder is running on 192.168.0.18 and is configured to forward traffic from port 22222 to the SSH server.

# **Testing Methodology**

To test our port forwarder, we configured it with the following rules using our web interface:

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_9.png)

In a separate terminal window, we can see that our port forwarder starting up:

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_10.png)

Running the command **netstat -ant**, we can confirms that the forwarder is now listening on all the specified ports

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_11.png)

We configured one desktop to operate as the port forwarder, two other desktops to act as clients and three more desktops to act as the various servers specified in the rules above. The configuration results in the network diagram below:

 ![image alt text](image_12.png)

## **Test Case #1 - Encryption on SSL Echo Server**

Before testing the port forwarder, we wanted to confirm that encryption is working on our SSL echo server. We first set up our non-SSL client/server from Assignment 2 and established a single session to the server as below:

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_13.png)

Using Wireshark to capture the session, we can see the message in plaintext in the packets:

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_14.png)

We then ran the SSL client/server with the same settings as above:

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_15.png)

A Wireshark capture of the session this time shows that the message is now scrambled, indicating that SSL is working on our client and server.

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_16.png)

## **Test Case #2 - Forwarding Multiple Inbound Requests**

For this test case, we used the SSL client to create 1000 client connections to our SSL echo server running as seen in the screenshot below:

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_17.png)

After running, the log file **client data - 1000.xlsx** was generated with information on all 1000 client sessions.

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_18.png)

In addition to running the SSL echo server the Chatroom server was also run simultaneously, hosting a chat session between both client PCs at 192.168.0.17 and 192.168.0.25. We observed that our chat session was able to proceed without any impact from the SSL echo server tests, as can be seen by the screenshots below:

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_19.png)

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_20.png)

From these results, we can conclude that the forwarder can properly forward multiple inbound requests.

## **Test Case #3 - Forwarding Two-Way Traffic**

To test that the forwarder can forward traffic properly from client to server and vice versa, we established an SSH session over the port forwarder. The client PC has IP address 192.168.0.23 as seen below:

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_21.png)

From the terminal session below, note how SSH is accessed through the forwarder IP address at 192.168.0.18 but running the **ip a show eno1** command after connecting returns us the SSH server IP of 192.168.0.21.

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_22.png)

Because our SSH command returned us output from the server, we can conclude that our forwarder handles two-way traffic correctly. For additional evidence, see the Wireshark capture file **ssh session.pcapng **included with our submission.

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_23.png)

## **Test Case #4 - ****Load Balancing, ****Low Load Conditions**

To confirm that our port forwarder correctly functions as a load balancer, we set up two Apache web servers on IP addresses 192.168.0.17 and 192.168.0.21. From the client PC at 192.168.0.23 we used Firefox to access our test webpage using the port forwarder’s address and received the webpage from the first web server:

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_24.png)

Refreshing the webpage with CTRL + F5 to bypass the browser cache, we see that the webpage is now served from our second web server:

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_25.png)

The wireshark capture file **web server load balancing.pcapng** verifies the load balancing behaviour we observed above. If we filter the capture file to show only HTTP traffic, we see that the first HTTP GET request is received by the forwarder and then passed onto the server at 192.168.0.17. The subsequent GET is also received by the forwarder and passed onto the other web server at 192.168.0.21.

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_26.png)

## **Test Case #5 - Load Balancing, Heavy Load Conditions**

In order to get a sense of how well the port forwarder performs load balancing under heavy load, we used our Assignment 2 client/server code establish 20000 client connections to the port forwarder using the settings below:

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_27.png)

After running the client, we see that the forwarder sends 10000 connections to the first server on 192.168.0.17![image alt text](image_28.png)

10000 connections are also sent to the second server on 192.168.0.21.

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_29.png)

The results file generated by our client shows that 771047 messages were sent to the server over 15 seconds with an average response time of 411 ms.

![image alt text](https://github.com/roFilip/PortForwarder/blob/master/readme_imges/image_30.png)

From these results, we can conclude that our port forwarder is able to handle a large number of connections successfully.

**Conclusion**

Port forwarding is a very necessary tool for any network admin, or architect. We need them in order to maintain security, and control over the traffic into the network. By using epoll for our forwarder, as well as a very robust, easy to use front end, we have come up with a very scalable port forwarder that could be used on virtually any network to forward and organize connections and traffic to many servers. Some of our other tests also include forwarding a minecraft server, web server, our scalable server for load balancing and all types of servers are working with our forwarder very smoothly.


