import sys
import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QDesktopWidget, QWidget
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import QTimer, Qt, QUrl, QCoreApplication, QTimer
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtMultimedia import QSoundEffect

slots = 6 #Num of icons
screenHeight = 160 #Size for a single slot to be shown (px)
viewportOffset = 160 #Y-Offset of slot from y=0 (px)
numOfStrips = 5 #Num of strips
tick = 10 #Tick rate
majorPrizeIndex = 1 #Num corresponding to major prize icon

icons = [num + 1 for num in range(slots)]

temp = 50 

class SlotStrip(QWidget):
    def __init__(self, parent=None, x=0, y=viewportOffset - temp, width=screenHeight, height=screenHeight*slots, id=1, test="slotmachine.png"):
        super().__init__(parent)
        self.setGeometry(x, y, width, height)

        self.parent = parent
        self.id = id
        self.counter = 0
        self.switch = True
        self.endSequence = False
        self.targetPos = 0
        self.spinRate = 20
        self.spins = -1
        self.debounce = True
        self.target = -1
        
        self.innerLayout = icons.copy()
        random.shuffle(self.innerLayout)

        self.innerGhostLayout = icons.copy()
        random.shuffle(self.innerGhostLayout)

        self.inner = QWidget(self)
        self.innerGhost = QWidget(self)
        self.innerGhost.move(0, -(screenHeight * slots))

        for i, path in enumerate(self.innerLayout):
            label = QLabel(self.inner)
            pixmap = QPixmap(f"icon{path}.png").scaled(width, screenHeight, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(pixmap)
            label.setGeometry(0, i * screenHeight, width, screenHeight)
        
        for i, path2 in enumerate(self.innerGhostLayout):
            label = QLabel(self.innerGhost)
            pixmap = QPixmap(f"icon{path2}.png").scaled(width, screenHeight, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(pixmap)
            label.setGeometry(0, i * screenHeight, width, screenHeight)

        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)


    def animate(self):
        if not (self.endSequence):
            self.inner.move(self.inner.pos().x(), self.inner.pos().y() + self.spinRate)
            self.innerGhost.move(self.innerGhost.pos().x(), self.innerGhost.pos().y() + self.spinRate)

            if (self.debounce):
                if (self.inner.pos().y() >= temp + screenHeight):
                    self.switch = False
                    self.counter += 1
                    self.debounce = False
                elif (self.innerGhost.pos().y() >= temp + screenHeight):
                    self.switch = True
                    self.counter += 1
                    self.debounce = False

        if (self.endSequence):
            if (self.switch):
                if (self.inner.pos().y() >= self.targetPos):
                    self.playLandingSound()
                    self.stopSpin()

                    if (self.id == numOfStrips):
                        self.sequenceFinished()
                else:    
                    self.inner.move(self.inner.pos().x(), self.inner.pos().y() + self.spinRate)
                    self.innerGhost.move(self.innerGhost.pos().x(), self.innerGhost.pos().y() + self.spinRate)
            else:
                if (self.innerGhost.pos().y() >= self.targetPos):
                    self.playLandingSound()
                    self.stopSpin()

                    if (self.id == numOfStrips):
                        self.sequenceFinished()
                else:          
                    self.inner.move(self.inner.pos().x(), self.inner.pos().y() + self.spinRate)
                    self.innerGhost.move(self.innerGhost.pos().x(), self.innerGhost.pos().y() + self.spinRate)

        #Sets normstrip back to start
        if (self.inner.pos().y() >= (2 * temp) + screenHeight):
            self.inner.move(0, (2 * (-screenHeight * slots)) + ((2 * temp) + screenHeight))
            self.debounce = True

        #Sets ghoststrip back to start
        if (self.innerGhost.pos().y() >= (2 * temp) + screenHeight):
            self.innerGhost.move(0, (2 * (-screenHeight * slots)) + ((2 * temp) + screenHeight))
            self.debounce = True

        #Condition to end
        if (self.counter == self.spins):
            self.endSequence = True
            if (self.switch):
                self.target = self.innerLayout.index(self.parent.getSlotTargets(self.id) + 1)
            else:
                self.target = self.innerGhostLayout.index(self.parent.getSlotTargets(self.id) + 1)
            self.targetPos = -screenHeight * self.target  + temp

    def sequenceFinished(self):
        self.parent.playSpinSounds(False)
        self.parent.debounce = True
        
        if (self.parent.winFlag):
            if (self.parent.majorWin):
                self.parent.sounds["slotWin"].play()
            else:
                #Play different sound
                pass

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
            self.parent.globalSpin = self.spins
        if (self.id == numOfStrips):
            self.spins = 3 + self.parent.globalSpin + ((self.id - 1) * 2)
        else:
            self.spins = 1 + self.parent.globalSpin + ((self.id - 1) * 2)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.slotTargets = [0,0,0,0,0]
        self.toggle = False #Controls button functionality from slot stop/reset
        self.debounce = False #Prevents button spam
        self.winFlag = False #Win flag
        self.majorWin = False
        self.globalSpin = -1 #Basis for ending
        
        #Calculates if you win on startup
        self.win()

        # self.setGeometry(700,500,screenHeight * numOfStrips,screenHeight + 100) #Sets window size
        self.setGeometry(700,500,800,480) #Sets window size

        #Centers window
        centerPoint = QDesktopWidget().availableGeometry().center()
        temp1 = self.frameGeometry()
        temp1.moveCenter(centerPoint)
        self.move(temp1.topLeft())

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
        self.sounds["slotWin"].setLoopCount(1)
        self.sounds["slotWin"].setVolume(0.1)

        for sound in self.sounds.values():
            while sound.status() != QSoundEffect.Ready:
                QCoreApplication.processEvents()

        #Initialized UI
        self.initialize()

    def win(self):
        probability = random.random()
        winRate = 1

        if (probability <= winRate):
            targetSlot = random.randint(0,slots - 1)
            self.slotTargets = [targetSlot, targetSlot, targetSlot, targetSlot, targetSlot]
            self.winFlag = True

            if (targetSlot == majorPrizeIndex - 1):
                self.majorWin = True
            else:
                self.majorWin = False
        else:
            first, second, third, fourth, fifth = random.randint(0,slots - 1), random.randint(0,slots - 1), random.randint(0,slots - 1), random.randint(0,slots - 1), random.randint(0,slots - 1)

            while (second == first):
                second = random.randint(0,slots - 1)
            
            while (third == first and third == second):
                third = random.randint(0,slots - 1)

            while (fourth == first and fourth == second and fourth == third):
                fourth = random.randint(0,slots - 1)

            while (fifth == first and fifth == second and fifth == third and fifth == fourth):
                fifth = random.randint(0,slots - 1)

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
        # elif event.key() == Qt.Key_Q:
            # print(self.slotstrip1.inner.pos())
            # print(self.slotstrip1.innerGhost.pos())
            # self.slotstrip1.stopSpin()
            # self.slotstrip2.stopSpin()
            # self.slotstrip3.stopSpin()
            # self.slotstrip4.stopSpin()
            # self.slotstrip5.stopSpin()
        # elif event.key() == Qt.Key_P:
        #     self.slotstrip1.timer.start()
        #     self.slotstrip2.timer.start()
        #     self.slotstrip3.timer.start()
        #     self.slotstrip4.timer.start()
        #     self.slotstrip5.timer.start()
        # elif event.key() == Qt.Key_Z:
        #     pass

    def initialize(self):
        #Create slot objects
        self.slotstrip1 = SlotStrip(self, id=1)
        self.slotstrip2 = SlotStrip(self, screenHeight, id=2)
        self.slotstrip3 = SlotStrip(self, screenHeight*2, id=3)
        self.slotstrip4 = SlotStrip(self, screenHeight*3, id=4)
        self.slotstrip5 = SlotStrip(self, screenHeight*4, id=5)

        #UI Things
        self.topBorder = QLabel(self)
        self.topBorder.setGeometry(0, -2, screenHeight * numOfStrips, viewportOffset - temp)
        self.topBorder.setStyleSheet("background-color: #850b04;")
        self.topBorder.setPixmap(QPixmap("slotbackground1.png"))

        self.topBorderDivide = QLabel(self)
        self.topBorderDivide.setGeometry(0, viewportOffset - 2 - temp, screenHeight * numOfStrips, 2)
        self.topBorderDivide.setStyleSheet("background-color: black;")

        self.botBorder = QLabel(self)
        self.botBorder.setGeometry(0, viewportOffset + screenHeight + 2 + temp, screenHeight * numOfStrips, self.height() - (viewportOffset + screenHeight + temp) - 2)
        self.botBorder.setStyleSheet("background-color: #850b04;")
        self.botBorder.setPixmap(QPixmap("slotbackground1.png"))

        self.botBorderDivide = QLabel(self)
        self.botBorderDivide.setGeometry(0, viewportOffset + screenHeight + temp, screenHeight * numOfStrips, 2)
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
        self.title.setGeometry(231,20,338,80)
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

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
