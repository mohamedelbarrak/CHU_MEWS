class Patient:

    def __init__(self):

        self.reset()

    def reset(self):

        # Identification
        self.ppm = ""

        # Constantes vitales
        self.temperature = None
        self.frequence_cardiaque = None
        self.frequence_respiratoire = None
        self.pression_systolique = None
        self.pression_diastolique = None
        self.spo2 = None

        # Evaluation clinique
        self.conscience = None

        # Résultat
        self.score_mews = None