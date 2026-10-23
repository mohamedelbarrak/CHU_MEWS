
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

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_timeout)

        self.setStyleSheet("""
        QWidget{background:#f3f3f3;}
        QLabel{color:#2c3e50;}
        QPushButton{
            background:#1976D2;color:white;border:none;
            border-radius:12px;font-size:18px;min-height:55px;
        }
        QPushButton:hover{background:#1565C0;}
        QPushButton:disabled{background:#BDBDBD;}
        """)

        layout = QVBoxLayout(self)

        title = QLabel("Mesure de la pression artérielle")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 26, QFont.Bold))

        info = QLabel("Placez correctement le brassard puis cliquez sur COMMENCER.")
        info.setAlignment(Qt.AlignCenter)

        self.animationLabel = QLabel("❤️")
        self.animationLabel.setAlignment(Qt.AlignCenter)
        self.animationLabel.setFont(QFont("Arial", 48))

        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)

        self.statusLabel = QLabel("Prêt pour la mesure")
        self.statusLabel.setAlignment(Qt.AlignCenter)

        self.pressureLabel = QLabel("-- / -- mmHg")
        self.pressureLabel.setAlignment(Qt.AlignCenter)
        self.pressureLabel.setFont(QFont("Arial", 22, QFont.Bold))

        self.heartRateLabel = QLabel("-- BPM")
        self.heartRateLabel.setAlignment(Qt.AlignCenter)
        self.heartRateLabel.setFont(QFont("Arial", 22, QFont.Bold))

        self.startButton = QPushButton("COMMENCER")
        self.stopButton = QPushButton("ARRÊTER")
        self.nextButton = QPushButton("SUIVANT")

        self.stopButton.setEnabled(False)
        self.nextButton.setEnabled(False)

        self.startButton.clicked.connect(self.start_measure)
        self.stopButton.clicked.connect(self.stop_measure)
        self.nextButton.clicked.connect(self.next_page)

        layout.addWidget(title)
        layout.addWidget(info)
        layout.addWidget(self.animationLabel)
        layout.addWidget(self.progressBar)
        layout.addWidget(self.statusLabel)
        layout.addWidget(QLabel("Pression artérielle :"))
        layout.addWidget(self.pressureLabel)
        layout.addWidget(QLabel("Fréquence cardiaque :"))
        layout.addWidget(self.heartRateLabel)


        # layout.addWidget(self.startButton)
        # layout.addWidget(self.stopButton)
        # layout.addWidget(self.nextButton)

        # =========================
        # LIGNE DES 3 BOUTONS
        # =========================

        layout.setSpacing(15)

        buttons_layout = QHBoxLayout()

        buttons_layout.setSpacing(15)

        buttons_layout.addWidget(self.startButton)
        buttons_layout.addWidget(self.stopButton)
        buttons_layout.addWidget(self.nextButton)

        # On ajoute le HBox dans le VBox
        layout.addLayout(buttons_layout)


        layout.addStretch()

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
