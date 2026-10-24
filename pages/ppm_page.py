
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QStyle
)


class PPMPage(QWidget):

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
        self.ppm = ""

        self.setObjectName("ppmPage")

        # ===================================
        # STYLE GENERAL
        # ===================================
        self.setStyleSheet("""
            QWidget#ppmPage {
                background-color: #F4F7FA;
            }

            QLabel {
                color: #243B53;
                background: transparent;
            }

            QPushButton {
                border: none;
                border-radius: 8px;
                font-size: 19px;
                font-weight: bold;
            }

            QPushButton#backButton {
                background-color: #DCEEFE;
                color: #145B9C;
                border: 1px solid #A5CBF0;
            }

            QPushButton#backButton:hover {
                background-color: #BDDDF9;
            }

            QPushButton#backButton:pressed {
                background-color: #91C4F2;
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

            QPushButton#clear:hover {
                background-color: #F8CDCF;
            }

            QPushButton#clear:pressed {
                background-color: #F5B9BD;
            }

            QPushButton#validate {
                background-color: #D8F4E5;
                color: #176C43;
            }

            QPushButton#validate:hover {
                background-color: #C2EDD6;
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

            QLabel#display[error="true"] {
                border: 2px solid #E57373;
            }

            QLabel#errorLabel {
                color: #C62828;
                font-size: 13px;
                font-weight: bold;
            }
        """)

        # ===================================
        # LAYOUT PRINCIPAL
        # ===================================
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 8, 16, 10)
        main_layout.setSpacing(5)

        # ===================================
        # BOUTON RETOUR + TITRE
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
        back_button.setToolTip("Retour à l'accueil")
        back_button.clicked.connect(self.go_back)

        title = QLabel("Identification du patient")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 21, QFont.Bold))
        title.setFixedHeight(40)

        right_space = QWidget()
        right_space.setFixedWidth(44)

        header.addWidget(back_button)
        header.addWidget(title, 1)
        header.addWidget(right_space)

        # ===================================
        # INSTRUCTION
        # ===================================
        instruction = QLabel("Veuillez saisir le PPM")
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setFont(QFont("Arial", 13))
        instruction.setFixedHeight(24)

        # ===================================
        # AFFICHAGE DU PPM
        # ===================================
        self.display = QLabel("")
        self.display.setObjectName("display")
        self.display.setProperty("error", False)
        self.display.setAlignment(Qt.AlignCenter)
        self.display.setFixedHeight(44)

        # ===================================
        # MESSAGE D'ERREUR
        # ===================================
        self.errorLabel = QLabel("")
        self.errorLabel.setObjectName("errorLabel")
        self.errorLabel.setAlignment(Qt.AlignCenter)
        self.errorLabel.setFixedHeight(24)
        self.errorLabel.hide()

        # ===================================
        # PAVE NUMERIQUE
        # ===================================
        keypad = QGridLayout()
        keypad.setSpacing(5)

        positions = [
            ("1", 0, 0), ("2", 0, 1), ("3", 0, 2),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2),
            ("0", 3, 1)
        ]

        for text, row, col in positions:

            button = QPushButton(text)
            button.setObjectName("number")
            button.setFixedHeight(52)

            button.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed
            )

            button.setCursor(Qt.PointingHandCursor)

            button.clicked.connect(
                lambda checked=False, t=text: self.add_digit(t)
            )

            keypad.addWidget(button, row, col)

        # ===================================
        # BOUTONS EFFACER / VALIDER
        # ===================================
        buttons = QHBoxLayout()
        buttons.setSpacing(8)

        clear = QPushButton("⌫ Effacer")
        clear.setObjectName("clear")
        clear.setFixedHeight(48)
        clear.setCursor(Qt.PointingHandCursor)
        clear.clicked.connect(self.clear)

        validate = QPushButton("Valider")
        validate.setObjectName("validate")
        validate.setFixedHeight(48)
        validate.setCursor(Qt.PointingHandCursor)
        validate.clicked.connect(self.validate)

        buttons.addWidget(clear)
        buttons.addWidget(validate)

        # ===================================
        # ASSEMBLAGE FINAL
        # ===================================
        main_layout.addLayout(header)
        main_layout.addWidget(instruction)

        main_layout.addSpacing(10)

        main_layout.addWidget(self.display)

        # Zone du message d'erreur
        main_layout.addWidget(self.errorLabel)

        # Espace avant le pavé numérique
        main_layout.addSpacing(12)

        main_layout.addLayout(keypad)

        # Espace avant les actions
        main_layout.addSpacing(14)

        main_layout.addLayout(buttons)

        main_layout.addStretch(1)

    # ===================================
    # AFFICHER OU MASQUER L'ERREUR
    # ===================================
    def set_error(self, message=""):

        has_error = bool(message)

        self.errorLabel.setText(message)
        self.errorLabel.setVisible(has_error)

        self.display.setProperty("error", has_error)

        # Actualiser le style après modification
        self.display.style().unpolish(self.display)
        self.display.style().polish(self.display)
        self.display.update()

    # ===================================
    # RETOUR A LA PAGE D'ACCUEIL
    # ===================================
    def go_back(self):
        self.set_error()
        self.main_window.go_to_welcome()

    # ===================================
    # AJOUTER UN CHIFFRE
    # ===================================
    def add_digit(self, digit):

        if len(self.ppm) < 4:
            self.ppm += digit
            self.display.setText(self.ppm)

        # Supprimer l'erreur dès la correction
        self.set_error()

    # ===================================
    # EFFACER LE DERNIER CHIFFRE
    # ===================================
    def clear(self):

        if self.ppm:
            self.ppm = self.ppm[:-1]
            self.display.setText(self.ppm)

        self.set_error()

    # ===================================
    # REINITIALISER COMPLETEMENT
    # ===================================
    def reset_page(self):

        self.ppm = ""
        self.display.setText("")
        self.set_error()

    # ===================================
    # VALIDATION DU PPM
    # ===================================
    def validate(self):

        if len(self.ppm) != 4:

            self.set_error(
                "⚠ Le PPM doit contenir exactement 4 chiffres."
            )
            return

        # Validation réussie
        self.set_error()

        # Sauvegarde dans Patient
        self.main_window.patient.ppm = self.ppm

        # Aller vers RespirationPage
        self.main_window.go_to_respiration()
