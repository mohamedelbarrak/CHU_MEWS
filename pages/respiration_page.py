from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)


# ===========================================================
#      WIDGET CERCLE (CHRONOMETRE)
# ===========================================================

class CircularTimer(QWidget):

    def __init__(self):

        super().__init__()

        self.value = 6###
        self.maximum = 6###

        self.setMinimumSize(320,320)

    def setValue(self,value):

        self.value=value
        self.update()

    def paintEvent(self,event):

        painter=QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        size=min(self.width(),self.height())-25

        rect=QRectF(
            (self.width()-size)/2,
            (self.height()-size)/2,
            size,
            size
        )

        # Cercle gris

        pen=QPen(QColor(220,220,220),18)

        painter.setPen(pen)

        painter.drawEllipse(rect)

        # Progression bleue

        angle=360*self.value/self.maximum

        pen=QPen(QColor("#1976D2"),18)

        painter.setPen(pen)

        painter.drawArc(
            rect,
            90*16,
            -angle*16
        )

        # Temps

        painter.setPen(Qt.black)

        font=QFont("Arial",42,QFont.Bold)

        painter.setFont(font)

        painter.drawText(
            rect,
            Qt.AlignCenter,
            str(self.value)
        )


# ===========================================================
#              PAGE RESPIRATION
# ===========================================================

class RespirationPage(QWidget):

    def __init__(self,main_window):

        super().__init__()

        self.main_window=main_window

        self.remaining_time=6###

        self.nb_respirations=0

        self.running=False

        # Timer

        self.timer=QTimer()

        self.timer.timeout.connect(self.update_timer)

        # =========================
        # STYLE
        # =========================

        self.setStyleSheet("""

        QLabel{

            color:#2c3e50;

        }

        QPushButton{

            background:#1976D2;

            color:white;

            border:none;

            border-radius:15px;

            font-size:22px;

            padding:18px;

        }

        QPushButton:hover{

            background:#1565C0;

        }

        QPushButton:disabled{

            background:#bdbdbd;

        }

        """)

        # =========================
        # TITRE
        # =========================

        titre=QLabel("Fréquence respiratoire")

        titre.setAlignment(Qt.AlignCenter)

        titre.setFont(QFont("Arial",28,QFont.Bold))

        # =========================
        # EXPLICATION
        # =========================

        explication=QLabel(

            "Après chaque respiration,\n"
            "appuyez sur le bouton RESPIRATION.\n\n"
            "Le comptage dure 60 secondes."

        )

        explication.setAlignment(Qt.AlignCenter)

        explication.setFont(QFont("Arial",16))

        # =========================
        # CERCLE
        # =========================

        self.circular=CircularTimer()

        # =========================
        # NOMBRE RESPIRATION
        # =========================

        self.countLabel=QLabel("FR : 0")

        self.countLabel.setAlignment(Qt.AlignCenter)

        self.countLabel.setFont(QFont("Arial",24,QFont.Bold))

        # =========================
        # BOUTONS
        # =========================

        self.startButton=QPushButton("COMMENCER")

        self.startButton.setMinimumHeight(70)

        self.startButton.clicked.connect(self.start_measure)

        self.respButton=QPushButton("RESPIRATION")

        self.respButton.setMinimumHeight(90)

        self.respButton.setEnabled(False)

        self.respButton.clicked.connect(self.add_respiration)

        self.nextButton=QPushButton("SUIVANT")

        self.nextButton.setMinimumHeight(70)

        self.nextButton.setEnabled(False)

        self.nextButton.clicked.connect(self.next_page)

        # =========================
        # LAYOUT
        # =========================

        layout=QVBoxLayout()

        layout.setSpacing(25)

        layout.addStretch()

        layout.addWidget(titre)

        layout.addWidget(explication)

        layout.addWidget(self.circular,alignment=Qt.AlignCenter)

        layout.addWidget(self.countLabel)

        # layout.addWidget(self.startButton)

        # layout.addWidget(self.respButton)

        # layout.addWidget(self.nextButton)

        layout.setSpacing(30)

        buttons_layout = QHBoxLayout()

        buttons_layout.setSpacing(15)

        buttons_layout.addWidget(self.startButton)
        buttons_layout.addWidget(self.respButton)
        buttons_layout.addWidget(self.nextButton)

        layout.addLayout(buttons_layout)

        layout.addStretch()

        self.setLayout(layout)

            # ==========================================================
    # COMMENCER LA MESURE
    # ==========================================================

    def start_measure(self):

        # Réinitialisation
        self.remaining_time = 6###
        self.nb_respirations = 0

        self.circular.setValue(6)###

        self.countLabel.setText("Respirations : 0")

        self.running = True

        # Boutons
        self.startButton.setEnabled(False)
        self.respButton.setEnabled(True)
        self.nextButton.setEnabled(False)

        # Timer : 1 seconde
        self.timer.start(1000)


    # ==========================================================
    # MISE A JOUR DU CHRONOMETRE
    # ==========================================================

    def update_timer(self):

        self.remaining_time -= 1

        self.circular.setValue(self.remaining_time)

        if self.remaining_time <= 0:

            self.timer.stop()

            self.running = False

            self.circular.setValue(0)

            self.respButton.setEnabled(False)

            self.nextButton.setEnabled(True)

            self.startButton.setEnabled(True)

            # Sauvegarde
            self.main_window.patient.frequence_respiratoire = self.nb_respirations

            print("Respiration enregistrée :",
                  self.main_window.patient.frequence_respiratoire)


    # ==========================================================
    # AJOUTER UNE RESPIRATION
    # ==========================================================

    def add_respiration(self):

        if not self.running:
            return

        self.nb_respirations += 1

        self.countLabel.setText(
            f"Respirations : {self.nb_respirations}"
        )


    # ==========================================================
    # PAGE SUIVANTE
    # ==========================================================

   # def next_page(self):

        #print("PPM :", self.main_window.patient.ppm)

        #print(
        #    "Respirations :",
        #    self.main_window.patient.frequence_respiratoire
        #)

        # Aller vers la prochaine page
        # self.main_window.go_to_temperature()
        #self.main_window.go_to_blood_pressure()

    def next_page(self):

        self.main_window.patient.frequence_respiratoire = self.nb_respirations

        print("=================================")
        print("PPM :", self.main_window.patient.ppm)
        print("Respirations :", self.main_window.patient.frequence_respiratoire)
        print("=================================")

        if hasattr(self.main_window, "go_to_blood_pressure"):
            self.main_window.go_to_blood_pressure()
        else:
            print("Erreur : go_to_blood_pressure() n'existe pas dans MainWindow.")


    def reset_page(self):

        self.timer.stop()

        self.running = False

        self.remaining_time = 6###

        self.nb_respirations = 0

        self.circular.setValue(6)###

        self.countLabel.setText("Respirations : 0")

        self.startButton.setEnabled(True)

        self.respButton.setEnabled(False)

        self.nextButton.setEnabled(False)