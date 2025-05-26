import sys
import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import QTimer, Qt, QUrl, QCoreApplication
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtMultimedia import QSoundEffect

""""
TO-DO
- Work on better sounds
-Replace spins with a button press that controls when to stop
"""


slots = 4
screenHeight = 160
numOfTargetSlots = 5

class SlotStrip(QLabel):
    def __init__(self, parent=None, ghostStrip=None, x=0, y=0, width=screenHeight, height=screenHeight*4, id=1, spin=False, tick=10):
        super().__init__(parent)
        self.parent = parent
        self.id = id
        self.ghostStrip = ghostStrip
        self.temp = 0
        self.switch = True
        self.endSequence = False
        self.targetPos = 0
        self.spinRate = 20 
        self.spins = 2 + (self.id * 2) #Controls how many spins before starting ending sequence 

        self.setGeometry(x,y,width,height)
        self.setPixmap(QPixmap("slotmachine.png"))
        self.setScaledContents(True)

        if (ghostStrip):
            self.id = id
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.move_label)
            self.timer.start(tick)

    def move_label(self):
        if (not self.endSequence):
            #Handles moving each strip normally
            if (self.switch):
                if (self.pos().y() >= screenHeight * -(slots)):
                    self.move(self.pos().x(), self.pos().y() - self.spinRate)
            else:
                if (self.ghostStrip.pos().y() >= screenHeight * -(slots)):
                    self.ghostStrip.move(self.ghostStrip.pos().x(), self.ghostStrip.pos().y() - self.spinRate)

            #Starts moving ghoststrip when normstrip is about to run off
            if (self.pos().y() < screenHeight * -(slots - 1)):
                self.ghostStrip.move(self.pos().x(), self.ghostStrip.pos().y() - self.spinRate)

            #Starts moving normstrip when ghoststrip is about to run off
            if (self.ghostStrip.pos().y() < screenHeight * -(slots - 1)):
                self.move(self.pos().x(), self.pos().y() - self.spinRate)

            #Sets normstrip back to start
            if (self.pos().y() <= screenHeight * -slots):
                self.switch = False
                self.temp += 1
                self.move(self.pos().x(), screenHeight)

            #Sets ghoststrip back to start
            if (self.ghostStrip.pos().y() <= screenHeight * -slots):
                self.switch = True
                self.temp += 1
                self.ghostStrip.move(self.ghostStrip.pos().x(), screenHeight)

            #Condition to end
            if (self.temp == self.spins):
                self.endSequence = True
                # self.targetPos = -screenHeight * self.parent.getSlotTargets(self.id)
                self.targetPos = -screenHeight * 0

        else:
            if (self.switch):
                if (self.pos().y() > self.targetPos):
                    self.move(self.pos().x(), self.pos().y() - self.spinRate)
                else:
                    self.playLandingSound()
                    self.stopSpin()

                    if (self.id == numOfTargetSlots):
                        self.sequenceFinished()
            else:
                if (self.ghostStrip.pos().y() > self.targetPos):
                    self.ghostStrip.move(self.ghostStrip.pos().x(), self.ghostStrip.pos().y() - self.spinRate)
                else:
                    self.playLandingSound()
                    self.stopSpin()
                    if (self.id == numOfTargetSlots):
                        self.sequenceFinished()

    def sequenceFinished(self):
        self.parent.playSpinSounds(False)

    def playLandingSound(self):
        self.parent.sounds["slotLand"].play()

    def stopSpin(self):
        self.timer.stop()

    def reset(self):
        self.temp = 0
        self.endSequence = False
        self.timer.start()
        

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.slotTargets = [0,0,0,0,0]
        
        #Calculates if you win on startup
        self.win()

        self.setGeometry(700,500,screenHeight * numOfTargetSlots,screenHeight + 100) #Sets window size

        self.sounds = {
            "slotLoop": QSoundEffect(),
            "slotLand": QSoundEffect()
        }
        self.sounds["slotLoop"].setSource(QUrl.fromLocalFile("slotloop.wav"))
        self.sounds["slotLand"].setSource(QUrl.fromLocalFile("slotland.wav"))


        self.sounds["slotLoop"].setLoopCount(QSoundEffect.Infinite)
        self.sounds["slotLoop"].setVolume(0.1)

        self.sounds["slotLand"].setLoopCount(1)
        self.sounds["slotLand"].setVolume(0.05)

        for sound in self.sounds.values():
            while sound.status() != QSoundEffect.Ready:
                QCoreApplication.processEvents()

        self.initialize()

    def win(self):
        probability = random.random()
        winRate = 0.5

        if (probability <= winRate):
            targetSlot = random.randint(0,3)
            self.slotTargets = [targetSlot, targetSlot, targetSlot, targetSlot, targetSlot]
        else:
            first, second, third, fourth, fifth = random.randint(0,3), random.randint(0,3), random.randint(0,3), random.randint(0,3), random.randint(0,3)

            while (second == first):
                second = random.randint(0,3)
            
            while (third == first and third == second):
                third = random.randint(0,3)

            while (fourth == first and fourth == second and fourth == third):
                third = random.randint(0,3)

            while (fifth == first and fifth == second and fifth == third and fifth == fourth):
                third = random.randint(0,3)

            self.slotTargets[0] = first
            self.slotTargets[1] = second
            self.slotTargets[2] = third
            self.slotTargets[3] = fourth
            self.slotTargets[4] = fifth

    def playSpinSounds(self, switch):
        if (switch):
            self.sounds["slotLoop"].play()
        else:
            self.sounds["slotLoop"].stop()
        
    def reset(self):
        self.win()
        self.playSpinSounds(True)
        self.slotstrip1.reset()
        self.slotstrip2.reset()
        self.slotstrip3.reset()
        self.slotstrip4.reset()
        self.slotstrip5.reset()

    def getSlotTargets(self, slotId):
        return self.slotTargets[slotId - 1]

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Q:
            self.slotstrip1.restart()

    def initialize(self):
        self.slotstrip1Ghost = SlotStrip(self, None, 0, screenHeight)
        self.slotstrip1 = SlotStrip(self, self.slotstrip1Ghost, id=1, spin=True)

        self.slotstrip2Ghost = SlotStrip(self, None, screenHeight, screenHeight)
        self.slotstrip2 = SlotStrip(self, self.slotstrip2Ghost, screenHeight, 0, id=2, spin=True)

        self.slotstrip3Ghost = SlotStrip(self, None, screenHeight*2, screenHeight)
        self.slotstrip3 = SlotStrip(self, self.slotstrip3Ghost, screenHeight*2, 0, id=3, spin=True)

        self.slotstrip4Ghost = SlotStrip(self, None, screenHeight*3, screenHeight)
        self.slotstrip4 = SlotStrip(self, self.slotstrip4Ghost, screenHeight*3, 0, id=4, spin=True)

        self.slotstrip5Ghost = SlotStrip(self, None, screenHeight*4, screenHeight)
        self.slotstrip5 = SlotStrip(self, self.slotstrip5Ghost, screenHeight*4, 0, id=5, spin=True)

        self.botBorder = QLabel(self)
        self.botBorder.setGeometry(0, screenHeight + 2, screenHeight * numOfTargetSlots, self.height() - screenHeight - 2)
        self.botBorder.setStyleSheet("background-color: #850b04;")

        self.botBorderDivide = QLabel(self)
        self.botBorderDivide.setGeometry(0, screenHeight, screenHeight * numOfTargetSlots, 2)
        self.botBorderDivide.setStyleSheet("background-color: black;")

        self.button = QPushButton("SPIN", self)
        self.button.setGeometry(370,170,100,80)
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
        self.button.clicked.connect(self.reset)
        self.playSpinSounds(True)
        self.show()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    # window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
