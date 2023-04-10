from tkinter import *
from tkinter import messagebox
import pdb
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client:
    request_code = {
        'SETUP': 0,
        'PLAY': 1,
        'PAUSE': 2,
        'TEARDOWN': 3
    }
    state_code = {
        'INIT': 0,
        'READY': 1,
        'PLAYING': 2
    }
    state = state_code['INIT']


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
        if self.state == Client.state_code['INIT']:
            self.sendRtspRequest('SETUP')

    # TODO

    def exitClient(self):
        """Teardown button handler."""
        self.sendRtspRequest('TEARDOWN')
        self.master.destroy()
        os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
        # pdb.set_trace()
    # TODO

    def pauseMovie(self):
        # pdb.set_trace()
        """Pause button handler."""
        if self.state == Client.state_code['PLAYING']:
            self.sendRtspRequest('PAUSE')

    def playMovie(self):
        """Play button handler."""
        if self.state == Client.state_code['READY']:
            self.playVideo = threading.Event()
            self.playVideo.clear() # hold the event til the rtp socket is opened
            threading.Thread(target=self.listenRtp).start()
            self.sendRtspRequest('PLAY')

    def listenRtp(self):
        """Listen for RTP packets."""
        # pdb.set_trace()
        while True:
            try:
                self.playVideo.wait()
                if self.teardownAcked: break
                data = self.rtpSocket.recv(20480)
                if data:
                    pkt = RtpPacket()
                    pkt.decode(data)
                    if pkt.seqNum() > self.frameNbr:
                        filename = self.writeFrame(pkt.getPayload())
                        self.updateMovie(filename)
            except: # attempt to read the data after PAUSE or TEARDOWN request sent will cause exception
                if self.requestSent == self.request_code["TEARDOWN"]:
                    break
    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        # pdb.set_trace()
        fileName = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        with open(fileName, mode="wb") as fp:
            fp.write(data)

        return fileName
    # TODO

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        current_frame = ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image=current_frame, height=288)
        self.label.image = current_frame
    # TODO

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
            print("Connected to Server: {}:{}".format(self.serverAddr, self.serverPort))
        except:
            messagebox.showerror(f"Failed connection to server {self.serverAddr}:{str(self.serverPort)}")

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        self.rtspSeq = self.rtspSeq + 1

        msg = "{} {} {}\nCSeq: {}\nSession: {}".format(
            requestCode, self.fileName, "RTSP/1.0",
            str(self.rtspSeq),
            str(self.sessionId)
        )
        request = Client.request_code[requestCode]
        if request == Client.request_code['SETUP'] and self.state == Client.state_code['INIT']:
            # Create a separate thread for listening for rtsp reply
            threading.Thread(target=self.recvRtspReply).start()
            msg = msg + "; client_port= {}\n".format(str(self.rtpPort))
        elif request == Client.request_code['PLAY'] and self.state == Client.state_code['READY']:
            pass
        elif request == Client.request_code['PAUSE'] and self.state == Client.state_code['PLAYING']:
            pass
        elif request == Client.request_code['TEARDOWN'] \
                and self.state in [Client.state_code['READY'], Client.state_code['PLAYING']]:
            pass
        else: return

        if(self.requestSent != request):
            self.requestSent = request
            self.rtspSocket.send(msg.encode())

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)
            if reply:
                self.parseRtspReply(reply.decode())
                print("\nRTSP reply: {}".format(reply))
            # End RTSP session
            if self.requestSent == Client.request_code['TEARDOWN']:
                self.playVideo.clear()
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                self.rtpSocket.shutdown(socket.SHUT_RDWR)
                self.rtpSocket.close()
                break

    # TODO

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        lines = data.split('\n')
        sequence_no = int(lines[1].split(' ')[1])

        if self.sessionId == 0:
            self.sessionId = lines[2].split(' ')[1]
        if self.rtspSeq == sequence_no:
            if self.sessionId == lines[2].split(' ')[1] and lines[0].split(' ')[2] == "OK":
                if self.requestSent == Client.request_code['SETUP']:
                    # Set the session id for the communication
                    self.state = Client.state_code['READY']
                    self.openRtpPort()
                elif self.requestSent == Client.request_code['PLAY']:
                    self.state = Client.state_code['PLAYING']
                    self.playVideo.set() # unlock for 'play thread'
                elif self.requestSent == Client.request_code['PAUSE']:
                    self.state = Client.state_code['READY']
                    self.playVideo.clear() # stop the current playing
                elif self.requestSent == Client.request_code['TEARDOWN']:
                    self.state = Client.state_code['INIT']
                    self.teardownAcked = 1
        print("Client State: {}".format(self.state))

    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # Create a new datagram socket to receive RTP packets from the server
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtpSocket.settimeout(0.5)
        try:
            self.rtpSocket.bind(("", self.rtpPort))
            self.state = Client.state_code['READY']
        except:
            messagebox.showerror(f"Cannot connect to server{self.serverAddr}:{self.rtpSocket}")

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        if self.state == Client.state_code['PLAYING']:
            self.pauseMovie()
        if messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:
            self.playMovie()
