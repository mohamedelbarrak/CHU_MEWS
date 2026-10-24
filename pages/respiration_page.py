
from PySide6.QtCore import Qt, QTimer, QRectF, QSize
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QStyle,
    QSizePolicy
)


# ==========================================
# WIDGET CERCLE - CHRONOMETRE
# ==========================================

class CircularTimer(QWidget):

    def __init__(self):
        super().__init__()

        # Mode test : 6 secondes
        # Pour une vraie mesure : 60 secondes
        self.maximum = 6
        self.value = self.maximum

        self.setFixedSize(170, 170)

    def setValue(self, value):
        self.value = max(0, min(value, self.maximum))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        size = min(self.width(), self.height()) - 22

        rect = QRectF(
            (self.width() - size) / 2,
            (self.height() - size) / 2,
            size,
            size
        )

        # Cercle de fond
        pen = QPen(QColor("#DCE3EA"), 12)
        painter.setPen(pen)
        painter.drawEllipse(rect)

        # Progression bleue
        angle = 360 * self.value / self.maximum

        pen = QPen(QColor("#1976D2"), 12)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        painter.drawArc(
            rect,
            90 * 16,
            -int(angle * 16)
        )

        # Temps restant
        painter.setPen(QColor("#243B53"))
        painter.setFont(QFont("Arial", 35, QFont.Bold))
        painter.drawText(
            rect,
            Qt.AlignCenter,
            str(self.value)
        )


# ==========================================
# PAGE RESPIRATION
# ==========================================

class RespirationPage(QWidget):

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
        self.setObjectName("respirationPage")

        # 6 secondes pour le test
        # Mettre 60 pour la mesure réelle
        self.duration = 6

        self.remaining_time = self.duration
        self.nb_respirations = 0
        self.running = False

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        # ===================================
        # STYLE
        # ===================================
        self.setStyleSheet("""
            QWidget#respirationPage {
                background-color: #F4F7FA;
            }

            QLabel {
                color: #243B53;
                background: transparent;
            }

            QPushButton {
                border: none;
                border-radius: 8px;
                font-size: 17px;
                font-weight: bold;
            }

            QPushButton#backButton {
                background-color: #DCEEFE;
                border: 1px solid #A5CBF0;
            }

            QPushButton#backButton:hover {
                background-color: #BDDDF9;
            }

            QPushButton#startButton {
                background-color: #DCEEFE;
                color: #145B9C;
                border: 1px solid #A5CBF0;
            }

            QPushButton#respButton {
                background-color: #1976D2;
                color: white;
            }

            QPushButton#nextButton {
                background-color: #D8F4E5;
                color: #176C43;
            }

            QPushButton#startButton:pressed {
                background-color: #91C4F2;
            }

            QPushButton#respButton:pressed {
                background-color: #0D47A1;
            }

            QPushButton#nextButton:pressed {
                background-color: #A9E6C4;
            }

            QPushButton:disabled {
                background-color: #E2E5E9;
                color: #9BA3AD;
                border: 1px solid #D7DCE1;
            }

            QLabel#countLabel {
                color: #145B9C;
                font-size: 30px;
                font-weight: bold;
            }

            QLabel#countTitle {
                color: #607D98;
                font-size: 15px;
            }
        """)

        # ===================================
        # LAYOUT PRINCIPAL
        # ===================================
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 12)
        layout.setSpacing(7)

        # ===================================
        # BOUTON RETOUR + TITRE
        # ===================================
        header = QHBoxLayout()
        header.setSpacing(8)

        back_button = QPushButton()
        back_button.setObjectName("backButton")
        back_button.setFixedSize(44, 40)
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.setToolTip("Retour à l'identification")

        back_button.setIcon(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_ArrowLeft
            )
        )
        back_button.setIconSize(QSize(24, 24))
        back_button.clicked.connect(self.go_back)

        title = QLabel("Fréquence respiratoire")
        title.setFont(QFont("Arial", 21, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setFixedHeight(40)

        right_space = QWidget()
        right_space.setFixedWidth(44)

        header.addWidget(back_button)
        header.addWidget(title, 1)
        header.addWidget(right_space)

        # ===================================
        # INSTRUCTIONS
        # ===================================
        instruction = QLabel(
            "Après chaque respiration, appuyez sur RESPIRATION."
        )
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setFont(QFont("Arial", 13))
        instruction.setWordWrap(True)
        instruction.setFixedHeight(28)

        duration_label = QLabel(
            f"Durée du comptage : {self.duration} secondes"
        )
        duration_label.setAlignment(Qt.AlignCenter)
        duration_label.setFont(QFont("Arial", 12))
        duration_label.setStyleSheet("color: #607D98;")
        duration_label.setFixedHeight(24)

        # ===================================
        # CHRONOMETRE
        # ===================================
        self.circular = CircularTimer()
        self.circular.maximum = self.duration
        self.circular.setValue(self.duration)

        # ===================================
        # COMPTEUR RESPIRATIONS
        # ===================================
        count_container = QVBoxLayout()
        count_container.setSpacing(5)

        count_title = QLabel("RESPIRATIONS")
        count_title.setObjectName("countTitle")
        count_title.setAlignment(Qt.AlignCenter)

        self.countLabel = QLabel("0")
        self.countLabel.setObjectName("countLabel")
        self.countLabel.setAlignment(Qt.AlignCenter)

        count_container.addWidget(count_title)
        count_container.addWidget(self.countLabel)

        # Cercle à gauche, compteur à droite
        measurement_layout = QHBoxLayout()
        measurement_layout.setSpacing(35)

        measurement_layout.addStretch(1)
        measurement_layout.addWidget(self.circular)
        measurement_layout.addLayout(count_container)
        measurement_layout.addStretch(1)

        # ===================================
        # BOUTONS
        # ===================================
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        self.startButton = QPushButton("COMMENCER")
        self.startButton.setObjectName("startButton")
        self.startButton.setFixedHeight(55)
        self.startButton.setCursor(Qt.PointingHandCursor)
        self.startButton.clicked.connect(self.start_measure)

        self.respButton = QPushButton("RESPIRATION")
        self.respButton.setObjectName("respButton")
        self.respButton.setFixedHeight(55)
        self.respButton.setEnabled(False)
        self.respButton.setCursor(Qt.PointingHandCursor)
        self.respButton.clicked.connect(self.add_respiration)

        self.nextButton = QPushButton("SUIVANT")
        self.nextButton.setObjectName("nextButton")
        self.nextButton.setFixedHeight(55)
        self.nextButton.setEnabled(False)
        self.nextButton.setCursor(Qt.PointingHandCursor)
        self.nextButton.clicked.connect(self.next_page)

        for button in (
            self.startButton,
            self.respButton,
            self.nextButton
        ):
            button.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed
            )
            buttons_layout.addWidget(button, 1)

        # ===================================
        # ASSEMBLAGE
        # ===================================
        layout.addLayout(header)
        layout.addWidget(instruction)
        layout.addWidget(duration_label)

        layout.addStretch(1)

        layout.addLayout(measurement_layout)

        layout.addStretch(1)

        layout.addLayout(buttons_layout)

    # ===================================
    # RETOUR A PPM
    # ===================================
    def go_back(self):
        # Arrêter le chronomètre avant de quitter
        self.timer.stop()
        self.running = False

        # Réinitialiser la page
        self.reset_page()

        self.main_window.go_to_ppm()

    # ===================================
    # COMMENCER
    # ===================================
    def start_measure(self):
        self.reset_page()

        self.running = True

        self.startButton.setEnabled(False)
        self.respButton.setEnabled(True)
        self.nextButton.setEnabled(False)

        self.timer.start(1000)

    # ===================================
    # MISE A JOUR DU CHRONOMETRE
    # ===================================
    def update_timer(self):
        if not self.running:
            return

        self.remaining_time -= 1
        self.circular.setValue(self.remaining_time)

        if self.remaining_time <= 0:
            self.timer.stop()
            self.running = False

            self.circular.setValue(0)
            self.respButton.setEnabled(False)
            self.nextButton.setEnabled(True)
            self.startButton.setEnabled(True)

            self.main_window.patient.frequence_respiratoire = (
                self.nb_respirations
            )

            print(
                "Respiration enregistrée :",
                self.main_window.patient.frequence_respiratoire
            )

    # ===================================
    # AJOUTER UNE RESPIRATION
    # ===================================
    def add_respiration(self):
        if not self.running:
            return

        self.nb_respirations += 1
        self.countLabel.setText(
            str(self.nb_respirations)
        )

    # ===================================
    # PAGE SUIVANTE
    # ===================================
    def next_page(self):
        if self.running or self.remaining_time > 0:
            return

        self.main_window.patient.frequence_respiratoire = (
            self.nb_respirations
        )

        self.main_window.go_to_blood_pressure()

    # ===================================
    # REINITIALISATION
    # ===================================
    def reset_page(self):
        self.timer.stop()

        self.running = False
        self.remaining_time = self.duration
        self.nb_respirations = 0

        self.circular.setValue(self.duration)
        self.countLabel.setText("0")

        self.startButton.setEnabled(True)
        self.respButton.setEnabled(False)
        self.nextButton.setEnabled(False)
