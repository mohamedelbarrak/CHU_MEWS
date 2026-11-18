"""Page de mesure respiratoire MEWS pour Raspberry Pi + Sensirion SDP810 (I2C).

Prérequis sur le Raspberry Pi : PySide6, smbus2, I2C activé (/dev/i2c-1).
La validation du système complet sur matériel et des seuils reste indispensable.
"""

import math
import threading
import time

from PySide6.QtCore import Qt, QTimer, QRectF, QSize, QThread, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QStyle,
    QSizePolicy,
)

# Import facultatif ici : une erreur de dépendance est montrée dans la page,
# plutôt que de provoquer l'arrêt de toute l'application au chargement.
try:
    from smbus2 import SMBus, i2c_msg
    ERREUR_SMBUS = None
except ImportError as exc:
    SMBus = None
    i2c_msg = None
    ERREUR_SMBUS = str(exc)


# ==========================================
# CONFIGURATION MODIFIABLE
# ==========================================
DUREE_SECONDES = 60       # Durée réelle de mesure (mettre 20 pour des tests)
ALERTE_SANS_RESPIRATION_S = 10  # Alerte si 0 cycle détecté après 10 s (ou 5)
I2C_BUS = 1               # Raspberry Pi : normalement /dev/i2c-1
SDP810_ADRESSE = 0x25     # SDP810 : 0x25 (SDP811 : généralement 0x26)
SEUIL_PA = 0.5            # Seuil en pascals, à ajuster sur des mesures réelles
SENS_PRESSION = 1         # Mettre -1 si inspiration/expiration sont inversées

INTERVALLE_LECTURE_S = 0.040   # 40 ms : cadence ~25 Hz
CONFIRMATION_S = 0.120         # 120 ms
MIN_CYCLE_S = 1.0             # Au moins 1 s entre début d'inspiration et expiration
MAX_CYCLE_S = 10.0            # Reprise si expiration non trouvée en 10 s
CALIBRATION_ECHANTILLONS = 30
CALIBRATION_PAUSE_S = 0.020


# ==========================================
# LECTEUR SDP810 DIRECTEMENT EN I2C
# ==========================================
def crc8_sensirion(octets):
    """CRC-8 Sensirion : polynôme 0x31, valeur initiale 0xFF."""
    crc = 0xFF
    for octet in octets:
        crc ^= octet
        for _ in range(8):
            crc = ((crc << 1) ^ 0x31) & 0xFF if (crc & 0x80) else (crc << 1) & 0xFF
    return crc


class SDP810I2C:
    """Accès I²C natif au SDP8xx, sans Arduino et sans bibliothèque Arduino."""

    def __init__(self, bus_num=I2C_BUS, adresse=SDP810_ADRESSE):
        if SMBus is None:
            raise RuntimeError(
                "Le module 'smbus2' est absent. Installez-le sur le Raspberry Pi "
                f"(détail : {ERREUR_SMBUS})."
            )
        self.adresse = adresse
        self.bus = SMBus(bus_num)
        self.en_mesure = False

    def _commande(self, code):
        """Commande Sensirion sur 2 octets, sans octet de registre supplémentaire."""
        msg = i2c_msg.write(self.adresse, [(code >> 8) & 0xFF, code & 0xFF])
        self.bus.i2c_rdwr(msg)

    def commencer(self):
        # Reprendre la main si l'ancien programme a laissé le capteur en mesure.
        self._commande(0x3FF9)  # Stop continuous measurement
        time.sleep(0.002)
        self._commande(0x3615)  # DP compensée en température, moyenne jusqu'à lecture
        self.en_mesure = True
        time.sleep(0.025)       # Première mesure disponible après ~8 ms

    def lire_pression_pa(self):
        # Important : lecture I²C brute (pas de read_i2c_block_data qui
        # pourrait ajouter un octet de commande non attendu par le capteur).
        msg = i2c_msg.read(self.adresse, 9)
        self.bus.i2c_rdwr(msg)
        data = list(msg)

        for position in (0, 3, 6):
            if crc8_sensirion(data[position:position + 2]) != data[position + 2]:
                raise ValueError("CRC incorrect dans la réponse du SDP810.")

        pression_brute = int.from_bytes(bytes(data[0:2]), "big", signed=True)
        facteur = int.from_bytes(bytes(data[6:8]), "big", signed=False)
        if facteur == 0:
            raise ValueError("Facteur d'échelle SDP810 nul.")

        return pression_brute / facteur

    def fermer(self):
        try:
            if self.en_mesure:
                self._commande(0x3FF9)
                self.en_mesure = False
        finally:
            self.bus.close()


# ==========================================
# THREAD POUR ÉVITER DE BLOQUER PYSide6
# ==========================================
class MesureRespiratoireThread(QThread):
    mesure_demarre = Signal(float)  # Horodatage monotonic du début des 60 s
    respiration_detectee = Signal(int)  # Nombre de cycles, actualisé en direct
    aucune_respiration = Signal(int)    # Aucun cycle lors des premières secondes
    resultat = Signal(int)              # Nombre final de cycles complets
    erreur = Signal(str)

    def __init__(self, duree, parent=None):
        super().__init__(parent)
        self.duree = duree
        self.arret = threading.Event()

    def demander_arret(self):
        self.arret.set()

    def run(self):
        capteur = None
        try:
            capteur = SDP810I2C()
            capteur.commencer()

            # Étalonnage au repos, sans différence de pression sur les deux ports.
            valeurs = []
            for _ in range(CALIBRATION_ECHANTILLONS):
                if self.arret.is_set():
                    return
                valeurs.append(capteur.lire_pression_pa())
                if self.arret.wait(CALIBRATION_PAUSE_S):
                    return
            zero_pression = sum(valeurs) / len(valeurs)

            pression_filtree = 0.0
            etat = "ATTENTE_INSPIRATION"
            debut_confirmation = None
            debut_inspiration = 0.0
            nb_respirations = 0
            erreurs_consecutives = 0

            debut = time.monotonic()
            fin = debut + self.duree
            self.mesure_demarre.emit(debut)

            while not self.arret.is_set():
                maintenant = time.monotonic()
                if maintenant >= fin:
                    break

                # Une absence de cycle complet au début impose de revoir
                # le masque, le circuit et la détection avant de continuer.
                # Cela ne permet PAS de savoir à lui seul si le masque est porté.
                if (
                    nb_respirations == 0
                    and self.duree > ALERTE_SANS_RESPIRATION_S
                    and maintenant - debut >= ALERTE_SANS_RESPIRATION_S
                ):
                    self.aucune_respiration.emit(ALERTE_SANS_RESPIRATION_S)
                    return

                try:
                    pression = (
                        capteur.lire_pression_pa() - zero_pression
                    ) * SENS_PRESSION
                    erreurs_consecutives = 0
                except (OSError, ValueError) as exc:
                    erreurs_consecutives += 1
                    if erreurs_consecutives >= 3:
                        raise RuntimeError(
                            f"Lecture du SDP810 impossible : {exc}"
                        ) from exc
                    if self.arret.wait(INTERVALLE_LECTURE_S):
                        return
                    continue

                pression_filtree = 0.75 * pression_filtree + 0.25 * pression
                inspiration = pression_filtree < -SEUIL_PA
                expiration = pression_filtree > SEUIL_PA

                # Transposition du même automate que dans le code Arduino.
                if etat == "ATTENTE_INSPIRATION":
                    if inspiration:
                        if debut_confirmation is None:
                            debut_confirmation = maintenant
                        elif maintenant - debut_confirmation >= CONFIRMATION_S:
                            debut_inspiration = maintenant
                            etat = "ATTENTE_EXPIRATION"
                            debut_confirmation = None
                    else:
                        debut_confirmation = None
                else:
                    temps_cycle = maintenant - debut_inspiration
                    if temps_cycle > MAX_CYCLE_S:
                        etat = "ATTENTE_INSPIRATION"
                        debut_confirmation = None
                    elif expiration and temps_cycle >= MIN_CYCLE_S:
                        if debut_confirmation is None:
                            debut_confirmation = maintenant
                        elif maintenant - debut_confirmation >= CONFIRMATION_S:
                            nb_respirations += 1
                            self.respiration_detectee.emit(nb_respirations)
                            etat = "ATTENTE_INSPIRATION"
                            debut_confirmation = None
                    else:
                        debut_confirmation = None

                # Lecture toutes les ~40 ms, sans monopoliser le processeur.
                attente = min(INTERVALLE_LECTURE_S, max(0.0, fin - time.monotonic()))
                if self.arret.wait(attente):
                    return

            if not self.arret.is_set():
                self.resultat.emit(nb_respirations)
        except (OSError, RuntimeError, ValueError) as exc:
            if not self.arret.is_set():
                self.erreur.emit(str(exc))
        finally:
            if capteur is not None:
                try:
                    capteur.fermer()
                except OSError:
                    pass


# ==========================================
# WIDGET CERCLE - CHRONOMÈTRE
# ==========================================
class CircularTimer(QWidget):
    def __init__(self):
        super().__init__()
        self.maximum = DUREE_SECONDES
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
            size,
        )

        painter.setPen(QPen(QColor("#DCE3EA"), 12))
        painter.drawEllipse(rect)

        angle = 360 * self.value / self.maximum
        pen = QPen(QColor("#1976D2"), 12)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 90 * 16, -int(angle * 16))

        painter.setPen(QColor("#243B53"))
        painter.setFont(QFont("Arial", 35, QFont.Bold))
        painter.drawText(rect, Qt.AlignCenter, str(self.value))


# ==========================================
# PAGE RESPIRATION
# ==========================================
class RespirationPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("respirationPage")

        self.duration = DUREE_SECONDES
        self.remaining_time = self.duration
        self.nb_respirations = 0
        self.running = False
        self.mesure_valide = False
        self.debut_reel = None
        self.worker = None

        self.timer = QTimer(self)
        self.timer.setInterval(100)  # Horloge mise à jour finement ; affichage entier
        self.timer.timeout.connect(self.update_timer)

        self.setStyleSheet("""
            QWidget#respirationPage { background-color: #F4F7FA; }
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
            QLabel#countLabel {
                color: #145B9C;
                font-size: 30px;
                font-weight: bold;
            }
            QLabel#countTitle { color: #607D98; font-size: 15px; }
            QLabel#statusLabel { color: #607D98; font-size: 13px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 12)
        layout.setSpacing(7)

        # En-tête conservé
        header = QHBoxLayout()
        header.setSpacing(8)

        back_button = QPushButton()
        back_button.setObjectName("backButton")
        back_button.setFixedSize(44, 40)
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.setToolTip("Retour à l'identification")
        back_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft)
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

        # Instructions : plus aucun appui sur un bouton après chaque respiration.
        self.instruction = QLabel(
            "Portez bien votre masque. Le capteur compte automatiquement "
            "vos respirations. Respirez normalement pendant la mesure."
        )
        self.instruction.setAlignment(Qt.AlignCenter)
        self.instruction.setFont(QFont("Arial", 13))
        self.instruction.setWordWrap(True)
        self.instruction.setFixedHeight(52)

        self.duration_label = QLabel(
            f"Durée du comptage : {self.duration} secondes"
        )
        self.duration_label.setAlignment(Qt.AlignCenter)
        self.duration_label.setFont(QFont("Arial", 12))
        self.duration_label.setStyleSheet("color: #607D98;")
        self.duration_label.setFixedHeight(24)

        self.circular = CircularTimer()
        self.circular.maximum = self.duration
        self.circular.setValue(self.duration)

        count_container = QVBoxLayout()
        count_container.setSpacing(5)
        count_title = QLabel("RESPIRATIONS")
        count_title.setObjectName("countTitle")
        count_title.setAlignment(Qt.AlignCenter)

        # Le nombre de cycles s'actualise en direct (sans bouton manuel).
        self.countLabel = QLabel("0")
        self.countLabel.setObjectName("countLabel")
        self.countLabel.setAlignment(Qt.AlignCenter)
        count_container.addWidget(count_title)
        count_container.addWidget(self.countLabel)

        measurement_layout = QHBoxLayout()
        measurement_layout.setSpacing(35)
        measurement_layout.addStretch(1)
        measurement_layout.addWidget(self.circular)
        measurement_layout.addLayout(count_container)
        measurement_layout.addStretch(1)

        # Zone de statut : initialisation / mesure / résultat / erreur.
        self.statusLabel = QLabel(
            "Portez bien votre masque, puis appuyez sur COMMENCER."
        )
        self.statusLabel.setObjectName("statusLabel")
        self.statusLabel.setAlignment(Qt.AlignCenter)
        self.statusLabel.setWordWrap(True)
        self.statusLabel.setMinimumHeight(52)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        self.startButton = QPushButton("COMMENCER")
        self.startButton.setObjectName("startButton")
        self.startButton.setFixedHeight(55)
        self.startButton.setCursor(Qt.PointingHandCursor)
        self.startButton.clicked.connect(self.start_measure)

        self.nextButton = QPushButton("SUIVANT")
        self.nextButton.setObjectName("nextButton")
        self.nextButton.setFixedHeight(55)
        self.nextButton.setEnabled(False)
        self.nextButton.setCursor(Qt.PointingHandCursor)
        self.nextButton.clicked.connect(self.next_page)

        for button in (self.startButton, self.nextButton):
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            buttons_layout.addWidget(button, 1)

        layout.addLayout(header)
        layout.addWidget(self.instruction)
        layout.addWidget(self.duration_label)
        layout.addStretch(1)
        layout.addLayout(measurement_layout)
        layout.addWidget(self.statusLabel)
        layout.addStretch(1)
        layout.addLayout(buttons_layout)

    # ===================================
    # GESTION DU CAPTEUR ET DES ÉVÉNEMENTS
    # ===================================
    def _stop_worker(self):
        if self.worker is not None:
            self.worker.demander_arret()
            # Lectures I²C très courtes ; on attend l'arrêt avant de libérer la page.
            self.worker.wait()
            self.worker = None

    def start_measure(self):
        self.reset_page()
        # Ne pas enregistrer une ancienne fréquence si une nouvelle mesure échoue.
        self.main_window.patient.frequence_respiratoire = None

        self.startButton.setText("COMMENCER")
        self.startButton.setEnabled(False)
        self.nextButton.setEnabled(False)
        self._set_status(
            "Initialisation et étalonnage du capteur… "
            "Ne créez pas de différence de pression pendant cette étape."
        )

        thread = MesureRespiratoireThread(self.duration, self)
        self.worker = thread
        thread.mesure_demarre.connect(
            lambda debut, t=thread: self.on_measure_started(t, debut)
        )
        thread.respiration_detectee.connect(
            lambda cycles, t=thread: self.on_respiration_detected(t, cycles)
        )
        thread.aucune_respiration.connect(
            lambda secondes, t=thread: self.on_no_breath_detected(t, secondes)
        )
        thread.resultat.connect(
            lambda cycles, t=thread: self.on_measure_finished(t, cycles)
        )
        thread.erreur.connect(
            lambda message, t=thread: self.on_measure_error(t, message)
        )
        thread.start()

    def on_measure_started(self, thread, debut):
        if self.worker is not thread:
            return
        self.running = True
        self.debut_reel = debut
        self._set_status(
            "Mesure en cours : respirez normalement, "
            "le compteur s'actualise automatiquement."
        )
        self.timer.start()
        self.update_timer()

    def update_timer(self):
        if not self.running or self.debut_reel is None:
            return
        ecoule = time.monotonic() - self.debut_reel
        self.remaining_time = max(0, math.ceil(self.duration - ecoule))
        self.circular.setValue(self.remaining_time)
        # Seul le worker valide le résultat à la fin effective des 60 secondes.

    def on_respiration_detected(self, thread, cycles):
        """Signal émis par le capteur pour chaque inspiration/expiration complète."""
        if self.worker is not thread or not self.running:
            return
        self.nb_respirations = cycles
        self.countLabel.setText(str(cycles))

    def on_no_breath_detected(self, thread, secondes):
        """Interrompt la mesure si aucun cycle n'a été détecté au début."""
        if self.worker is not thread or not self.running:
            return
        self.timer.stop()
        self.running = False
        self.mesure_valide = False
        self.main_window.patient.frequence_respiratoire = None
        self.nextButton.setEnabled(False)
        self.startButton.setText("RECOMMENCER")
        self.startButton.setEnabled(True)
        self._set_status(
            f"ALERTE : aucune respiration détectée après {secondes} s. "
            "Portez bien votre masque, vérifiez les tuyaux, puis "
            "appuyez sur RECOMMENCER. Si le patient semble ne pas "
            "respirer, alertez immédiatement un soignant.",
            alerte=True,
        )
        self._stop_worker()

    def on_measure_finished(self, thread, cycles):
        if self.worker is not thread:
            return
        self.timer.stop()
        self.running = False
        self.remaining_time = 0
        self.circular.setValue(0)
        self.nb_respirations = cycles
        self.countLabel.setText(str(cycles))  # Conserver la valeur affichée en direct

        if cycles == 0:
            self.mesure_valide = False
            self._set_status(
                "Aucun cycle détecté : mesure non interprétable. "
                "Vérifiez le masque, les tuyaux et l'état du patient.",
                alerte=True,
            )
            self.nextButton.setEnabled(False)
            self.main_window.patient.frequence_respiratoire = None
        else:
            # Comptage = fréquence en resp/min pour 60 s.
            frequence = cycles * 60.0 / self.duration
            self.main_window.patient.frequence_respiratoire = round(frequence)
            self.mesure_valide = True
            # Le compteur conserve sa valeur. Seule la fréquence apparaît ici.
            self._set_status(
                f"Mesure terminée. Fréquence respiratoire : "
                f"{frequence:.1f} resp/min."
            )
            self.nextButton.setEnabled(True)
            print(
                "Fréquence respiratoire enregistrée :",
                self.main_window.patient.frequence_respiratoire,
                "resp/min"
            )

        self.startButton.setEnabled(True)

    def on_measure_error(self, thread, message):
        if self.worker is not thread:
            return
        self.timer.stop()
        self.running = False
        self.mesure_valide = False
        self.main_window.patient.frequence_respiratoire = None
        self.nextButton.setEnabled(False)
        self.startButton.setEnabled(True)
        self.countLabel.setText("—")
        self.startButton.setText("RECOMMENCER")
        self._set_status(f"Erreur du capteur : {message}", alerte=True)
        print("ERREUR SDP810 :", message)

    def next_page(self):
        if self.running or not self.mesure_valide:
            return
        self._stop_worker()
        self.main_window.go_to_blood_pressure()

    def go_back(self):
        self.reset_page()
        self.main_window.go_to_ppm()

    def _set_status(self, message, alerte=False):
        self.statusLabel.setText(message)
        if alerte:
            self.statusLabel.setStyleSheet(
                "color: #B42318; font-size: 13px; font-weight: bold; "
                "background-color: #FEE4E2; border-radius: 8px; padding: 5px;"
            )
        else:
            self.statusLabel.setStyleSheet(
                "color: #607D98; font-size: 13px; background: transparent;"
            )

    def reset_page(self):
        self.timer.stop()
        self._stop_worker()
        self.running = False
        self.mesure_valide = False
        self.debut_reel = None
        self.remaining_time = self.duration
        self.nb_respirations = 0
        self.circular.setValue(self.duration)
        self.countLabel.setText("0")
        self._set_status(
            "Portez bien votre masque, puis appuyez sur COMMENCER. "
            "Le nombre de respirations s'affichera en temps réel."
        )
        self.startButton.setText("COMMENCER")
        self.startButton.setEnabled(True)
        self.nextButton.setEnabled(False)

    def closeEvent(self, event):
        self.timer.stop()
        self._stop_worker()
        super().closeEvent(event)
