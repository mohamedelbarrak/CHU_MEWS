
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout, QWidget, QLabel, QPushButton, QVBoxLayout,
    QMessageBox, QProgressBar
)

class BloodPressurePage(QWidget):
    """
    Page de mesure de la pression artérielle et de la fréquence cardiaque.
    Les emplacements pour la communication Arduino/Raspberry sont marqués
    par 'TODO'.
    """

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window

        self.measure_running = False
        self.timeout = 0
        self.progress = 0
        self.heart_state = False

        # =========================================================
        # TIMER
        # =========================================================

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_timeout)

        # =========================================================
        # STYLE GENERAL
        # =========================================================

        self.setStyleSheet("""
        QWidget {
            background: #f5f7fa;
        }

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

        QProgressBar {
            border: none;
            border-radius: 10px;
            background: #e0e0e0;
            height: 18px;
            text-align: center;
        }

        QProgressBar::chunk {
            background: #1976D2;
            border-radius: 10px;
        }
        """)

        # =========================================================
        # LAYOUT PRINCIPAL
        # =========================================================

        layout = QVBoxLayout(self)

        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(20)

        # =========================================================
        # TITRE
        # =========================================================

        title = QLabel("Mesure de la pression artérielle")

        title.setAlignment(Qt.AlignCenter)

        title.setFont(
            QFont("Arial", 30, QFont.Bold)
        )

        layout.addWidget(title)

        # =========================================================
        # ESPACE
        # =========================================================

        layout.addSpacing(10)

        # =========================================================
        # INFORMATION
        # =========================================================

        info = QLabel(
            "Placez correctement le brassard\n"
            "puis cliquez sur COMMENCER."
        )

        info.setAlignment(Qt.AlignCenter)

        info.setFont(
            QFont("Arial", 21, QFont.Bold)
        )

        layout.addWidget(info)

        # =========================================================
        # ESPACE
        # =========================================================

        layout.addSpacing(15)

        # =========================================================
        # COEUR
        # =========================================================

        self.animationLabel = QLabel("❤️")

        self.animationLabel.setAlignment(Qt.AlignCenter)

        self.animationLabel.setFont(
            QFont("Arial", 75)
        )

        layout.addWidget(self.animationLabel)

        # =========================================================
        # BARRE DE PROGRESSION
        # =========================================================

        self.progressBar = QProgressBar()

        self.progressBar.setRange(0, 100)

        self.progressBar.setValue(0)

        self.progressBar.setMinimumHeight(18)

        layout.addWidget(self.progressBar)

        # =========================================================
        # STATUT
        # =========================================================

        self.statusLabel = QLabel(
            "Prêt pour la mesure"
        )

        self.statusLabel.setAlignment(Qt.AlignCenter)

        self.statusLabel.setFont(
            QFont("Arial", 22, QFont.Bold)
        )

        layout.addWidget(self.statusLabel)

        # =========================================================
        # ESPACE
        # =========================================================

        layout.addSpacing(15)

        # =========================================================
        # RESULTATS
        # =========================================================

        results_layout = QHBoxLayout()

        results_layout.setSpacing(40)

        # -------------------------
        # PRESSION
        # -------------------------

        pressure_container = QVBoxLayout()

        pressure_title = QLabel(
            "Pression artérielle"
        )

        pressure_title.setAlignment(
            Qt.AlignCenter
        )

        pressure_title.setFont(
            QFont("Arial", 20, QFont.Bold)
        )

        self.pressureLabel = QLabel(
            "-- / -- mmHg"
        )

        self.pressureLabel.setAlignment(
            Qt.AlignCenter
        )

        self.pressureLabel.setFont(
            QFont("Arial", 26, QFont.Bold)
        )

        pressure_container.addWidget(
            pressure_title
        )

        pressure_container.addWidget(
            self.pressureLabel
        )

        # -------------------------
        # FREQUENCE CARDIAQUE
        # -------------------------

        heart_container = QVBoxLayout()

        heart_title = QLabel(
            "Fréquence cardiaque"
        )

        heart_title.setAlignment(
            Qt.AlignCenter
        )

        heart_title.setFont(
            QFont("Arial", 20, QFont.Bold)
        )

        self.heartRateLabel = QLabel(
            "-- BPM"
        )

        self.heartRateLabel.setAlignment(
            Qt.AlignCenter
        )

        self.heartRateLabel.setFont(
            QFont("Arial", 26, QFont.Bold)
        )

        heart_container.addWidget(
            heart_title
        )

        heart_container.addWidget(
            self.heartRateLabel
        )

        # Ajouter les deux résultats
        results_layout.addLayout(
            pressure_container
        )

        results_layout.addLayout(
            heart_container
        )

        layout.addLayout(
            results_layout
        )

        # =========================================================
        # ESPACE FLEXIBLE
        # =========================================================

        layout.addStretch()

        # =========================================================
        # BOUTONS
        # =========================================================

        self.startButton = QPushButton(
            "COMMENCER"
        )

        self.stopButton = QPushButton(
            "ARRÊTER"
        )

        self.nextButton = QPushButton(
            "SUIVANT"
        )

        # Même largeur
        self.startButton.setMinimumWidth(220)
        self.stopButton.setMinimumWidth(220)
        self.nextButton.setMinimumWidth(220)

        # États initiaux
        self.stopButton.setEnabled(False)

        self.nextButton.setEnabled(False)

        # Connexions
        self.startButton.clicked.connect(
            self.start_measure
        )

        self.stopButton.clicked.connect(
            self.stop_measure
        )

        self.nextButton.clicked.connect(
            self.next_page
        )

        # =========================================================
        # LIGNE DES 3 BOUTONS
        # =========================================================

        buttons_layout = QHBoxLayout()

        buttons_layout.setSpacing(20)

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

        layout.addLayout(
            buttons_layout
        )

        # Petit espace en bas
        layout.addSpacing(10)

        self.setLayout(layout)



    def reset_page(self):
        self.measure_running = False
        self.timeout = 0
        self.progress = 0
        self.timer.stop()
        self.progressBar.setValue(0)
        self.animationLabel.setText("❤️")
        self.statusLabel.setText("Prêt pour la mesure")
        self.pressureLabel.setText("-- / -- mmHg")
        self.heartRateLabel.setText("-- BPM")
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.nextButton.setEnabled(False)

    def start_measure(self):
        self.reset_page()
        self.measure_running = True
        self.statusLabel.setText("Mesure en cours...")
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)

        # TODO:
        # Démarrer la communication avec l'Arduino / tensiomètre
        # Exemple :
        # self.serial.write(b"START\n")

        self.timer.start(50)#0,5 seconde → 1 %      50

    def stop_measure(self):
        self.timer.stop()
        self.measure_running = False
        self.statusLabel.setText("Mesure arrêtée")
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)

    def check_timeout(self):
        if not self.measure_running:
            return

        self.timeout += 1
        self.progress = min(100, self.progress + 1)
        self.progressBar.setValue(self.progress)

        self.heart_state = not self.heart_state
        self.animationLabel.setText("🫀" if self.heart_state else "❤️")

        # TODO:
        # Lire les données Arduino.
        # Quand les données sont disponibles :
        #
        # self.receive_measure(systolique, diastolique, bpm)

        if self.timeout == 20:
            # Simulation
            self.receive_measure(118, 76, 72)

        if self.timeout >= 120:
            self.show_measure_error()

    def receive_measure(self, systolique, diastolique, bpm):
        self.timer.stop()
        self.measure_running = False

        if hasattr(self.main_window, "patient"):
            p = self.main_window.patient
            p.pression_systolique = systolique
            p.pression_diastolique = diastolique
            p.frequence_cardiaque = bpm

        self.pressureLabel.setText(f"{systolique} / {diastolique} mmHg")
        self.heartRateLabel.setText(f"{bpm} BPM")
        self.statusLabel.setText("Mesure terminée")
        self.progressBar.setValue(100)

        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.nextButton.setEnabled(True)

    def show_measure_error(self):
        self.timer.stop()
        self.measure_running = False
        self.statusLabel.setText("Échec de la mesure")
        self.animationLabel.setText("⚠️")
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)

        QMessageBox.warning(
            self,
            "Erreur",
            "Veuillez vérifier le brassard, le câble USB et réessayer."
        )

    def next_page(self):
        # TODO:
        # self.main_window.go_to_consciousness()
        print("Passage à la page suivante.")
        self.main_window.go_to_temperature()
