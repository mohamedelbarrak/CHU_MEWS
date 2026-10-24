
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QSizePolicy
)


class PPMPage(QWidget):

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
        self.ppm = ""

        self.setObjectName("ppmPage")

        self.setStyleSheet("""
            QWidget#ppmPage {
                background-color: #F4F7FA;
            }

            QLabel {
                color: #243B53;
            }

            QPushButton {
                border: none;
                border-radius: 8px;
                font-size: 19px;
                font-weight: bold;
            }

            QPushButton#number {
                background-color: #DCEEFE;
                color: #145B9C;
                border: 1px solid #A5CBF0;
            }

            QPushButton#number:hover {
                background-color: #BDDDF9;
            }

            QPushButton#number:pressed {
                background-color: #91C4F2;
            }

            QPushButton#clear {
                background-color: #FCE1E1;
                color: #B42332;
            }

            QPushButton#clear:pressed {
                background-color: #F5B9BD;
            }

            QPushButton#validate {
                background-color: #D8F4E5;
                color: #176C43;
            }

            QPushButton#validate:pressed {
                background-color: #A9E6C4;
            }

            QLabel#display {
                background-color: white;
                border: 2px solid #84B8E9;
                border-radius: 8px;
                color: #193853;
                font-size: 25px;
                font-weight: bold;
            }
        """)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 8, 16, 10)
        main_layout.setSpacing(6)

        # Titre
        title = QLabel("Identification du patient")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 21, QFont.Bold))
        title.setFixedHeight(36)

        # Instruction
        instruction = QLabel("Veuillez saisir le PPM")
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setFont(QFont("Arial", 13))
        instruction.setFixedHeight(24)

        # Affichage du PPM
        self.display = QLabel("")
        self.display.setObjectName("display")
        self.display.setAlignment(Qt.AlignCenter)
        self.display.setFixedHeight(48)

        # Pavé numérique
        keypad = QGridLayout()
        keypad.setSpacing(6)

        positions = [
            ("1", 0, 0), ("2", 0, 1), ("3", 0, 2),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2),
            ("0", 3, 1)
        ]

        for text, row, col in positions:
            button = QPushButton(text)
            button.setObjectName("number")
            button.setFixedHeight(48)
            button.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed
            )

            button.clicked.connect(
                lambda checked=False, t=text: self.add_digit(t)
            )

            keypad.addWidget(button, row, col)

        # Boutons d'action
        buttons = QHBoxLayout()
        buttons.setSpacing(8)

        clear = QPushButton("Effacer")
        clear.setObjectName("clear")
        clear.setFixedHeight(46)
        clear.clicked.connect(self.clear)

        validate = QPushButton("Valider")
        validate.setObjectName("validate")
        validate.setFixedHeight(46)
        validate.clicked.connect(self.validate)

        buttons.addWidget(clear)
        buttons.addWidget(validate)

        # Assemblage
        main_layout.addWidget(title)
        main_layout.addWidget(instruction)
        main_layout.addSpacing(7)
        main_layout.addWidget(self.display)
        main_layout.addSpacing(8)
        main_layout.addLayout(keypad)
        main_layout.addSpacing(8)
        main_layout.addLayout(buttons)
        main_layout.addStretch(1)

    def add_digit(self, digit):
        self.ppm += digit
        self.display.setText(self.ppm)

    def clear(self):
        self.ppm = ""
        self.display.setText("")

    def validate(self):
        if len(self.ppm) != 4:
            QMessageBox.warning(
                self,
                "PPM invalide",
                "Veuillez saisir un PPM valide."
            )
            return

        self.main_window.patient.ppm = self.ppm
        self.main_window.go_to_respiration()
