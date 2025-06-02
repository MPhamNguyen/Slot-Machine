import sys
import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QDesktopWidget
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import QTimer, Qt, QUrl, QCoreApplication, QTimer
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtMultimedia import QSoundEffect

slots = 4 #Num of icons
screenHeight = 160 #Size for a single slot to be shown (px)
viewportOffset = 160 #Y-Offset of slot from y=0 (px)
numOfStrips = 5 #Num of strips
tick = 10 #Tick rate

class SlotStrip(QLabel):
    def __init__(self, parent=None, ghostStrip=None, x=0, y=viewportOffset, width=screenHeight, height=screenHeight*4, id=1, spin=False):
        super().__init__(parent)
        self.parent = parent
        self.id = id
        self.ghostStrip = ghostStrip
        self.counter = 0
        self.switch = True
        self.endSequence = False
        self.targetPos = 0
        self.spinRate = 20 
        self.spins = -1

        self.setGeometry(x,y,width,height)
        self.setPixmap(QPixmap("slotmachine.png"))
        self.setScaledContents(True)

        if (ghostStrip):
            self.id = id
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.move_label)

    def move_label(self):
        if (not self.endSequence):
            #Handles moving each strip normally
            if (self.switch):
                if (self.pos().y() >= screenHeight * -(slots) + viewportOffset):
                    self.move(self.pos().x(), self.pos().y() - self.spinRate)
            else:
                if (self.ghostStrip.pos().y() >= screenHeight * -(slots) + viewportOffset):
                    self.ghostStrip.move(self.ghostStrip.pos().x(), self.ghostStrip.pos().y() - self.spinRate)

            #Starts moving ghoststrip when normstrip is about to run off
            if (self.pos().y() < screenHeight * -(slots - 1) + viewportOffset):
                self.ghostStrip.move(self.pos().x(), self.ghostStrip.pos().y() - self.spinRate)

            #Starts moving normstrip when ghoststrip is about to run off
            if (self.ghostStrip.pos().y() < screenHeight * -(slots - 1) + viewportOffset):
                self.move(self.pos().x(), self.pos().y() - self.spinRate)

            #Sets normstrip back to start
            if (self.pos().y() <= (screenHeight * -slots) + viewportOffset):
                self.switch = False
                self.counter += 1
                self.move(self.pos().x(), screenHeight + viewportOffset)

            #Sets ghoststrip back to start
            if (self.ghostStrip.pos().y() <= (screenHeight * -slots) + viewportOffset):
                self.switch = True
                self.counter += 1
                self.ghostStrip.move(self.ghostStrip.pos().x(), screenHeight + viewportOffset)

            #Condition to end
            if (self.counter == self.spins):
                self.endSequence = True
                self.targetPos = -screenHeight * self.parent.getSlotTargets(self.id) + viewportOffset

        else:
            if (self.switch):
                if (self.pos().y() > self.targetPos):
                    self.move(self.pos().x(), self.pos().y() - self.spinRate)
                else:
                    self.playLandingSound()
                    self.stopSpin()

                    if (self.id == numOfStrips):
                        self.sequenceFinished()
            else:
                if (self.ghostStrip.pos().y() > self.targetPos):
                    self.ghostStrip.move(self.ghostStrip.pos().x(), self.ghostStrip.pos().y() - self.spinRate)
                else:
                    self.playLandingSound()
                    self.stopSpin()

                    if (self.id == numOfStrips):
                        self.sequenceFinished()

    def sequenceFinished(self):
        self.parent.playSpinSounds(False)
        self.parent.debounce = True
        
        if (self.parent.winFlag):
            self.parent.sounds["slotWin"].play()

    def playLandingSound(self):
        self.parent.sounds["slotLand"].play()

    def stopSpin(self):
        self.timer.stop()

    def reset(self):
        self.counter = 0
        self.spins = -1
        self.endSequence = False
        self.parent.sounds["slotWin"].stop()
        self.staggeredStart()
        

    def staggeredStart(self):
        #Staggers when each slot starts to spin again
        delay = self.id * 100 
        QTimer.singleShot(delay, lambda: self.timer.start(tick))

    def endingSequence(self):
        if (self.id == 1):
            self.spins = 1 + self.counter 
        if (self.id == numOfStrips):
            self.spins = 3 + self.counter + ((self.id - 1) * 2)
        else:
            self.spins = 1 + self.counter + ((self.id - 1) * 2)
        

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.slotTargets = [0,0,0,0,0]
        self.toggle = False #Controls button functionality from slot stop/reset
        self.debounce = False #Prevents button spam
        self.winFlag = False #Win flag
        
        #Calculates if you win on startup
        self.win()

        # self.setGeometry(700,500,screenHeight * numOfStrips,screenHeight + 100) #Sets window size
        self.setGeometry(700,500,800,480) #Sets window size

        #Centers window
        centerPoint = QDesktopWidget().availableGeometry().center()
        temp = self.frameGeometry()
        temp.moveCenter(centerPoint)
        self.move(temp.topLeft())

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        #Initialize sounds
        self.sounds = {
            "slotLoop": QSoundEffect(),
            "slotLand": QSoundEffect(),
            "slotWin": QSoundEffect(),
        }
        self.sounds["slotLoop"].setSource(QUrl.fromLocalFile("slotloop.wav"))
        self.sounds["slotLoop"].setLoopCount(QSoundEffect.Infinite)
        self.sounds["slotLoop"].setVolume(0.1)

        self.sounds["slotLand"].setSource(QUrl.fromLocalFile("slotland1.wav"))
        self.sounds["slotLand"].setLoopCount(1)
        self.sounds["slotLand"].setVolume(0.15)

        self.sounds["slotWin"].setSource(QUrl.fromLocalFile("slotwin.wav"))
        self.sounds["slotWin"].setLoopCount(2)
        self.sounds["slotWin"].setVolume(0.2)

        for sound in self.sounds.values():
            while sound.status() != QSoundEffect.Ready:
                QCoreApplication.processEvents()

        #Initialized UI
        self.initialize()

    def win(self):
        probability = random.random()
        winRate = 0.5

        if (probability <= winRate):
            targetSlot = random.randint(0,slots - 1)
            self.slotTargets = [targetSlot, targetSlot, targetSlot, targetSlot, targetSlot]
            self.winFlag = True
        else:
            first, second, third, fourth, fifth = random.randint(0,slots - 1), random.randint(0,slots - 1), random.randint(0,slots - 1), random.randint(0,slots - 1), random.randint(0,slots - 1)

            while (second == first):
                second = random.randint(0,slots - 1)
            
            while (third == first and third == second):
                third = random.randint(0,slots - 1)

            while (fourth == first and fourth == second and fourth == third):
                third = random.randint(0,slots - 1)

            while (fifth == first and fifth == second and fifth == third and fifth == fourth):
                third = random.randint(0,slots - 1)

            self.slotTargets[0] = first
            self.slotTargets[1] = second
            self.slotTargets[2] = third
            self.slotTargets[3] = fourth
            self.slotTargets[4] = fifth
            self.winFlag = False

    def playSpinSounds(self, switch):
        if (switch):
            self.sounds["slotLoop"].play()
        else:
            self.sounds["slotLoop"].stop()
        
    def buttonPress(self):
        if self.toggle and self.debounce: #Restarts spinning animation
            self.win()
            self.playSpinSounds(True)
            self.slotstrip1.reset()
            self.slotstrip2.reset()
            self.slotstrip3.reset()
            self.slotstrip4.reset()
            self.slotstrip5.reset()
            self.toggle = False
            self.debounce = False
        elif (not self.toggle): #Stop the spinning animation
            self.slotstrip1.endingSequence()
            self.slotstrip2.endingSequence()
            self.slotstrip3.endingSequence()
            self.slotstrip4.endingSequence()
            self.slotstrip5.endingSequence()
            self.toggle = True


    def getSlotTargets(self, slotId):
        return self.slotTargets[slotId - 1]

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Q:
            self.slotstrip1.restart()

    def initialize(self):
        #Create slot objects
        self.slotstrip1Ghost = SlotStrip(self, None, viewportOffset, screenHeight + viewportOffset)
        self.slotstrip1 = SlotStrip(self, self.slotstrip1Ghost, id=1, spin=True)

        self.slotstrip2Ghost = SlotStrip(self, None, screenHeight, screenHeight + viewportOffset)
        self.slotstrip2 = SlotStrip(self, self.slotstrip2Ghost, screenHeight, viewportOffset, id=2, spin=True)

        self.slotstrip3Ghost = SlotStrip(self, None, screenHeight*2, screenHeight + viewportOffset)
        self.slotstrip3 = SlotStrip(self, self.slotstrip3Ghost, screenHeight*2, viewportOffset, id=3, spin=True)

        self.slotstrip4Ghost = SlotStrip(self, None, screenHeight*3, screenHeight + viewportOffset)
        self.slotstrip4 = SlotStrip(self, self.slotstrip4Ghost, screenHeight*3, viewportOffset, id=4, spin=True)

        self.slotstrip5Ghost = SlotStrip(self, None, screenHeight*4, screenHeight + viewportOffset)
        self.slotstrip5 = SlotStrip(self, self.slotstrip5Ghost, screenHeight*4, viewportOffset, id=5, spin=True)


        #UI Things
        self.topBorder = QLabel(self)
        self.topBorder.setGeometry(0, -2, screenHeight * numOfStrips, viewportOffset)
        self.topBorder.setStyleSheet("background-color: #850b04;")
        self.topBorder.setPixmap(QPixmap("slotbackground1.png"))

        self.topBorderDivide = QLabel(self)
        self.topBorderDivide.setGeometry(0, viewportOffset - 2, screenHeight * numOfStrips, 2)
        self.topBorderDivide.setStyleSheet("background-color: black;")

        self.botBorder = QLabel(self)
        self.botBorder.setGeometry(0, viewportOffset + screenHeight + 2, screenHeight * numOfStrips, self.height() - (viewportOffset + screenHeight) - 2)
        self.botBorder.setStyleSheet("background-color: #850b04;")
        self.botBorder.setPixmap(QPixmap("slotbackground1.png"))

        self.botBorderDivide = QLabel(self)
        self.botBorderDivide.setGeometry(0, viewportOffset + screenHeight, screenHeight * numOfStrips, 2)
        self.botBorderDivide.setStyleSheet("background-color: black;")
        
        #Temp button
        self.button = QPushButton("SPIN", self)
        self.button.setGeometry(self.width() - 110,self.height() - 90,100,80)
        font_size = int(min(self.button.width(), self.button.height()) * 0.4)
        font = QFont("Impact", font_size, QFont.Bold)
        self.button.setFont(font)
        self.button.setStyleSheet(
        """
        background-color: #e5b31a;
        color: black;
        border: 2px solid black;
        border-radius: 10px;
        text-transform: uppercase;                          
        """)
        self.button.clicked.connect(self.buttonPress)
        self.playSpinSounds(True)

        #Title
        self.title = QLabel(self)
        self.title.setGeometry(147,20,506,120)
        self.title.setPixmap(QPixmap("title.png"))
        self.title.setScaledContents(True)

        # self.show() #For testing purposes
        self.showFullScreen() #Comment back on live version

        #Initial Startup
        self.slotstrip1.staggeredStart()
        self.slotstrip2.staggeredStart()
        self.slotstrip3.staggeredStart()
        self.slotstrip4.staggeredStart()
        self.slotstrip5.staggeredStart()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
