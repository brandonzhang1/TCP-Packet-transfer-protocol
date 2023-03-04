# TCP-Packet-transfer-protocol-simulation

Simulates the coordination between two endpoints in handling corrupted and lost packets over a TCP socket connection with rates set by argument input. Simulates the following state transition protocol.

![receiver](http://github.com/brandonzhang1/TCP-Packet-transfer-protocol/receiver.png)

![sender](http://github.com/brandonzhang1/TCP-Packet-transfer-protocol/sender.png)


To run, first run the receiver program in the background before running the sender program. Arguments shown here are to invoke default values.
>python receiver.py 0 1 1&
>python sender.py 0 0 0 0 1 1 0
