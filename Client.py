import tkinter.messagebox as tkMessageBox
from tkinter import *
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
import time
import datetime
from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT

	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	DESCRIBE = 4


	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.count_loss_frame = 0
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		self.DESCRIBE_STR = "DESCRIBE"
		self.DESCRIBE_STR = "DESCRIBE"
		self.SETUP_STR = "SETUP"
		self.RTSP_VER = "RTSP/1.0"
		self.TRANSPORT = "RTP/AVP"
		self.PLAY_STR = "PLAY"
		self.PAUSE_STR = "PAUSE"
		self.TEARDOWN_STR = "TEARDOWN"
		#extend
		self.total_time = 0
		self.total_data = 0
		self.firstPlay = True
	def createWidgets(self):
		"""Build GUI."""
		self.master.resizable(width=True, height=True)
		self.master.configure(bg='black')

		self.load1 = Image.open("poster.jpg")
		self.load1.resize((50, 50),Image.ANTIALIAS)
		self.render1 = ImageTk.PhotoImage(self.load1)

		self.img1 = Label(self.master, image=self.render1)
		self.img1.grid(row=2,column=0,  padx=2, pady=2)

		self.label5 = Label(self.master, text="You are now watching: \nGattaca (1997)")
		self.label5.grid(row=0, column=0, columnspan=4,padx=5, pady=5)
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3,bg='red',fg="white")
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=0, column=3, padx=2, pady=2)
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=3, column=0, padx=2, pady=2)

		# Create Play button
		self.start = Button(self.master, width=20, padx=3, pady=3,bg='green',fg="white")
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=3, column=1, padx=2, pady=2)

		# Create Pause button
		self.pause = Button(self.master, width=20, padx=3, pady=3,bg='blue',fg="white")
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=3, column=2, padx=2, pady=2)

		# Create Describe button
		self.start = Button(self.master, width=20, padx=3, pady=3,bg='yellow',fg="black")
		self.start["text"] = "Describe"
		self.start["command"] = self.describeMovie
		self.start.grid(row=3, column=3, padx=2, pady=2)

		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=2, column=1, columnspan=3, sticky=W+E+N+S, padx=5, pady=5)

		self.label1 = Label(self.master, text="Enjoy your movie")
		self.label1.grid(row=8, column=0, columnspan=4,padx=5, pady=5)

		self.label1 = Label(self.master, text="How to play video")
		self.label1.grid(row=4, column=0,columnspan=4,padx=0, pady=5)
		self.label1 = Label(self.master, text="Step 1: Click Set Up")
		self.label1.grid(row=5, column=1,padx=0, pady=5,sticky=W)
		self.label1 = Label(self.master, text="Step 2: Click Play to streaming movie or click Pause to pause the movie")
		self.label1.grid(row=6, column=1,padx=0, pady=5,sticky=W)
		self.label1 = Label(self.master, text="Step 3: Click Teardown to turn off")
		self.label1.grid(row=7, column=1,padx=0, pady=5,sticky=W)

	def setupMovie(self):
		"""Setup button handler."""
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)

	def exitClient(self):
		"""Teardown button handler."""
		self.sendRtspRequest(self.TEARDOWN)
		self.master.destroy()  # Close the gui window
		os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)  # Delete the cache image from video

	def pauseMovie(self):
		"""Setup button handler."""
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)
		"""Pause button handler."""
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	def playMovie(self):
		if self.state == self.INIT and self.firstPlay:
			self.sendRtspRequest(self.SETUP)
			self.firstPlay = False
			# Wait until ready
			while self.state != self.READY:
				pass

		if self.state == self.READY:
			# Create a new thread to listen for RTP packets
			threading.Thread(target=self.listenRtp).start()
			self.playEvent = threading.Event()
			self.playEvent.clear()
			self.sendRtspRequest(self.PLAY)
	def describeMovie(self):
		"""Describe button handler"""
		#if self.state == self.READY:
		self.sendRtspRequest(self.DESCRIBE)
	def listenRtp(self):
		"""Listen for RTP packets."""
		start_time = time.time()
		while True:
			try:
				data = self.rtpSocket.recv(20480)
				self.total_data += len(data)
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)

					currFrameNbr = rtpPacket.seqNum()
					print("Current Seq Num: " + str(currFrameNbr)+" | Total loss frame: " + str(self.count_loss_frame))


					if currFrameNbr > self.frameNbr:  # Discard the late packet
						self.count_loss_frame += currFrameNbr - (self.frameNbr + 1)
						self.frameNbr = currFrameNbr
						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
			except:
				# Stop listening upon requesting PAUSE or TEARDOWN
				if self.playEvent.isSet():
					break

				# Upon receiving ACK for TEARDOWN request,
				# close the RTP socket
				if self.teardownAcked == 1:
					self.rtpSocket.shutdown(socket.SHUT_RDWR)
					self.rtpSocket.close()
					break
				break
		packet_loss_rate = float(self.count_loss_frame / self.frameNbr)
		print("\n--> RTP Packet Loss Rate : " + str(packet_loss_rate))
		end_time = time.time()
		self.total_time += end_time - start_time
		print("Video data length: " + str(self.total_data) + " bytes")
		print("Total time: " + str(self.total_time) + " s")
		print("Video data rate: " + str(self.total_data / self.total_time) + " bytes/second")

	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(cachename, "wb")
		file.write(data)
		file.close()

		return cachename

	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		photo = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image=photo, height=288)
		self.label.image = photo

	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkMessageBox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)

	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""
		# -------------
		# TO COMPLETE
		# -------------

		# Setup request
		if requestCode == self.SETUP and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()
			# Update RTSP sequence number.
			self.rtspSeq = 1

			# Write the RTSP request to be sent.
			request = ( "SETUP " + str(self.fileName) + " RTSP/1.0 " + "\n"
						"CSeq: " + str(self.rtspSeq) + "\n"
						"Transport: RTP/UDP; client_port= " + str(self.rtpPort))

			# Keep track of the sent request.
			self.requestSent = self.SETUP

		# Play request
		elif requestCode == self.PLAY and self.state == self.READY:
			# Update RTSP sequence number.
			self.rtspSeq = self.rtspSeq + 1

			# Write the RTSP request to be sent.
			request = ("PLAY " + str(self.fileName) + " RTSP/1.0 " + "\n" +
						"CSeq: " + str(self.rtspSeq) + "\n" +
						"Session: " + str(self.sessionId))

			# Keep track of the sent request.
			self.requestSent = self.PLAY

		# Pause request
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			# Update RTSP sequence number.
			self.rtspSeq = self.rtspSeq + 1

			# Write the RTSP request to be sent.
			request = ( "PAUSE " + str(self.fileName) + " RTSP/1.0 " + "\n" +
						"CSeq: " + str(self.rtspSeq) + "\n" +
						"Session: " + str(self.sessionId))

			# Keep track of the sent request.
			self.requestSent = self.PAUSE

		# Teardown request
		elif requestCode == self.TEARDOWN and not self.state == self.INIT:
			# Update RTSP sequence number.
			self.rtspSeq = self.rtspSeq + 1

			# Write the RTSP request to be sent.
			request = ( "TEARDOWN " + str(self.fileName) + " RTSP/1.0" + "\n"
						"CSeq: " + str(self.rtspSeq) + "\n"
						"Session: " + str(self.sessionId))

			# Keep track of the sent request.
			self.requestSent = self.TEARDOWN

		elif requestCode == self.DESCRIBE:

			self.rtspSeq = self.rtspSeq + 1
			request = "%s %s %s\nCSeq: %d\nSession: %d" % (
				self.DESCRIBE_STR, self.fileName, self.RTSP_VER, self.rtspSeq, self.sessionId)
			self.requestSent = self.DESCRIBE
			self.rtspSocket.send(request.encode())
			print('\nData sent:\n' + request)
			x = datetime.datetime.now()
			top = Toplevel()
			top.geometry('300x100')
			Lb1 = Listbox(top, width=50, height=20)
			Lb1.insert(1, "Describe: ")
			Lb1.insert(2, "1. File Video: " + str(self.fileName))
			Lb1.insert(3, "2. Date: " + str(x.date()))
			Lb1.insert(4, "3. Time: " + str(x.strftime("%X")))
			Lb1.insert(5, "4. Day: " + str(x.strftime("%A")))
			Lb1.insert(5, "5. Session: " + str(self.sessionId))

			Lb1.pack()
			top.mainloop()
		else:
			return


		# Send the RTSP request using rtspSocket.
		self.rtspSocket.send(request.encode("utf-8"))

		print('\nData sent:\n' + request)

	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True:
			reply = self.rtspSocket.recv(1024)

			if reply:
				#print(reply);
				self.parseRtspReply(reply.decode("utf-8"))

			# Close the RTSP socket upon requesting Teardown
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break

	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		lines = data.split('\n')
		seqNum = int(lines[1].split(' ')[1])

		# Process only if the server reply's sequence number is the same as the request's
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session

			# Process only if the session ID is the same
			if self.sessionId == session:
				if int(lines[0].split(' ')[1]) == 200:
					if self.requestSent == self.SETUP:
						# -------------
						# TO COMPLETE
						# -------------
						# Update RTSP state.
						self.state = self.READY

						# Open RTP port.
						self.openRtpPort()
					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING
					elif self.requestSent == self.PAUSE:
						self.state = self.READY

						# The play thread exits. A new thread is created on resume.
						self.playEvent.set()
					elif self.requestSent == self.TEARDOWN:
						self.state = self.INIT

						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1



	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		# -------------
		# TO COMPLETE
		# -------------
		# Create a new datagram socket to receive RTP packets from the server
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)

		try:
			# Bind the socket to the address using the RTP port given by the client user
			self.state = self.READY
			self.rtpSocket.bind(('', self.rtpPort))
		except:
			tkMessageBox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.pauseMovie()
		if tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?"):
			self.exitClient()
		else:  # When the user presses cancel, resume playing.
			self.playMovie()
