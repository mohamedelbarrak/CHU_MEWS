
from PySide6.QtCore import Qt, QTimer, QSize, QRectF
from PySide6.QtGui import QFont, QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QFrame,
    QSizePolicy,
    QStyle
)


# ==========================================
# WIDGET THERMOMETRE
# ==========================================

class ThermometerWidget(QWidget):

    def __init__(self):
        super().__init__()

        self.temperature = 35.0
        self.setFixedSize(155, 215)

    def setTemperature(self, temperature):
        self.temperature = temperature
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Coordonnees internes
        center_x = 65
        top_y = 12
        bottom_y = 166
        bulb_y = 175

        tube_width = 23
        bulb_radius = 30

        # Tube gris
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#D9E1E8"))

        painter.drawRoundedRect(
            QRectF(
                center_x - tube_width / 2,
                top_y,
                tube_width,
                bulb_y - top_y
            ),
            tube_width / 2,
            tube_width / 2
        )

        # Bulbe gris
        painter.drawEllipse(
            QRectF(
                center_x - bulb_radius,
                bulb_y - bulb_radius,
                bulb_radius * 2,
                bulb_radius * 2
            )
        )

        # Calcul de la temperature
        minimum = 35.0
        maximum = 42.0

        value = max(
            minimum,
            min(self.temperature, maximum)
        )

        percentage = (
            (value - minimum) /
            (maximum - minimum)
        )

        liquid_top = (
            bottom_y -
            percentage * (bottom_y - top_y)
        )

        # Liquide bleu
        painter.setBrush(QColor("#1976D2"))

        painter.drawRoundedRect(
            QRectF(
                center_x - 7,
                liquid_top,
                14,
                bulb_y - liquid_top
            ),
            7,
            7
        )

        # Bulbe bleu
        painter.drawEllipse(
            QRectF(
                center_x - 23,
                bulb_y - 23,
                46,
                46
            )
        )

        # Graduations
        painter.setPen(
            QPen(QColor("#8292A2"), 1.5)
        )

        painter.setFont(QFont("Arial", 10))

        for temperature in range(35, 43):
            y = (
                bottom_y -
                ((temperature - 35) / 7) *
                (bottom_y - top_y)
            )

            painter.drawLine(
                int(center_x + 17),
                int(y),
                int(center_x + 25),
                int(y)
            )

            painter.drawText(
                int(center_x + 30),
                int(y + 4),
                f"{temperature}°"
            )


# ==========================================
# PAGE TEMPERATURE
# ==========================================

class TemperaturePage(QWidget):

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
        self.setObjectName("temperaturePage")

        # Variables
        self.temperature = 0.0
        self.measure_running = False
        self.elapsed_time = 0
        self.measure_valid = False

        # ===================================
        # TIMER
        # ===================================
        self.timer = QTimer(self)
        self.timer.timeout.connect(
            self.check_measurement
        )

        # ===================================
        # STYLE
        # ===================================
        self.setStyleSheet("""
            QWidget#temperaturePage {
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

            QPushButton#backButton:pressed {
                background-color: #91C4F2;
            }

            QPushButton#startButton {
                background-color: #DCEEFE;
                color: #145B9C;
                border: 1px solid #A5CBF0;
            }

            QPushButton#stopButton {
                background-color: #FCE1E1;
                color: #B42332;
            }

            QPushButton#nextButton {
                background-color: #D8F4E5;
                color: #176C43;
            }

            QPushButton#startButton:pressed {
                background-color: #91C4F2;
            }

            QPushButton#stopButton:pressed {
                background-color: #F5B9BD;
            }

            QPushButton#nextButton:pressed {
                background-color: #A9E6C4;
            }

            QPushButton:disabled {
                background-color: #E2E5E9;
                color: #9BA3AD;
                border: 1px solid #D7DCE1;
            }

            QFrame#resultCard {
                background-color: white;
                border: 1px solid #DCE6F0;
                border-radius: 12px;
            }

            QLabel#temperatureValue {
                color: #145B9C;
                font-size: 34px;
                font-weight: bold;
            }

            QLabel#temperatureTitle {
                color: #607D98;
                font-size: 13px;
                font-weight: bold;
            }

            QLabel#statusLabel {
                color: #243B53;
                font-size: 17px;
                font-weight: bold;
            }
        """)

        # ===================================
        # LAYOUT PRINCIPAL
        # ===================================
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 12)
        layout.setSpacing(8)

        # ===================================
        # RETOUR + TITRE
        # ===================================
        header = QHBoxLayout()
        header.setSpacing(8)

        back_button = QPushButton()
        back_button.setObjectName("backButton")
        back_button.setFixedSize(44, 40)

        back_button.setIcon(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_ArrowLeft
            )
        )

        back_button.setIconSize(QSize(24, 24))
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.setToolTip(
            "Retour à la pression artérielle"
        )

        back_button.clicked.connect(self.go_back)

        self.titleLabel = QLabel(
            "Mesure de la température"
        )

        self.titleLabel.setFont(
            QFont("Arial", 21, QFont.Bold)
        )

        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setFixedHeight(40)

        right_space = QWidget()
        right_space.setFixedWidth(44)

        header.addWidget(back_button)
        header.addWidget(self.titleLabel, 1)
        header.addWidget(right_space)

        # ===================================
        # INSTRUCTIONS
        # ===================================
        self.infoLabel = QLabel(
            "Approchez le front du capteur, "
            "puis appuyez sur COMMENCER."
        )

        self.infoLabel.setAlignment(Qt.AlignCenter)
        self.infoLabel.setFont(QFont("Arial", 12))
        self.infoLabel.setWordWrap(True)
        self.infoLabel.setFixedHeight(35)

        # ===================================
        # THERMOMETRE
        # ===================================
        self.thermometer = ThermometerWidget()

        # ===================================
        # CARTE DE RESULTAT
        # ===================================
        result_card = QFrame()
        result_card.setObjectName("resultCard")
        result_card.setFixedHeight(185)

        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(15, 12, 15, 12)
        result_layout.setSpacing(8)

        temperature_title = QLabel("TEMPÉRATURE")
        temperature_title.setObjectName(
            "temperatureTitle"
        )
        temperature_title.setAlignment(Qt.AlignCenter)

        self.temperatureLabel = QLabel("--.- °C")
        self.temperatureLabel.setObjectName(
            "temperatureValue"
        )
        self.temperatureLabel.setAlignment(
            Qt.AlignCenter
        )

        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(
            "background-color: #DCE6F0;"
            "max-height: 1px;"
            "border: none;"
        )

        self.statusLabel = QLabel(
            "Prêt pour la mesure"
        )
        self.statusLabel.setObjectName("statusLabel")
        self.statusLabel.setAlignment(Qt.AlignCenter)
        self.statusLabel.setWordWrap(True)

        result_layout.addWidget(temperature_title)
        result_layout.addWidget(self.temperatureLabel)
        result_layout.addWidget(separator)
        result_layout.addWidget(self.statusLabel)

        # ===================================
        # THERMOMETRE + RESULTAT
        # ===================================
        measurement_layout = QHBoxLayout()
        measurement_layout.setSpacing(25)

        measurement_layout.addStretch(1)

        measurement_layout.addWidget(
            self.thermometer,
            alignment=Qt.AlignCenter
        )

        measurement_layout.addWidget(
            result_card,
            2
        )

        measurement_layout.addStretch(1)

        # ===================================
        # BOUTONS
        # ===================================
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        self.startButton = QPushButton("COMMENCER")
        self.startButton.setObjectName("startButton")
        self.startButton.setFixedHeight(52)
        self.startButton.clicked.connect(
            self.start_measure
        )

        self.stopButton = QPushButton("ARRÊTER")
        self.stopButton.setObjectName("stopButton")
        self.stopButton.setFixedHeight(52)
        self.stopButton.setEnabled(False)
        self.stopButton.clicked.connect(
            self.stop_measure
        )

        self.nextButton = QPushButton("SUIVANT")
        self.nextButton.setObjectName("nextButton")
        self.nextButton.setFixedHeight(52)
        self.nextButton.setEnabled(False)
        self.nextButton.clicked.connect(
            self.next_page
        )

        for button in (
            self.startButton,
            self.stopButton,
            self.nextButton
        ):
            button.setCursor(Qt.PointingHandCursor)
            button.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed
            )
            buttons_layout.addWidget(button, 1)

        # ===================================
        # ASSEMBLAGE FINAL
        # ===================================
        layout.addLayout(header)
        layout.addWidget(self.infoLabel)

        layout.addStretch(1)

        layout.addLayout(measurement_layout)

        layout.addStretch(1)

        layout.addLayout(buttons_layout)

    # ===================================
    # BOUTON RETOUR
    # ===================================
    def go_back(self):
        self.reset_page()

        # Retour à la page précédente
        self.main_window.go_to_blood_pressure()

    # ===================================
    # COMMENCER LA MESURE
    # ===================================
    def start_measure(self):
        self.reset_page()

        self.measure_running = True

        self.statusLabel.setText("Mesure en cours...")

        self.infoLabel.setText(
            "Restez immobile devant le capteur."
        )

        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.nextButton.setEnabled(False)

        # TODO :
        # Démarrer le capteur de température Arduino.
        # Exemple :
        # self.serial.write(b"START_TEMP\\n")

        self.timer.start(500)

    # ===================================
    # VERIFICATION DE LA MESURE
    # ===================================
    def check_measurement(self):
        if not self.measure_running:
            return

        self.elapsed_time += 1

        # TODO :
        # Lire la température depuis l'Arduino
        # et appeler :
        # self.receive_temperature(temperature)

        # Simulation temporaire : 36.7 °C
        # après 3 secondes
        if self.elapsed_time == 6:
            self.receive_temperature(36.7)
            return

        # Timeout après 60 secondes
        if self.elapsed_time >= 120:
            self.show_measure_error()

    # ===================================
    # RECEPTION DE LA TEMPERATURE
    # ===================================
    def receive_temperature(self, temperature):

        if not self.measure_running:
            return

        # Vérification de la valeur reçue
        if not 30 <= temperature <= 45:
            self.show_measure_error()
            return

        self.timer.stop()
        self.measure_running = False

        self.temperature = temperature
        self.measure_valid = True

        self.temperatureLabel.setText(
            f"{temperature:.1f} °C"
        )

        self.thermometer.setTemperature(
            temperature
        )

        self.statusLabel.setText(
            "Mesure terminée"
        )

        self.infoLabel.setText(
            "Température mesurée avec succès."
        )

        # Sauvegarde dans Patient
        if hasattr(self.main_window, "patient"):
            self.main_window.patient.temperature = (
                temperature
            )

        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.nextButton.setEnabled(True)

    # ===================================
    # ARRETER LA MESURE
    # ===================================
    def stop_measure(self):
        self.timer.stop()
        self.measure_running = False
        self.measure_valid = False

        self.statusLabel.setText("Mesure arrêtée")

        self.infoLabel.setText(
            "Vous pouvez recommencer la mesure."
        )

        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.nextButton.setEnabled(False)

        # TODO :
        # Envoyer la commande d'arrêt au capteur.

    # ===================================
    # ERREUR DE MESURE
    # ===================================
    def show_measure_error(self):
        self.timer.stop()
        self.measure_running = False
        self.measure_valid = False

        self.statusLabel.setText("Échec de la mesure")

        self.infoLabel.setText(
            "Vérifiez le capteur et réessayez."
        )

        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.nextButton.setEnabled(False)

        QMessageBox.warning(
            self,
            "Erreur de mesure",
            "La température n'a pas pu être mesurée.\n"
            "Veuillez vérifier la position du capteur "
            "et réessayer."
        )

    # ===================================
    # PAGE SUIVANTE
    # ===================================
    def next_page(self):
        if self.measure_running or not self.measure_valid:
            return

        self.main_window.patient.temperature = (
            self.temperature
        )

        print("Température :", self.temperature)

        if hasattr(
            self.main_window,
            "go_to_consciousness"
        ):
            self.main_window.go_to_consciousness()
        else:
            print(
                "La page de conscience AVPU "
                "n'est pas encore disponible."
            )

    # ===================================
    # REINITIALISATION
    # ===================================
    def reset_page(self):
        self.timer.stop()

        self.measure_running = False
        self.measure_valid = False
        self.temperature = 0.0
        self.elapsed_time = 0

        self.temperatureLabel.setText("--.- °C")
        self.thermometer.setTemperature(35.0)

        self.statusLabel.setText(
            "Prêt pour la mesure"
        )

        self.infoLabel.setText(
            "Approchez le front du capteur, "
            "puis appuyez sur COMMENCER."
        )

        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.nextButton.setEnabled(False)
