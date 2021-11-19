import sys
import time
import socket
import struct

from PyQt5.QtGui import QFont, QPainter, QColor, QPixmap, QStandardItemModel, QStandardItem
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from matplotlib import rcParams

from crc32 import crc32_fill_table, crc32

from waveform import Waveform

rcParams['font.family'] = 'arial'

def printBuff(pref,data):
    str = ''
    for b in data:
        str += "%02X" % b
    print(pref + " " + str)


class RecvThread(QThread):

    rxTmSig = pyqtSignal(tuple,bytes)

    def __init__(self, parent, sock):

        QThread.__init__(self, parent)

        self.sock = sock
        self.data = bytes()
        self.running = True

    def run(self):
        while self.running is True:
            try:
                data = self.sock.recv(65536)
            except:
                print("Socket recv error")
                continue
            try:
                self.parse(data)
            except:
                print("Parse error")


    def stop(self):
        self.running = False
        self.wait()

    def parse(self,data):
        self.data += data
        off = 0
        while True:
            if len(self.data) - off > 0:
                if self.data[off] == 0x8D:
                    if len(self.data) - off >= 12:
                        # [0] Start (uint8)
                        # [1] APID (uint8)
                        # [2] Sequence (uint16)
                        # [3] Type (uint8)
                        # [4] SubType (uint8)
                        # [5] Size (uint16)
                        # [6] CRC (uint32)
                        header = struct.unpack("<BBHBBHI", self.data[off:off + 12])
                        data_off = off + 12
                        if len(self.data) - data_off >= header[5]:
                            self.rxTmSig.emit(header, self.data[data_off:data_off + header[5]])
                            off = data_off + header[5]
                        else:
                            self.data = self.data[off:]
                            break
                    else:
                        self.data = self.data[off:]
                        break
                else:
                    off += 1
            else:
                self.data = bytes()
                break


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class StartAcqDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Start acquisition")
        self.resize(270, 110)

        self.source = QComboBox()
        self.source.addItem("DETECTOR")
        self.source.addItem("SIMULATOR")

        self.waveNo = QLineEdit()
        self.waveNo.setText("0")

        self.message = QLabel("Set waveform no. to 0 for infinite")

        self.waitUsecs = QLineEdit()
        self.waitUsecs.setText("500000")

        form = QFormLayout()
        form.addRow("Source:", self.source)
        form.addRow("Waveform no.:", self.waveNo)
        form.addRow("", self.message)
        form.addRow("Wait:", self.waitUsecs)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttonBox)
        self.setLayout(layout)


class MsgListItem(QStandardItem):
    def __init__(self, txt='', font_size=10, set_bold=False, fcolor=QColor(0, 0, 0), bcolor=QColor(255, 255, 255)):
        super().__init__()
        fnt = QFont('Arial', font_size)
        fnt.setBold(set_bold)
        self.setEditable(False)
        self.setForeground(fcolor)
        self.setBackground(bcolor)
        self.setFont(fnt)
        self.setText(txt)


class Window(QMainWindow):

    def __init__(self, parent=None):

        super(Window, self).__init__(parent)

        self.mplCanvas = MplCanvas(self, width=5, height=4, dpi=100)

        self.msgListModel = QStandardItemModel()
        self.msgListModel.setHorizontalHeaderLabels(["Time", "TCTM", "Group", "Count", "Type", "SubT", "Interpretation"])

        self.msgList = QTreeView()
        self.msgList.setModel(self.msgListModel)
        self.msgList.setColumnWidth(0, 80)
        self.msgList.setColumnWidth(1, 40)
        self.msgList.setColumnWidth(2, 40)
        self.msgList.setColumnWidth(3, 60)
        self.msgList.setColumnWidth(4, 40)
        self.msgList.setColumnWidth(5, 40)

        layout = QVBoxLayout()
        layout.addWidget(self.mplCanvas)
        layout.addWidget(self.msgList)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.connDiscLabel = QLabel("DISC")
        #p2 = QLabel("DISC")

        self.statusBar = QStatusBar()
        self.statusBar.addPermanentWidget(self.connDiscLabel)
        #self.statusBar.addPermanentWidget(p2)
        self.setStatusBar(self.statusBar)

        self.serverConnAct = QAction("&Connect", self)
        self.serverConnAct.triggered.connect(self.serverConn)

        self.serverDiscAct = QAction("&Disconnect", self)
        self.serverDiscAct.triggered.connect(self.serverDisc)
        self.serverDiscAct.setDisabled(True)

        self.connTestAct = QAction("&Connection test", self)
        self.connTestAct.triggered.connect(self.connTest)

        self.startAcqAct = QAction("&Start acq.", self)
        self.startAcqAct.triggered.connect(self.startAcq)

        self.stopAcqAct = QAction("S&top acq.", self)
        self.stopAcqAct.triggered.connect(self.stopAcq)

        mb = self.menuBar()
        devMenu = mb.addMenu("&Server")
        devMenu.addAction(self.serverConnAct)
        devMenu.addAction(self.serverDiscAct)
        devMenu = mb.addMenu("&TC")
        devMenu.addAction(self.connTestAct)
        devMenu.addAction(self.startAcqAct)
        devMenu.addAction(self.stopAcqAct)

        # Not use the native menu bar when in macOS
        mb.setNativeMenuBar(False)

        self.setWindowTitle("GammaFlash DAM Client")

        self.startTime = time.time()

        self.recvThread = None
        self.sock = None
        self.timer = None

        self.tcCount = 0

        self.crcTable = crc32_fill_table(0x05D7B3A1)

        self.wformTotCount = 0
        self.wformSeqCount = -1
        self.wform = None

    @pyqtSlot(tuple,bytes)
    def rxTm(self, header, data):
        if header[3] == 0xA1: # Waveform
            if header[4] == 0x01: # Waveform header
                #self.tmToLog(header, data)
                self.tmToWformInit(header, data)
            else: # Waveform data
                self.tmToWformAdd(header, data)
        else:
            self.tmToLog(header, data)

    def tmToLog(self, header, data):
        uptime = time.time() - self.startTime
        item = self.createMsgListItem(uptime, header, data)
        self.msgListModel.appendRow(item)
        if self.msgListModel.rowCount() > 250:
            self.msgListModel.removeRow(0)
        self.msgList.scrollToBottom()

    def tick(self):
        uptime = time.time() - self.startTime

    def closeEvent(self, event):
        self.serverDisc()
        event.accept()

    def createMsgListItem(self, uptime, header, data):

        apid_class = header[1] & 0x80
        apid_source = header[1] & 0x7F
        seq_group = header[2] & 0xC000
        seq_count = header[2] & 0x3FFF

        fcolor = QColor(0, 0, 0)
        bcolor = QColor(255, 255, 255)

        if header[3] == 0x01:
            if data[0] == 0x00:
                bcolor = QColor(209, 255, 189) # Light green
            else:
                bcolor = QColor(245, 191, 206) # Light red
        elif header[3] == 0x03:
            fcolor = QColor(200, 200, 200)

        c1 = MsgListItem(txt="%8.3f" % uptime, fcolor=fcolor, bcolor=bcolor)
        if apid_class == 0x00:
            c2 = MsgListItem(txt="TC", fcolor=fcolor, bcolor=bcolor)
        else:
            c2 = MsgListItem(txt="TM", fcolor=fcolor, bcolor=bcolor)
        if seq_group == 0x0000:
            c3 = MsgListItem(txt="C", fcolor=fcolor, bcolor=bcolor)
        elif seq_group == 0x4000:
            c3 = MsgListItem(txt="F", fcolor=fcolor, bcolor=bcolor)
        elif seq_group == 0x8000:
            c3 = MsgListItem(txt="L", bcolor=bcolor)
        elif seq_group == 0xC000:
            c3 = MsgListItem(txt="S", fcolor=fcolor, bcolor=bcolor)
        else:
            c3 = MsgListItem(txt="U", fcolor=fcolor, bcolor=bcolor)
        c4 = MsgListItem(txt="%3d" % seq_count, fcolor=fcolor, bcolor=bcolor)
        c5 = MsgListItem(txt="%3d" % header[3], fcolor=fcolor, bcolor=bcolor)
        c6 = MsgListItem(txt="%3d" % header[4], fcolor=fcolor, bcolor=bcolor)

        interpretation = ""

        if header[3] == 0x03:
            if header[4] == 0x01:
                payload = struct.unpack("<BBBBI", data)
                interpretation = "Hk "
                if payload[0] == 0x02:
                    interpretation += "SRV"
                elif payload[0] == 0x03:
                    interpretation += "ACQ"
                else:
                    interpretation += "___"
                if payload[1] & 0x80:
                    interpretation += " P"
                else:
                    interpretation += " _"
                if payload[1] & 0x40:
                    interpretation += "G"
                else:
                    interpretation += "_"
                if payload[1] & 0x20:
                    interpretation += "T"
                else:
                    interpretation += "_"
                interpretation += " %8d" % payload[4]

        c7 = MsgListItem(txt=interpretation, fcolor=fcolor, bcolor=bcolor)
        return [c1, c2, c3, c4, c5, c6, c7]

    def serverConn(self):
        if self.recvThread is None:

            # Open the dialog to get the params
            #host = "127.0.0.1"
            host = "169.254.179.11"
            port = 1234

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)
            try:
                self.sock.connect((host, port))
            except:
                self.statusBar.showMessage("Connection to %s-%04d failed" % (host, port))
                return
            self.sock.settimeout(5)

            self.recvThread = RecvThread(None, self.sock)
            self.recvThread.rxTmSig.connect(self.rxTm)
            self.recvThread.start()

            self.timer = QTimer()
            self.timer.timeout.connect(self.tick)
            self.timer.start(1000)

            self.statusBar.showMessage("Connected to %s-%04d" % (host, port))
            self.connDiscLabel.setText("CONN")

            self.serverConnAct.setDisabled(True)
            self.serverDiscAct.setDisabled(False)

    def serverDisc(self):
        if self.recvThread is not None:
            del self.timer

            self.recvThread.stop()
            del self.recvThread

            self.recvThread = None
            self.sock = None
            self.timer = None

            self.statusBar.showMessage("Disconnected")
            self.connDiscLabel.setText("DISC")

            self.serverConnAct.setDisabled(False)
            self.serverDiscAct.setDisabled(True)

    def connTest(self):
        if self.recvThread is not None:
            self.tcCount += 1
            tc = struct.pack("<BBHBBHI", 0x8D, 0x00 + 0x0A, 0xC000 + self.tcCount, 0x11, 0x01, 0x0000, 0xFFFFFFFF)
            self.sock.send(tc)

    def startAcq(self):
        if self.recvThread is not None:
            dlg = StartAcqDialog()
            if dlg.exec():

                print("Send start acquisition TC")
                print(dlg.source.currentIndex())
                print(dlg.waveNo.text())
                print(dlg.waitUsecs.text())

                # Create data section
                data = struct.pack("<BBBBII", dlg.source.currentIndex(), 0, 0, 0, int(dlg.waveNo.text()), int(dlg.waitUsecs.text()))

                # Compute CRC
                crc = 0xFFFFFFFF
                crc = crc32(crc, data, self.crcTable)

                # Create header
                self.tcCount += 1
                header = struct.pack("<BBHBBHI", 0x8D, 0x00 + 0x0A, 0xC000 + self.tcCount, 0xA0, 0x04, len(data), crc)

                # Send
                self.sock.send(header + data)

                # Clear full waveform counter
                self.wformTotCount = 0

            else:
                print("Start acquisition cancelled")

    def stopAcq(self):
        if self.recvThread is not None:
            self.tcCount += 1
            tc = struct.pack("<BBHBBHI", 0x8D, 0x00 + 0x0A, 0xC000 + self.tcCount, 0xA0, 0x05, 0x0000, 0xFFFFFFFF)
            self.sock.send(tc)

    def tmToWformInit(self, header, data):
        self.wformSeqCount = header[2] & 0x3FFF
        self.wform = Waveform()
        self.wform.read_header(data)

    def tmToWformAdd(self, header, data):
        seqCount = header[2] & 0x3FFF
        self.wformSeqCount += 1
        if self.wformSeqCount == seqCount:
            res = self.wform.read_data(data)
            if res:
                self.wform.print()
                self.wformTotCount += 1
                print("Complete waveform acquired [%d]" % self.wformTotCount)
                self.mplCanvas.axes.cla()
                self.mplCanvas.axes.plot(self.wform.sigt, self.wform.sige)
                self.mplCanvas.axes.axvline(x=self.wform.trigt, color="black", linestyle=(0, (5, 5)))
                self.mplCanvas.axes.set_xlabel("Time [s]")
                self.mplCanvas.axes.set_ylabel("Signal [V]")
                self.mplCanvas.axes.grid()
                self.mplCanvas.draw()
        else:
            print("Sequence error: cur %6d exp %6d" % (seqCount, self.wformSeqCount))


if __name__ == '__main__':

    # Create pyqt5 application
    app = QApplication(sys.argv)

    # Create a window object
    main = Window()

    # Show the window
    main.show()

    # enter message loop
    sys.exit(app.exec_())