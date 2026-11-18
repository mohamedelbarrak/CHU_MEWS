from PySide6.QtWidgets import QStackedWidget

from blood_pressure_page import BloodPressurePage
from welcome_page import WelcomePage
from ppm_page import PPMPage
from patient import Patient
from respiration_page import RespirationPage
from temperature import TemperaturePage
#from consciousness_page import ConsciousnessPage


class MainWindow(QStackedWidget):
    """
    Fenêtre principale de l'application.
    Toutes les pages seront ajoutées ici.
    """

    def __init__(self):
        super().__init__()

        self.patient = Patient()

        # Informations de la fenêtre
        self.setWindowTitle("CHU Tanger - Calcul du Score MEWS")

        # Taille minimale (utile pendant le développement)
        #self.setMinimumSize(1280, 720)
        self.setMinimumSize(860, 280)

        # -------- Création des pages --------
        self.welcome_page = WelcomePage(self)
        self.ppm_page = PPMPage(self)
        self.respiration_page = RespirationPage(self)
        self.blood_pressure_page = BloodPressurePage(self)
        self.temperaturePage = TemperaturePage(self)
#        self.consciousnessPage = ConsciousnessPage(self)

        # -------- Ajout des pages --------
        self.addWidget(self.welcome_page)   # Index 0
        self.addWidget(self.ppm_page)       # Index 1
        self.addWidget(self.respiration_page)   # Index 2
        self.addWidget(self.blood_pressure_page)   # Index 3
        self.addWidget(self.temperaturePage)   # Index 4
#        self.addWidget(self.consciousnessPage)   # Index 5

        # -------- Première page affichée --------
        self.setCurrentIndex(0)
        self.resize(800, 480)
        # Pour la borne finale, décommente cette ligne :
        #self.showFullScreen()

    # =====================================================
    # Fonctions de navigation
    # =====================================================

    def go_to_welcome(self):
        """Retour à la page d'accueil."""
        self.setCurrentIndex(0)

    def go_to_ppm(self):
        """Aller à la page de saisie du PPM."""
        self.setCurrentIndex(1)

    def go_to_respiration(self):
        """Aller à la page de saisie de la fréquence respiratoire."""
        #self.respiration_page.reset_page()
        self.setCurrentIndex(2)

#    def go_to_temperature(self):
#        """Aller à la page de saisie de la température."""
#        self.setCurrentIndex(3)

    def go_to_blood_pressure(self):
        """Aller à la page de saisie de la pression artérielle."""
        self.setCurrentIndex(3)

    def go_to_temperature(self):
        self.setCurrentIndex(4)


#    def go_to_consciousness(self):
#        self.consciousnessPage.reset_page()
#        self.setCurrentWidget(self.consciousnessPage)