# echo-server.py

import socket


# BCI streaming setup
print("Setting up socket for BCI2000 stream...")
UDP_IP =  "127.0.0.1" 
UDP_PORT = 5005 
sock_bci = socket.socket(socket.AF_INET, # Internet
                    socket.SOCK_DGRAM) # UDP
sock_bci.bind((UDP_IP, UDP_PORT))

while True: 
    # Receive from BCI2000
    print("Receiving from BCI2000:")
    data, addr = sock_bci.recvfrom(1024) # buffer size is 1024 bytes
    data = data[2:] # Remove the first two dummy bytes (trial number and \t)
    data = data[:-3] # Remove the dummy bytes (\r\n)
    print("received message: %s" % data) #e.g.,'5\t16\t32595\t0\t2\t3\t3\t3'
