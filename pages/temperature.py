import time
import serial
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QPainter, QColor
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QStyle,
    QSizePolicy,
)


# ==========================================================
# WIDGET THERMOMETRE
# ==========================================================

class ThermometerWidget(QWidget):

    def __init__(self):

        super().__init__()

        self.temperature = 0.0

        # Thermomètre plus grand
        self.setMinimumSize(140, 135)
        self.setMaximumHeight(170)

    def setTemperature(self, temperature):

        self.temperature = temperature

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        # ==================================================
        # POSITION DU THERMOMETRE
        # ==================================================

        painter.scale(self.width() / 220, self.height() / 500)
        center_x = 110

        bottom_y = 395

        top_y = 35

        tube_width = 40

        bulb_radius = 50

        # ==================================================
        # TUBE GRIS
        # ==================================================

        painter.setPen(Qt.NoPen)

        painter.setBrush(
            QColor(220, 220, 220)
        )

        painter.drawRoundedRect(
            center_x - tube_width // 2,
            top_y,
            tube_width,
            bottom_y - top_y,
            tube_width // 2,
            tube_width // 2
        )

        # ==================================================
        # BULBE GRIS
        # ==================================================

        painter.drawEllipse(
            center_x - bulb_radius,
            bottom_y - 15,
            bulb_radius * 2,
            bulb_radius * 2
        )

        # ==================================================
        # LIMITES TEMPERATURE
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
        # HAUTEUR DU LIQUIDE
        # ==================================================

        liquid_height = int(
            percentage *
            (bottom_y - top_y - 20)
        )

        liquid_top = (
            bottom_y - 10 - liquid_height
        )

        # ==================================================
        # LIQUIDE BLEU
        # ==================================================

        painter.setBrush(
            QColor("#1976D2")
        )

        painter.drawRoundedRect(
            center_x - 12,
            liquid_top,
            24,
            liquid_height,
            12,
            12
        )

        # ==================================================
        # BULBE BLEU
        # ==================================================

        painter.drawEllipse(
            center_x - bulb_radius + 8,
            bottom_y - 7,
            (bulb_radius - 8) * 2,
            (bulb_radius - 8) * 2
        )

        # Le thermomètre reste uniquement graphique.
        # La valeur numérique est affichée par temperatureLabel après la mesure.


# ==========================================================
# PAGE TEMPERATURE
# ==========================================================

class TemperaturePage(QWidget):

    def __init__(self, main_window):

        super().__init__()

        self.main_window = main_window
        self.setObjectName("temperaturePage")

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
            QWidget#temperaturePage { background-color: #F4F7FA; }
            QLabel { color: #243B53; background: transparent; }
            QPushButton {
                border: none;
                border-radius: 8px;
                font-size: 17px;
                font-weight: bold;
            }
            QPushButton#backButton, QPushButton#startButton {
                background-color: #DCEEFE;
                color: #145B9C;
                border: 1px solid #A5CBF0;
            }
            QPushButton#backButton:hover, QPushButton#startButton:hover {
                background-color: #BDDDF9;
            }
            QPushButton#nextButton {
                background-color: #D8F4E5;
                color: #176C43;
            }
            QPushButton#nextButton:pressed { background-color: #A9E6C4; }
            QPushButton:disabled {
                background-color: #E2E5E9;
                color: #9BA3AD;
                border: 1px solid #D7DCE1;
            }
            QPushButton#stopButton {
                background-color: #FEE4E2;
                color: #B42318;
                border: 1px solid #F4B4AF;
            }
            QPushButton#stopButton:hover { background-color: #FBCBC7; }
            QPushButton#backButton:disabled, QPushButton#startButton:disabled,
            QPushButton#stopButton:disabled, QPushButton#nextButton:disabled {
                background-color: #E2E5E9;
                color: #9BA3AD;
                border: 1px solid #D7DCE1;
            }
        """)

        # ==================================================
        # LAYOUT PRINCIPAL
        # ==================================================

        layout = QVBoxLayout(self)

        layout.setContentsMargins(16, 8, 16, 12)
        layout.setSpacing(5)

        # En-tête identique à la page respiration
        header = QHBoxLayout()
        header.setSpacing(8)

        self.backButton = QPushButton()
        self.backButton.setObjectName("backButton")
        self.backButton.setFixedSize(44, 40)
        self.backButton.setCursor(Qt.PointingHandCursor)
        self.backButton.setToolTip("Retour à la tension artérielle")
        self.backButton.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft)
        )
        self.backButton.setIconSize(QSize(24, 24))
        self.backButton.clicked.connect(self.go_back)

        self.titleLabel = QLabel("Mesure de la température")
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setFont(QFont("Arial", 21, QFont.Bold))
        self.titleLabel.setFixedHeight(40)

        right_space = QWidget()
        right_space.setFixedWidth(44)
        header.addWidget(self.backButton)
        header.addWidget(self.titleLabel, 1)
        header.addWidget(right_space)
        layout.addLayout(header)

        # ==================================================
        # ESPACE
        # ==================================================

        layout.addSpacing(2)

        # ==================================================
        # INSTRUCTIONS
        # ==================================================

        self.infoLabel = QLabel(

            "Veuillez rapprocher votre tête du capteur.\n"
            "Cliquez sur COMMENCER, puis approchez votre front."

        )

        self.infoLabel.setAlignment(
            Qt.AlignCenter
        )
        self.infoLabel.setWordWrap(True)

        self.infoLabel.setFont(
            QFont(
                "Arial",
                15,
                QFont.Bold
            )
        )

        layout.addWidget(
            self.infoLabel
        )

        # ==================================================
        # ESPACE
        # ==================================================

        layout.addSpacing(2)

        # ==================================================
        # THERMOMETRE
        # ==================================================

        self.thermometer = ThermometerWidget()

        layout.addWidget(
            self.thermometer,
            alignment=Qt.AlignCenter
        )

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
                24,
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
        self.statusLabel.setWordWrap(True)

        self.statusLabel.setFont(
            QFont(
                "Arial",
                18,
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

        # Boutons : même forme et mêmes dimensions que la page respiration.
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        self.startButton = QPushButton("COMMENCER")
        self.startButton.setObjectName("startButton")
        self.startButton.clicked.connect(self.start_measure)

        self.stopButton = QPushButton("ARRÊTER")
        self.stopButton.setObjectName("stopButton")
        self.stopButton.setEnabled(False)
        self.stopButton.clicked.connect(self.stop_measure)

        self.nextButton = QPushButton("SUIVANT")
        self.nextButton.setObjectName("nextButton")
        self.nextButton.setEnabled(False)
        self.nextButton.clicked.connect(self.next_page)

        for button in (self.startButton, self.stopButton, self.nextButton):
            button.setFixedHeight(55)
            button.setCursor(Qt.PointingHandCursor)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            buttons_layout.addWidget(button, 1)

        layout.addLayout(buttons_layout)

    # ==========================================================
    # DEMARRER LA MESURE
    # ==========================================================

    # Configuration matérielle Raspberry Pi 4
    PORT_DISTANCE = "/dev/ttyAMA3"
    PORT_TEMPERATURE = "/dev/ttyAMA0"
    BAUD = 9600
    SEUIL_MM = 20          # Déclenchement : distance <= 20 mm
    SEUIL_SORTIE_MM = 25   # Tolérance après déclenchement
    NB_MESURES = 1
    TIMEOUT = 60.0        # Attente du front
    TIMEOUT_ACQUISITION = 15.0
    AGE_DISTANCE_MAX = 0.8
    DEBUG = True
    COMMANDE = bytes.fromhex("01 03 00 10 00 01 85 CF")
    ENTETE = bytes.fromhex("A4 03 07 07")

    def close_ports(self):
        self.timer.stop()
        for nom in ("tof", "temp_port"):
            port = getattr(self, nom, None)
            if port is not None:
                try:
                    port.close()
                except (OSError, serial.SerialException):
                    pass
                setattr(self, nom, None)

    def start_measure(self):
        self.close_ports()
        self.temperature = 0.0
        self.measure_running = True
        self.temperatureLabel.setText("--.- °C")
        self.thermometer.setTemperature(35.0)
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.nextButton.setEnabled(False)
        self.infoLabel.setText(f"Rapprochez votre front à {self.SEUIL_MM / 10:g} cm ou moins.")
        self.statusLabel.setText("Recherche du front...")
        self.tof = self.temp_port = None
        self.rx_tof = bytearray()
        self.rx_temp = bytearray()
        self.proche = False
        self.distance = None
        self.debut = time.monotonic()
        self.derniere_distance = 0.0
        self.envoi = 0.0
        self.attente_tof = False
        self.debut_proximite = 0.0
        self.dernier_log = 0.0
        self.nb_distances = 0
        self.nb_trames_temp = 0
        self.nb_crc_tof = 0
        self.nb_crc_temp = 0
        self.nb_octets_temp = 0
        self.nb_timeout_tof = 0
        self.derniere_temperature = None
        self.derniere_distance_brute = None
        self.min_distance = None
        self.dernier_hex_tof = ""
        self.dernier_hex_temp = ""
        self.nb_declenchements = 0
        self.nb_interruptions = 0
        try:
            # Le module de température émet automatiquement : ouvrir une seule
            # fois, lire en continu, mais ne retenir que la première
            # trame complète reçue après détection du front.
            self.tof = serial.Serial(self.PORT_DISTANCE, self.BAUD,
                                     timeout=0, write_timeout=0.1, exclusive=True)
            self.temp_port = serial.Serial(self.PORT_TEMPERATURE, self.BAUD,
                                           timeout=0, exclusive=True)
            self.tof.reset_input_buffer()
            self.temp_port.reset_input_buffer()
            self.timer.start(40)
        except (OSError, serial.SerialException) as exc:
            self.show_measure_error(str(exc))

    @staticmethod
    def crc16(data):
        crc = 0xFFFF
        for octet in data:
            crc ^= octet
            for _ in range(8):
                crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
        return crc

    def lire_distance(self, maintenant):
        donnees = self.tof.read(self.tof.in_waiting)
        if donnees:
            self.dernier_hex_tof = donnees[-24:].hex(" ")
            self.rx_tof.extend(donnees)
        while len(self.rx_tof) >= 7:
            if self.rx_tof[:3] != b"\x01\x03\x02":
                del self.rx_tof[0]
                continue
            trame = bytes(self.rx_tof[:7])
            if self.crc16(trame[:5]) != int.from_bytes(trame[5:7], "little"):
                self.nb_crc_tof += 1
                del self.rx_tof[0]
                continue
            del self.rx_tof[:7]
            if not self.attente_tof:
                continue
            self.attente_tof = False
            d = int.from_bytes(trame[3:5], "big")
            self.derniere_distance_brute = d
            self.nb_distances += 1
            self.distance = d if 0 < d <= 2000 else None
            self.derniere_distance = maintenant
            if self.distance is not None:
                self.min_distance = d if self.min_distance is None else min(self.min_distance, d)
        if self.attente_tof and maintenant - self.envoi >= 0.35:
            self.attente_tof = False
            self.nb_timeout_tof += 1
        if not self.attente_tof and maintenant - self.envoi >= 0.20:
            self.tof.reset_input_buffer()
            self.rx_tof.clear()
            self.tof.write(self.COMMANDE)
            self.envoi = maintenant
            self.attente_tof = True

    def lire_temperatures(self):
        donnees = self.temp_port.read(self.temp_port.in_waiting)
        if donnees:
            self.nb_octets_temp += len(donnees)
            self.dernier_hex_temp = donnees[-24:].hex(" ")
            self.rx_temp.extend(donnees)
        while True:
            debut = self.rx_temp.find(self.ENTETE)
            if debut < 0:
                del self.rx_temp[:-3]
                return
            del self.rx_temp[:debut]
            if len(self.rx_temp) < 12:
                return
            trame = bytes(self.rx_temp[:12])
            if sum(trame[:11]) & 0xFF != trame[11]:
                self.nb_crc_temp += 1
                del self.rx_temp[0]
                continue
            del self.rx_temp[:12]
            objet = int.from_bytes(trame[5:7], "big", signed=True) / 100.0
            ambiante = int.from_bytes(trame[7:9], "big", signed=True) / 100.0
            corps = int.from_bytes(trame[9:11], "big", signed=True) / 100.0
            self.nb_trames_temp += 1
            self.derniere_temperature = (objet, ambiante, corps)
            yield corps

    def annuler_acquisition(self):
        if self.proche:
            self.nb_interruptions += 1
        self.proche = False

    def diagnostic(self):
        d = self.derniere_distance_brute
        minimum = self.min_distance
        t = self.derniere_temperature
        return (f"Distance brute : {d if d is not None else '--'} mm ; "
                f"minimum : {minimum if minimum is not None else '--'} mm\n"
                f"TOF : {self.nb_distances} réponses, {self.nb_timeout_tof} délais, "
                f"{self.nb_crc_tof} CRC invalides\n"
                f"Température : {self.nb_octets_temp} octets, {self.nb_trames_temp} trames valides, "
                f"{self.nb_crc_temp} checksums invalides\n"
                f"Dernière estimation : {t[2] if t else '--'} °C ; "
                f"déclenchements : {self.nb_declenchements}, interruptions : {self.nb_interruptions}")

    def journal(self, maintenant):
        if self.DEBUG and maintenant - self.dernier_log >= 1.0:
            self.dernier_log = maintenant
            print("[TEMP] " + self.diagnostic().replace("\n", " | ") +
                  f" | HEX TOF : {self.dernier_hex_tof} | HEX TEMP : {self.dernier_hex_temp}", flush=True)

    def check_measurement(self):
        if not self.measure_running:
            return

        maintenant = time.monotonic()
        try:
            self.lire_distance(maintenant)
            frais = (self.distance is not None and
                     maintenant - self.derniere_distance <= self.AGE_DISTANCE_MAX)
            distance_texte = (f"{self.distance / 10:.1f} cm" if frais else "indisponible")
            limite = self.SEUIL_SORTIE_MM if self.proche else self.SEUIL_MM
            valide = frais and self.distance <= limite

            if not valide:
                self.annuler_acquisition()
                # Lire les trames pour le diagnostic, mais ne pas les utiliser.
                list(self.lire_temperatures())
                self.statusLabel.setText(f"Distance : {distance_texte}")
                self.infoLabel.setText(f"Rapprochez votre front à {self.SEUIL_MM / 10:g} cm ou moins.")
                self.journal(maintenant)
                if maintenant - self.debut >= self.TIMEOUT:
                    self.show_measure_error("Front non détecté ou position instable.\n" + self.diagnostic())
                return

            if not self.proche:
                # Purger UNE SEULE FOIS les anciennes données. Le module
                # GY-614V3DCC envoie ses trames automatiquement à 9600 bauds.
                self.temp_port.reset_input_buffer()
                self.rx_temp.clear()
                self.proche = True
                self.nb_declenchements += 1
                self.debut_proximite = maintenant
                self.infoLabel.setText("Front détecté. Restez immobile.")
                self.statusLabel.setText(f"Distance : {distance_texte} | Attente température...")
                print(f"[TEMP] Front détecté à {self.distance} mm : attente d'une nouvelle trame", flush=True)
                return

            # Ne jamais effacer le tampon ici : une trame de 12 octets
            # peut arriver en plusieurs lectures successives.
            for valeur in self.lire_temperatures():
                objet, ambiante, corps = self.derniere_temperature
                print(f"[TEMP] Trame valide : objet={objet:.2f} °C | "
                      f"ambiante={ambiante:.2f} °C | corps={corps:.2f} °C", flush=True)
                # Une seule trame suffit pour ce test. Si la valeur est
                # hors plage, l'afficher en diagnostic sans la sauvegarder.
                if not 30 <= valeur <= 45:
                    self.show_measure_error(
                        f"Trame reçue : corps={corps:.2f} °C, objet={objet:.2f} °C, "
                        f"ambiante={ambiante:.2f} °C.\n"
                        "Estimation corporelle hors plage du prototype (30–45 °C).\n"
                        "Aucune valeur enregistrée.")
                    return
                self.receive_temperature(valeur)
                return

            self.journal(maintenant)
            self.statusLabel.setText(f"Distance : {distance_texte} | Attente température...")
            self.infoLabel.setText("Front détecté. Attente d'une trame UART valide.")
            if maintenant - self.debut_proximite >= self.TIMEOUT_ACQUISITION:
                self.show_measure_error("Aucune nouvelle trame de température valide.\n" + self.diagnostic())
            elif maintenant - self.debut >= self.TIMEOUT:
                self.show_measure_error("Délai total de mesure dépassé.\n" + self.diagnostic())
        except (OSError, serial.SerialException) as exc:
            self.show_measure_error(str(exc))

    def hideEvent(self, event):
        if self.measure_running:
            self.stop_measure()
        super().hideEvent(event)

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

        self.close_ports()

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
            "Température corporelle estimée (prototype)."
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

        self.close_ports()

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

    def show_measure_error(self, detail=""):

        self.close_ports()

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

        print("[TEMP] ERREUR :", detail, flush=True)
        QMessageBox.warning(

            self,

            "Erreur de mesure",

            "La température n'a pas pu être mesurée.\n\n" + detail + "\n\n" +

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

        if self.measure_running or not self.nextButton.isEnabled():
            return

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

    def go_back(self):
        # Arrêter la mesure et fermer les UART avant de quitter la page.
        self.reset_page()
        self.main_window.go_to_blood_pressure()

    def reset_page(self):

        self.close_ports()

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
            "Cliquez sur COMMENCER, puis approchez votre front."

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