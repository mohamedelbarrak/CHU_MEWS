
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QProgressBar,
    QMessageBox,
    QFrame,
    QSizePolicy,
    QStyle
)


class BloodPressurePage(QWidget):

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
        self.setObjectName("bloodPressurePage")

        self.measure_running = False
        self.timeout = 0
        self.progress = 0
        self.heart_state = False

        # ===================================
        # TIMERS
        # ===================================

        # Timer de progression / simulation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_timeout)

        # Timer indépendant pour l'animation du cœur
        self.heartTimer = QTimer(self)
        self.heartTimer.timeout.connect(
            self.animate_heart
        )

        # Durée entre deux changements du cœur
        # 500 ms = 0,5 seconde
        self.heart_interval = 500

        # ===================================
        # STYLE
        # ===================================
        self.setStyleSheet("""
            QWidget#bloodPressurePage {
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
                border-radius: 10px;
            }

            QLabel#resultTitle {
                color: #607D98;
                font-size: 13px;
                font-weight: bold;
            }

            QLabel#resultValue {
                color: #145B9C;
                font-size: 23px;
                font-weight: bold;
            }

            QLabel#resultUnit {
                color: #607D98;
                font-size: 12px;
            }

            QProgressBar {
                border: none;
                border-radius: 7px;
                background-color: #DCE3EA;
                color: #243B53;
                text-align: center;
                font-size: 11px;
                font-weight: bold;
            }

            QProgressBar::chunk {
                background-color: #1976D2;
                border-radius: 7px;
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
            "Retour à la fréquence respiratoire"
        )
        back_button.clicked.connect(self.go_back)

        title = QLabel("Pression artérielle")
        title.setFont(QFont("Arial", 21, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setFixedHeight(40)

        right_space = QWidget()
        right_space.setFixedWidth(44)

        header.addWidget(back_button)
        header.addWidget(title, 1)
        header.addWidget(right_space)

        # ===================================
        # INSTRUCTION
        # ===================================
        instruction = QLabel(
            "Placez correctement le brassard, "
            "puis appuyez sur COMMENCER."
        )
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setFont(QFont("Arial", 12))
        instruction.setWordWrap(True)
        instruction.setFixedHeight(32)

        # ===================================
        # COEUR + STATUT
        # ===================================
        measure_layout = QHBoxLayout()
        measure_layout.setSpacing(18)

        self.animationLabel = QLabel("❤️")
        self.animationLabel.setAlignment(Qt.AlignCenter)
        self.animationLabel.setFont(QFont("Arial", 46))
        self.animationLabel.setFixedSize(100, 90)

        status_container = QVBoxLayout()
        status_container.setSpacing(8)

        self.statusLabel = QLabel("Prêt pour la mesure")
        self.statusLabel.setAlignment(Qt.AlignCenter)
        self.statusLabel.setFont(
            QFont("Arial", 17, QFont.Bold)
        )
        self.statusLabel.setFixedHeight(32)

        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setFixedHeight(20)

        status_container.addWidget(self.statusLabel)
        status_container.addWidget(self.progressBar)

        measure_layout.addStretch(1)
        measure_layout.addWidget(self.animationLabel)
        measure_layout.addLayout(status_container, 2)
        measure_layout.addStretch(1)

        # ===================================
        # CARTE PRESSION ARTERIELLE
        # ===================================
        pressure_card = QFrame()
        pressure_card.setObjectName("resultCard")

        pressure_layout = QVBoxLayout(pressure_card)
        pressure_layout.setContentsMargins(10, 10, 10, 10)
        pressure_layout.setSpacing(4)

        pressure_title = QLabel("PRESSION ARTÉRIELLE")
        pressure_title.setObjectName("resultTitle")
        pressure_title.setAlignment(Qt.AlignCenter)

        self.pressureLabel = QLabel("-- / --")
        self.pressureLabel.setObjectName("resultValue")
        self.pressureLabel.setAlignment(Qt.AlignCenter)

        pressure_unit = QLabel("mmHg")
        pressure_unit.setObjectName("resultUnit")
        pressure_unit.setAlignment(Qt.AlignCenter)

        pressure_layout.addWidget(pressure_title)
        pressure_layout.addWidget(self.pressureLabel)
        pressure_layout.addWidget(pressure_unit)

        # ===================================
        # CARTE FREQUENCE CARDIAQUE
        # ===================================
        heart_card = QFrame()
        heart_card.setObjectName("resultCard")

        heart_layout = QVBoxLayout(heart_card)
        heart_layout.setContentsMargins(10, 10, 10, 10)
        heart_layout.setSpacing(4)

        heart_title = QLabel("FRÉQUENCE CARDIAQUE")
        heart_title.setObjectName("resultTitle")
        heart_title.setAlignment(Qt.AlignCenter)

        self.heartRateLabel = QLabel("--")
        self.heartRateLabel.setObjectName("resultValue")
        self.heartRateLabel.setAlignment(Qt.AlignCenter)

        heart_unit = QLabel("BPM")
        heart_unit.setObjectName("resultUnit")
        heart_unit.setAlignment(Qt.AlignCenter)

        heart_layout.addWidget(heart_title)
        heart_layout.addWidget(self.heartRateLabel)
        heart_layout.addWidget(heart_unit)

        # ===================================
        # RESULTATS COTE A COTE
        # ===================================
        results_layout = QHBoxLayout()
        results_layout.setSpacing(12)

        results_layout.addWidget(pressure_card, 1)
        results_layout.addWidget(heart_card, 1)

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
        layout.addWidget(instruction)

        layout.addSpacing(8)

        layout.addLayout(measure_layout)

        layout.addSpacing(8)

        layout.addLayout(results_layout)

        layout.addStretch(1)

        layout.addLayout(buttons_layout)

    # ===================================
    # RETOUR A LA PAGE RESPIRATION
    # ===================================
    def go_back(self):

        # Arrêter les timers
        self.reset_page()

        # Page précédente
        self.main_window.go_to_respiration()

    # ===================================
    # REINITIALISATION
    # ===================================
    def reset_page(self):
        self.measure_running = False
        self.timeout = 0
        self.progress = 0
        self.heart_state = False

        self.timer.stop()
        self.heartTimer.stop()

        self.progressBar.setValue(0)
        self.animationLabel.setText("❤️")
        self.statusLabel.setText("Prêt pour la mesure")

        self.pressureLabel.setText("-- / --")
        self.heartRateLabel.setText("--")

        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.nextButton.setEnabled(False)

    # ===================================
    # COMMENCER LA MESURE
    # ===================================
    def start_measure(self):
        self.reset_page()

        self.measure_running = True
        self.statusLabel.setText("Mesure en cours...")

        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)

        # TODO :
        # Démarrer la communication Arduino
        # avec le tensiomètre réel.

        # Timer de progression / simulation
        self.timer.start(50)

        # Animation du cœur plus lente
        self.heartTimer.start(self.heart_interval)

    # ===================================
    # ANIMATION DU COEUR
    # ===================================
    def animate_heart(self):

        if not self.measure_running:
            return

        self.heart_state = not self.heart_state

        if self.heart_state:
            self.animationLabel.setText("🫀")
        else:
            self.animationLabel.setText("❤️")

    # ===================================
    # ARRETER LA MESURE
    # ===================================
    def stop_measure(self):
        self.timer.stop()
        self.heartTimer.stop()

        self.measure_running = False
        self.statusLabel.setText("Mesure arrêtée")

        self.animationLabel.setText("❤️")

        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.nextButton.setEnabled(False)

        # TODO :
        # Envoyer la commande d'arrêt
        # au tensiomètre si nécessaire.

    # ===================================
    # TIMER / PROGRESSION
    # ===================================
    def check_timeout(self):

        if not self.measure_running:
            return

        self.timeout += 1

        self.progress = min(
            100,
            self.progress + 1
        )

        self.progressBar.setValue(self.progress)

        # TODO :
        # Lire les données provenant de l'Arduino.
        # Dès réception, appeler :
        # self.receive_measure(systolique, diastolique, bpm)

        # Simulation actuelle
        if self.timeout == 20:
            self.receive_measure(118, 76, 72)
            return

        if self.timeout >= 120:
            self.show_measure_error()

    # ===================================
    # RECEPTION DES RESULTATS
    # ===================================
    def receive_measure(
        self,
        systolique,
        diastolique,
        bpm
    ):

        if not self.measure_running:
            return

        self.timer.stop()
        self.heartTimer.stop()

        self.measure_running = False

        # Sauvegarde dans Patient
        if hasattr(self.main_window, "patient"):
            patient = self.main_window.patient

            patient.pression_systolique = systolique
            patient.pression_diastolique = diastolique
            patient.frequence_cardiaque = bpm

        # Affichage des résultats
        self.pressureLabel.setText(
            f"{systolique} / {diastolique}"
        )

        self.heartRateLabel.setText(str(bpm))

        self.statusLabel.setText("Mesure terminée")
        self.progressBar.setValue(100)
        self.animationLabel.setText("❤️")

        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.nextButton.setEnabled(True)

    # ===================================
    # ERREUR DE MESURE
    # ===================================
    def show_measure_error(self):
        self.timer.stop()
        self.heartTimer.stop()

        self.measure_running = False

        self.statusLabel.setText("Échec de la mesure")
        self.animationLabel.setText("⚠️")

        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.nextButton.setEnabled(False)

        QMessageBox.warning(
            self,
            "Erreur",
            "Veuillez vérifier le brassard, "
            "le câble USB et réessayer."
        )

    # ===================================
    # PAGE SUIVANTE
    # ===================================
    def next_page(self):

        if self.measure_running:
            return

        if not self.nextButton.isEnabled():
            return

        self.main_window.go_to_temperature()
