import sys
import random
from socket import *

def makepkt(data, seq, ack):
	return bytes([data & 0b11111111111111111111111111111111,seq,ack])

#read setup values from sys.argv
seedPackCorr = int(sys.argv[1])
if seedPackCorr <= 2 or seedPackCorr >= 32000:
	seedPackCorr = 555
randPackCorr = random.Random(seedPackCorr)

packLost = float(sys.argv[2])
packCorrupt = float(sys.argv[3])
if packLost < 0 or packLost >= 1:
	packLost = 0.0005
if packCorrupt < 0 or packCorrupt >= 1:
	packCorrupt = 0.001
if packLost >= packCorrupt:
	packLost = 0.0005
	packCorrupt = 0.001

#initialize connection
serverHost = ''
serverPort = 50007
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(( serverHost, serverPort))
serverSocket.listen(1)
#loop logic
#print('receiver working')

prevData = -1
prevSeq = 0
waitFor = 0
while True:
	connectionID, addr = serverSocket.accept()
	while True:
		packet = connectionID.recv(1024)
		if len(packet) == 0:
			#print("debug")
			connectionID.close()
			break;
		packCheck = randPackCorr.random()
		if packCheck < packLost:
			print("")
			print("A packet has been lost")
			print("The receiver is moving back to state WAIT FOR", waitFor, "FROM BELOW")
		elif packCheck < packCorrupt:
			print("")
			print("A Corrupted packet has just been received")
			resendSeq = (waitFor + 1) % 2
			print("An ACK{0} is about to be resent".format(resendSeq))
			print("ACK packet to send contains: data =", 0, "seq =", resendSeq, "isack =", True)
			sendAck = makepkt(0, resendSeq, 1)
			connectionID.send(sendAck) 
			print("The receiver is moving back to state WAIT FOR", waitFor, "FROM BELOW")
		else:
			data = int.from_bytes(packet[0:-2], "big")
			seq = packet[-2]
			ack = False
			if packet[-1] == 1:
				ack = True
			if (data == prevData and seq != waitFor):
				print("")
				print("A duplicate packet with sequence number", seq, "has been received")
				print("Packet received contains: data =", data, "seq =", seq, "isack =", ack)
				print("An ACK{0} is about to be resent".format(seq))
				print("ACK packet to send contains: data =", 0, "seq =", seq, "isack =", True)
				sendAck = makepkt(0, seq, 1)
				connectionID.send(sendAck)
				print("The receiver is moving back to state WAIT FOR", waitFor, "FROM BELOW")
			else:
				print("")
				print("A packet with sequence number", seq, "has been received")
				print("Packet received contains: data =", data, "seq =", seq, "isack =", ack)
				print("An ACK{0} is about to be sent".format(seq))
				print("ACK packet to send contains: data =", 0, "seq =", seq, "isack =", True)				
				sendAck = makepkt(0, seq, 1)
				connectionID.send(sendAck)
				prevData = data
				waitFor = (seq + 1) % 2
				print("The receiver is moving to state WAIT FOR", waitFor, "FROM BELOW")
