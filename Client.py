from tkinter import *
from tkinter import messagebox

from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

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

    # Initiation..
    def __init__(self, master, serveraddr, serverport, rtpport, filename):
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
        # Sockets to communicate with streaming server
        self.rtpSocket = None
        self.rtspSocket = None

    def createWidgets(self):
        """Build GUI."""
        # Create Setup button
        self.setup = Button(self.master, width=20, padx=3, pady=3)
        self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie
        self.setup.grid(row=1, column=0, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=1, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=1, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4, sticky=W + E + N + S, padx=5, pady=5)

    def setupMovie(self):
        """Setup button handler."""
        if self.state == Client.INIT:
            self.sendRtspRequest(Client.SETUP)

    # TODO

    def exitClient(self):
        """Teardown button handler."""
        self.sendRtspRequest(Client.TEARDOWN)
        self.master.destroy()
        os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)

    # TODO

    def pauseMovie(self):
        """Pause button handler."""
        if self.state == Client.PLAYING:
            self.sendRtspRequest(Client.PAUSE)

    def playMovie(self):
        """Play button handler."""
        if self.state == Client.READY:
            self.sendRtspRequest(Client.PLAY)

    def listenRtp(self):
        """Listen for RTP packets."""


    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        folderName = "tmpFile"
        fileName = CACHE_FILE_NAME + str(self.sessionId) +CACHE_FILE_EXT
        os.mkdir(folderName)
        os.path.join(os.getcwd(), folderName, fileName)

        with open(fileName) as fp:
            fp.write(data)

        return fileName
    # TODO

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        current_frame = ImageTk.PhotoImage(Image.open(imageFile))
        self.lable.configure(image=current_frame, height=288)
        # self.label.image = current_frame
    # TODO

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            messagebox.showerror(f"Failed connection to server {self.serverAddr}:{self.serverPort}")
    # TODO

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""


    # -------------
    # TO COMPLETE
    # -------------

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply, _ = self.rtspSocket.recv(1024)
            if reply:
                self.parseRtspReply(reply)

            # End RTSP session
            if self.requestSent == Client.TEARDOWN:
                self.rtspSocket.close()
                break

    # TODO

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""


    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # Create a new datagram socket to receive RTP packets from the server
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtpSocket.settimeout(0.5)
        try:
            self.rtpSocket.bind((self.serverAddr, self.rtpSocket))
            self.state = Client.READY
        except:
            messagebox.showerror(f"Cannot connect to server{self.serverAddr}:{self.rtpSocket}")

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        if self.state == Client.PLAYING:
            self.pauseMovie()
        if messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:
            self.playMovie()
