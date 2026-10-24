from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPainter, QColor
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
)


# ==========================================================
# WIDGET THERMOMETRE
# ==========================================================

# ==========================================================
# WIDGET THERMOMETRE
# ==========================================================

class ThermometerWidget(QWidget):

    def __init__(self):

        super().__init__()

        self.temperature = 35.0

        # Zone suffisamment grande pour tout le thermomètre
        self.setMinimumSize(220, 330)

        self.setMaximumHeight(330)

    def setTemperature(self, temperature):

        self.temperature = temperature

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        # ==================================================
        # CENTRE
        # ==================================================

        center_x = self.width() // 2

        # ==================================================
        # DIMENSIONS DU THERMOMETRE
        # ==================================================

        tube_width = 32

        bulb_radius = 42

        top_y = 20

        # Position du centre du bulbe
        bulb_center_y = 255

        # Bas du tube
        tube_bottom = bulb_center_y

        # ==================================================
        # TUBE GRIS
        # ==================================================

        painter.setPen(Qt.NoPen)

        painter.setBrush(
            QColor("#d9d9d9")
        )

        painter.drawRoundedRect(
            center_x - tube_width // 2,
            top_y,
            tube_width,
            tube_bottom - top_y,
            tube_width // 2,
            tube_width // 2
        )

        # ==================================================
        # BULBE GRIS
        # ==================================================

        painter.setBrush(
            QColor("#d9d9d9")
        )

        painter.drawEllipse(
            center_x - bulb_radius,
            bulb_center_y - bulb_radius,
            bulb_radius * 2,
            bulb_radius * 2
        )

        # ==================================================
        # TEMPERATURE
        # ==================================================

        minimum = 35.0
        maximum = 42.0

        value = max(
            minimum,
            min(self.temperature, maximum)
        )

        percentage = (
            value - minimum
        ) / (
            maximum - minimum
        )

        # ==================================================
        # LIQUIDE BLEU
        # ==================================================

        liquid_top = int(
            tube_bottom -
            percentage *
            (tube_bottom - top_y)
        )

        painter.setBrush(
            QColor("#1976D2")
        )

        painter.drawRoundedRect(
            center_x - 9,
            liquid_top,
            18,
            tube_bottom - liquid_top,
            9,
            9
        )

        # ==================================================
        # BULBE BLEU
        # ==================================================

        # Le bulbe bleu est maintenant parfaitement
        # centré dans le bulbe gris.

        blue_bulb_radius = bulb_radius - 9

        painter.setBrush(
            QColor("#1976D2")
        )

        painter.drawEllipse(
            center_x - blue_bulb_radius,
            bulb_center_y - blue_bulb_radius,
            blue_bulb_radius * 2,
            blue_bulb_radius * 2
        )

        # ==================================================
        # GRADUATIONS
        # ==================================================

        painter.setPen(
            QColor("#777777")
        )

        painter.setFont(
            QFont(
                "Arial",
                12
            )
        )

        for i in range(8):

            temperature = 35 + i

            # Position de la graduation
            y = int(
                tube_bottom -
                (
                    i / 7
                ) *
                (
                    tube_bottom - top_y
                )
            )

            # Petite ligne
            painter.drawLine(
                center_x + 28,
                y,
                center_x + 42,
                y
            )

            # Texte
            painter.drawText(
                center_x + 48,
                y + 5,
                f"{temperature}°"
            )

# ==========================================================
# PAGE TEMPERATURE
# ==========================================================

class TemperaturePage(QWidget):

    def __init__(self, main_window):

        super().__init__()

        self.main_window = main_window

        # ==================================================
        # VARIABLES
        # ==================================================

        self.temperature = 0.0

        self.measure_running = False

        self.elapsed_time = 0

        # ==================================================
        # TIMER
        # ==================================================

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.check_measurement
        )

        # ==================================================
        # STYLE GENERAL
        # ==================================================

        self.setStyleSheet("""

        QLabel {

            color: #2c3e50;

        }

        QPushButton {

            background: #1976D2;

            color: white;

            border: none;

            border-radius: 14px;

            font-size: 20px;

            font-weight: bold;

            min-height: 65px;

            padding: 10px 25px;

        }

        QPushButton:hover {

            background: #1565C0;

        }

        QPushButton:disabled {

            background: #bdbdbd;

            color: #eeeeee;

        }

        """)

        # ==================================================
        # LAYOUT PRINCIPAL
        # ==================================================

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            50,
            30,
            50,
            30
        )

        layout.setSpacing(20)

        # ==================================================
        # TITRE
        # ==================================================

        self.titleLabel = QLabel(
            "Mesure de la température"
        )

        self.titleLabel.setAlignment(
            Qt.AlignCenter
        )

        self.titleLabel.setFont(
            QFont(
                "Arial",
                30,
                QFont.Bold
            )
        )

        layout.addWidget(
            self.titleLabel
        )

        # ==================================================
        # ESPACE
        # ==================================================

        #layout.addSpacing(10)

        # ==================================================
        # INSTRUCTIONS
        # ==================================================

        self.infoLabel = QLabel(

            "Veuillez rapprocher votre tête du capteur.\n"
            "Cliquez sur COMMENCER pour démarrer la mesure."

        )

        self.infoLabel.setAlignment(
            Qt.AlignCenter
        )

        self.infoLabel.setFont(
            QFont(
                "Arial",
                21,
                QFont.Bold
            )
        )

        layout.addWidget(
            self.infoLabel
        )

        # ==================================================
        # ESPACE
        # ==================================================

        #layout.addSpacing(10)

        # ==================================================
        # THERMOMETRE
        # ==================================================

        self.thermometer = ThermometerWidget()

        layout.addWidget(
            self.thermometer,
            alignment=Qt.AlignCenter
        )
        layout.addSpacing(30)
        # ==================================================
        # VALEUR TEMPERATURE
        # ==================================================

        self.temperatureLabel = QLabel(
            "--.- °C"
        )

        self.temperatureLabel.setAlignment(
            Qt.AlignCenter
        )

        self.temperatureLabel.setFont(
            QFont(
                "Arial",
                32,
                QFont.Bold
            )
        )

        layout.addWidget(
            self.temperatureLabel
        )

        # ==================================================
        # ETAT
        # ==================================================

        self.statusLabel = QLabel(
            "Prêt pour la mesure"
        )

        self.statusLabel.setAlignment(
            Qt.AlignCenter
        )

        self.statusLabel.setFont(
            QFont(
                "Arial",
                22,
                QFont.Bold
            )
        )

        layout.addWidget(
            self.statusLabel
        )

        # ==================================================
        # ESPACE FLEXIBLE
        # ==================================================

        # Permet de pousser les boutons vers le bas

        layout.addStretch()

        # ==================================================
        # BOUTON COMMENCER
        # ==================================================

        self.startButton = QPushButton(
            "COMMENCER"
        )

        self.startButton.setMinimumHeight(
            70
        )

        self.startButton.setMinimumWidth(
            220
        )

        self.startButton.clicked.connect(
            self.start_measure
        )

        # ==================================================
        # BOUTON ARRETER
        # ==================================================

        self.stopButton = QPushButton(
            "ARRÊTER"
        )

        self.stopButton.setMinimumHeight(
            70
        )

        self.stopButton.setMinimumWidth(
            220
        )

        self.stopButton.setEnabled(
            False
        )

        self.stopButton.clicked.connect(
            self.stop_measure
        )

        # ==================================================
        # BOUTON SUIVANT
        # ==================================================

        self.nextButton = QPushButton(
            "SUIVANT"
        )

        self.nextButton.setMinimumHeight(
            70
        )

        self.nextButton.setMinimumWidth(
            220
        )

        self.nextButton.setEnabled(
            False
        )

        self.nextButton.clicked.connect(
            self.next_page
        )

        # ==================================================
        # LIGNE DES 3 BOUTONS
        # ==================================================

        buttons_layout = QHBoxLayout()

  

        # Centrage horizontal

        buttons_layout.addStretch()

        buttons_layout.addWidget(
            self.startButton
        )

        buttons_layout.addWidget(
            self.stopButton
        )

        buttons_layout.addWidget(
            self.nextButton
        )

        buttons_layout.addStretch()

        # Ajouter les boutons au layout principal

        layout.addLayout(
            buttons_layout
        )

        # ==================================================
        # PETIT ESPACE EN BAS
        # ==================================================

        #layout.addSpacing(10)

        self.setLayout(
            layout
        )

    # ==========================================================
    # DEMARRER LA MESURE
    # ==========================================================

    def start_measure(self):

        # --------------------------------------------------
        # Réinitialisation
        # --------------------------------------------------

        self.temperature = 0.0

        self.elapsed_time = 0

        self.measure_running = True

        self.temperatureLabel.setText(
            "--.- °C"
        )

        self.thermometer.setTemperature(
            35.0
        )

        self.statusLabel.setText(
            "Mesure en cours..."
        )

        self.infoLabel.setText(
            "Veuillez rester immobile devant le capteur."
        )

        # --------------------------------------------------
        # Boutons
        # --------------------------------------------------

        self.startButton.setEnabled(
            False
        )

        self.stopButton.setEnabled(
            True
        )

        self.nextButton.setEnabled(
            False
        )

        # --------------------------------------------------
        # CODE ARDUINO
        # --------------------------------------------------

        # TODO :
        #
        # Ici tu ajouteras ton code pour démarrer
        # le capteur de température.
        #
        # Exemple :
        #
        # self.serial.write(b"START_TEMP\n")
        #
        # --------------------------------------------------

        self.timer.start(
            500
        )

    # ==========================================================
    # VERIFICATION DE LA MESURE
    # ==========================================================

    def check_measurement(self):

        if not self.measure_running:

            return

        self.elapsed_time += 1

        # --------------------------------------------------
        # CODE DE LECTURE ARDUINO
        # --------------------------------------------------

        # TODO :
        #
        # Ici tu récupéreras la vraie température
        # envoyée par l'Arduino.
        #
        # Exemple :
        #
        # data = self.serial.readline()
        #
        # temperature = float(
        #     data.decode().strip()
        # )
        #
        # self.receive_temperature(temperature)
        #
        # --------------------------------------------------

        # --------------------------------------------------
        # SIMULATION TEMPORAIRE
        # --------------------------------------------------

        if self.elapsed_time == 6:

            self.receive_temperature(
                36.7
            )

        # --------------------------------------------------
        # TIMEOUT
        # --------------------------------------------------

        if self.elapsed_time >= 120:

            self.show_measure_error()

    # ==========================================================
    # TEMPERATURE RECUE
    # ==========================================================

    def receive_temperature(
        self,
        temperature
    ):

        # --------------------------------------------------
        # Vérification de la valeur
        # --------------------------------------------------

        if temperature < 30 or temperature > 45:

            self.show_measure_error()

            return

        # --------------------------------------------------
        # Arrêt du timer
        # --------------------------------------------------

        self.timer.stop()

        self.measure_running = False

        self.temperature = temperature

        # --------------------------------------------------
        # Affichage
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Sauvegarde patient
        # --------------------------------------------------

        if hasattr(
            self.main_window,
            "patient"
        ):

            self.main_window.patient.temperature = (
                temperature
            )

        # --------------------------------------------------
        # Boutons
        # --------------------------------------------------

        self.startButton.setEnabled(
            True
        )

        self.stopButton.setEnabled(
            False
        )

        self.nextButton.setEnabled(
            True
        )

    # ==========================================================
    # ARRETER LA MESURE
    # ==========================================================

    def stop_measure(self):

        self.timer.stop()

        self.measure_running = False

        self.statusLabel.setText(
            "Mesure arrêtée"
        )

        self.infoLabel.setText(
            "Vous pouvez recommencer la mesure."
        )

        self.startButton.setEnabled(
            True
        )

        self.stopButton.setEnabled(
            False
        )

        self.nextButton.setEnabled(
            False
        )

    # ==========================================================
    # ERREUR DE MESURE
    # ==========================================================

    def show_measure_error(self):

        self.timer.stop()

        self.measure_running = False

        self.statusLabel.setText(
            "Échec de la mesure"
        )

        self.infoLabel.setText(
            "Veuillez vous rapprocher du capteur "
            "et réessayer."
        )

        self.startButton.setEnabled(
            True
        )

        self.stopButton.setEnabled(
            False
        )

        self.nextButton.setEnabled(
            False
        )

        QMessageBox.warning(

            self,

            "Erreur de mesure",

            "La température n'a pas pu être mesurée.\n\n"

            "Veuillez :\n"
            "• rapprocher votre tête du capteur\n"
            "• rester immobile\n"
            "• vérifier le capteur\n"
            "• réessayer"

        )

    # ==========================================================
    # PAGE SUIVANTE
    # ==========================================================

    def next_page(self):

        # --------------------------------------------------
        # Sauvegarde finale
        # --------------------------------------------------

        if hasattr(
            self.main_window,
            "patient"
        ):

            self.main_window.patient.temperature = (
                self.temperature
            )

        print(
            "Température :",
            self.temperature
        )

        # --------------------------------------------------
        # Aller vers AVPU
        # --------------------------------------------------

        if hasattr(
            self.main_window,
            "go_to_consciousness"
        ):

            self.main_window.go_to_consciousness()

        else:

            print(
                "Erreur : "
                "go_to_consciousness() "
                "n'existe pas dans MainWindow."
            )

    # ==========================================================
    # RESET DE LA PAGE
    # ==========================================================

    def reset_page(self):

        self.timer.stop()

        self.measure_running = False

        self.temperature = 0.0

        self.elapsed_time = 0

        # --------------------------------------------------
        # Réinitialiser affichage
        # --------------------------------------------------

        self.temperatureLabel.setText(
            "--.- °C"
        )

        self.thermometer.setTemperature(
            35.0
        )

        self.statusLabel.setText(
            "Prêt pour la mesure"
        )

        self.infoLabel.setText(

            "Veuillez rapprocher votre tête du capteur.\n"
            "Cliquez sur COMMENCER pour démarrer la mesure."

        )

        # --------------------------------------------------
        # Réinitialiser boutons
        # --------------------------------------------------

        self.startButton.setEnabled(
            True
        )

        self.stopButton.setEnabled(
            False
        )

        self.nextButton.setEnabled(
            False
        )