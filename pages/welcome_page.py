
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)


class WelcomePage(QWidget):

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
        self.setObjectName("welcomePage")

        self.setStyleSheet("""
            QWidget#welcomePage {
                background-color: #F4F7FA;
            }

            QLabel {
                background: transparent;
                color: #243B53;
            }

            QPushButton#startButton {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 65px;
                font-size: 18px;
                font-weight: bold;
            }

            QPushButton#startButton:hover {
                background-color: #1565C0;
            }

            QPushButton#startButton:pressed {
                background-color: #0D47A1;
            }
        """)

        # ===================================
        # LAYOUT PRINCIPAL
        # ===================================
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(0)

        # ===================================
        # TITRE
        # ===================================
        title = QLabel("CHU DE TANGER")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setFixedHeight(42)

        subtitle = QLabel(
            "Calcul automatique du score MEWS"
        )
        subtitle.setFont(QFont("Arial", 15))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFixedHeight(34)

        # ===================================
        # BOUTON DEMARRER
        # ===================================
        start_button = QPushButton("DÉMARRER")#▶ 
        start_button.setObjectName("startButton")
        start_button.setFixedSize(130, 130)
        start_button.setCursor(Qt.PointingHandCursor)

        start_button.clicked.connect(
            self.main_window.go_to_ppm
        )

        # ===================================
        # INFORMATIONS
        # ===================================
        info_layout = QHBoxLayout()
        info_layout.setSpacing(30)

        # Développeur
        developer_layout = QVBoxLayout()
        developer_layout.setSpacing(5)

        dev_title = QLabel("DÉVELOPPÉ PAR")
        dev_title.setFont(QFont("Arial", 11, QFont.Bold))
        dev_title.setAlignment(Qt.AlignCenter)
        dev_title.setStyleSheet("color: #607D98;")

        developer = QLabel("EL BARRAK Ibtihal")
        developer.setFont(QFont("Arial", 15, QFont.Bold))
        developer.setAlignment(Qt.AlignCenter)

        developer_layout.addWidget(dev_title)
        developer_layout.addWidget(developer)

        # Encadrants
        supervisor_layout = QVBoxLayout()
        supervisor_layout.setSpacing(5)

        sup_title = QLabel("ENCADRÉ PAR")
        sup_title.setFont(QFont("Arial", 11, QFont.Bold))
        sup_title.setAlignment(Qt.AlignCenter)
        sup_title.setStyleSheet("color: #607D98;")

        supervisors = QLabel(
            "Pr. Mohamed EL BARRAK\n"
            "Pr. Imane HAMIDI\n"
            "Pr. Hamza"
        )
        supervisors.setFont(QFont("Arial", 12))
        supervisors.setAlignment(Qt.AlignCenter)

        supervisor_layout.addWidget(sup_title)
        supervisor_layout.addWidget(supervisors)

        info_layout.addLayout(developer_layout, 1)
        info_layout.addLayout(supervisor_layout, 1)

        # ===================================
        # PIED DE PAGE
        # ===================================
        footer = QLabel("Interface MEWS · CHU de Tanger")
        footer.setAlignment(Qt.AlignCenter)
        footer.setFont(QFont("Arial", 10))
        footer.setStyleSheet("color: #728499;")
        footer.setFixedHeight(18)

        # ===================================
        # ASSEMBLAGE FINAL
        # ===================================
        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addSpacing(35)

        layout.addWidget(
            start_button,
            alignment=Qt.AlignCenter
        )

        layout.addSpacing(35)

        layout.addLayout(info_layout)

        layout.addStretch()

        layout.addWidget(
            footer,
            alignment=Qt.AlignCenter
        )
