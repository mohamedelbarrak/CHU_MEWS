from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
)
from PySide6.QtWidgets import QMessageBox

class PPMPage(QWidget):

    def __init__(self, main_window):
        super().__init__()
        #self.main_window.patient

        self.main_window = main_window

        self.ppm = ""

        self.setStyleSheet("""
            QWidget{
                background:white;
            }

            QPushButton{
                background:#1976D2;
                color:white;
                border:none;
                border-radius:10px;
                font-size:20px;
                min-height:70px;
            }

            QPushButton:hover{
                background:#1565C0;
            }

            QLabel{
                color:#2c3e50;
            }
        """)

        main_layout = QVBoxLayout(self)

        title = QLabel("Identification du patient")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Bold))

        instruction = QLabel("Veuillez saisir le PPM")
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setFont(QFont("Arial", 16))

        self.display = QLabel("")
        self.display.setAlignment(Qt.AlignCenter)
        self.display.setMinimumHeight(70)
        self.display.setStyleSheet("""
            QLabel{
                background:#ecf0f1;
                border:2px solid #1976D2;
                border-radius:8px;
                font-size:28px;
                color:black;
            }
        """)

        keypad = QGridLayout()

        positions = [
            ("1",0,0), ("2",0,1), ("3",0,2),
            ("4",1,0), ("5",1,1), ("6",1,2),
            ("7",2,0), ("8",2,1), ("9",2,2),
            ("0",3,1)
        ]

        for text,row,col in positions:

            button = QPushButton(text)

            button.clicked.connect(
                lambda checked=False, t=text: self.add_digit(t)
            )

            keypad.addWidget(button,row,col)

        buttons = QHBoxLayout()

        clear = QPushButton("Effacer")
        clear.clicked.connect(self.clear)

        validate = QPushButton("Valider")
        validate.clicked.connect(self.validate)

        buttons.addWidget(clear)
        buttons.addWidget(validate)

        main_layout.addStretch()

        main_layout.addWidget(title)
        main_layout.addWidget(instruction)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.display)
        main_layout.addSpacing(30)

        main_layout.addLayout(keypad)
        main_layout.addSpacing(20)

        main_layout.addLayout(buttons)

        main_layout.addStretch()

    def add_digit(self, digit):

        self.ppm += digit

        self.display.setText(self.ppm)

    def clear(self):

        self.ppm = ""

        self.display.setText("")

    #def validate(self):

        #self.main_window.patient.ppm = self.ppm

        #print(self.main_window.patient.ppm)

        # Aller vers la page suivante
        # self.main_window.go_to_temperature()
    def validate(self):
        if len(self.ppm) != 4:#24
            print("PPM invalide")
            QMessageBox.warning(
                self,
                "IPP invalide",
                "Veuillez saisir un IPP valide."
            )
            return

        self.main_window.patient.ppm = self.ppm
        self.main_window.go_to_respiration()
        