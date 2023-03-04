import sys
import time
import random
import errno
from socket import *

def makepkt(data, seq, ack):
	return bytes([data & 0b11111111111111111111111111111111,seq,ack])

#read setup values from sys.argv
seedTiming = int(sys.argv[1])
if seedTiming < 2 or seedTiming > 32000:
	seedTiming = 111
randTiming = random.Random(seedTiming)

seedACKCorr = int(sys.argv[2])
if seedACKCorr <= 2 or seedACKCorr >= 32000:
	seedACKCorr = 222
randACKCorr = random.Random(seedACKCorr)

seedData = int(sys.argv[3])
if seedData <= 2 or seedData >= 32000:
	seedData = 333
randData = random.Random(seedData)

numPackets = int(sys.argv[4])
if numPackets <= 1 or numPackets >= 100:
	numPackets = 10

ACKlost = float(sys.argv[5])
ACKcorrupt = float(sys.argv[6])
if ACKlost < 0 or ACKlost >= 1:
	ACKlost = 0.0005
if ACKcorrupt < 0 or ACKcorrupt >= 1:
	ACKcorrupt = 0.001
if ACKlost >= ACKcorrupt:
	ACKlost = 0.0005
	ACKcorrupt = 0.001

RTT = float(sys.argv[7])
if RTT <= 0.1 or RTT > 10.0:
	RTT = 5.0

#initialize connection
serverName = '127.0.0.1'
serverPort = 50007
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.settimeout(RTT)
clientSocket.connect( (serverName, serverPort) )



sentPackets = 0
seqState = 0
nextSenderState = 0
packet = makepkt(0, 0 ,0)
timeoutStart = 0
while sentPackets < numPackets:
	#0: send segment: send new packet, go to wait for ack
	#1: resend segment: send previous packet, don't advance packet#, go to wait for ack
	#2: wait for ack segment:
		#ack timeout: go to resend segment
		#ack corrupted/duplicate: go back to wait for ack with same timeout timer then go to resend segment
		#ack lost: go to resend segment
		#ack received: go to send segment and advance sent packet count

	if nextSenderState == 0:
		nextPacketDelay = randTiming.random() * 6
		time.sleep(nextPacketDelay)
		data = randData.randint(25, 100)
		packet = makepkt(data, seqState, 0)
		print("")
		print("A packet with sequence number", seqState, "is about to be sent")
		print("Packet to send contains data =", data, "seq =", seqState, "isack =", False)
		print("Starting timeout timer for ACK{0}".format(seqState))
		print("The Sender is moving to state WAIT FOR ACK{0}".format(seqState))
		clientSocket.send(packet)
		timeoutStart = time.time()
		nextSenderState = 2
	elif nextSenderState == 1:
		print("")
		print("A packet with sequence number", seqState, "is about to be resent")
		print("Packet to send contains data =", data, "seq =", seqState, "isack =", False)
		print("Starting timeout timer for ACK{0}".format(seqState))
		print("The Sender is moving to state WAIT FOR ACK{0}".format(seqState))
		clientSocket.send(packet)
		timeoutStart = time.time()
		nextSenderState = 2
	elif nextSenderState == 2:
		timeLeft = RTT - (time.time() - timeoutStart)
		response = None
		if timeLeft > 0:
			try:
				clientSocket.settimeout(timeLeft)
				response = clientSocket.recv(1024)
			except: #response timeout
				print("")
				print("ACK{0} timeout timer expired (packet lost)".format(seqState))
				print("The sender is moving back to state WAIT FOR CALL {0} FROM ABOVE".format(seqState))
				nextSenderState = 1
				continue
		else: #timeout occured during code execution (avoid setting negative timeout time)
			print("")
			print("ACK{0} timeout timer expired (packet lost)".format(seqState))
			print("The sender is moving back to state WAIT FOR CALL {0} FROM ABOVE".format(seqState))
			nextSenderState = 1
			continue

		recvData = int.from_bytes(response[0:-2], "big")
		seq = response[-2]
		ack = True
		if response[-1] == 0:
			ack = False

		ACKprob = randACKCorr.random()
		#if uncorrupted ack
		if ACKprob >= ACKcorrupt and ack:
			if seq == seqState: #correct ACK, advance next state
				print("")
				print("An ACK{0} packet has just been received".format(seq))
				print("Packet received contains: data =", recvData, "seq =", seq, "isack =", ack)
				print("Stopping timeout timer for ACK{0}".format(seq))
				seqState = (seqState + 1) % 2
				sentPackets+=1
				print("The sender is moving to state WAIT FOR CALL {0} FROM ABOVE".format(seqState))
				nextSenderState = 0
			else: #duplicate ACK
				print("")
				print("A duplicate ACK{0} packet has just been received".format(seq))
				print("Packet received contains: data =", recvData, "seq =", seq, "isack =", ack)
				print("Stopping timeout timer for ACK{0}".format(seq))
				print("The sender is moving back to state WAIT FOR ACK{0}".format(seqState))
				nextSenderState = 2
		else: 
			if ACKprob >= ACKlost: # ACK corrupted
				print("")
				print("A Corrupted ACK packet has just been received")
				print("The sender is moving back to state WAIT FOR ACK{0}".format(seqState))
				nextSenderState = 2
			elif ACKprob >= 0: # ACK lost
				print("")
				timeElapsed = time.time() - timeoutStart
				time.sleep(timeElapsed)
				print("ACK{0} timeout timer expired (ACK lost)".format(seqState))
				print("The sender is moving back to state WAIT FOR CALL {0} FROM ABOVE".format(seqState))
				nextSenderState = 1
