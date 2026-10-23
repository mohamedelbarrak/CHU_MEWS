from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class WelcomePage(QWidget):

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
#white
        self.setStyleSheet("""
            QWidget{
                background:#f3f3f3;
            }

            QLabel{
                color:#2c3e50;
            }

            QPushButton{
                background:#1976D2;
                color:white;
                border:none;
                border-radius:90px;
            }

            QPushButton:hover{
                background:#1565C0;
            }

            QPushButton:pressed{
                background:#0D47A1;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(25)

        title = QLabel("CHU DE TANGER")
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Calcul Automatique du Score MEWS")
        subtitle.setFont(QFont("Arial", 18))
        subtitle.setAlignment(Qt.AlignCenter)

        developers = QLabel(
            "Développé par\n"
            "EL BARRAK Ibtihal\n\n"
            "Encadré par\n"
            "Pr. Mohamed EL BARRAK\n"
            "Pr. Imane HAMIDI\n"
            "Pr. Hamza"
        )

        developers.setAlignment(Qt.AlignCenter)
        developers.setFont(QFont("Arial", 12))

        start_button = QPushButton("DÉMARRER")
        start_button.setFixedSize(180, 180)
        start_button.setFont(QFont("Arial", 18, QFont.Bold))

        start_button.clicked.connect(
            self.main_window.go_to_ppm
        )

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(40)
        layout.addWidget(start_button, alignment=Qt.AlignCenter)
        layout.addSpacing(40)
        layout.addWidget(developers)
        layout.addStretch()