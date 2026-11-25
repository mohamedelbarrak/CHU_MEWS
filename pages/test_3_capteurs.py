
#!/usr/bin/env python3

import time
import serial
import threading

from smbus2 import SMBus, i2c_msg


# ==================================================
# CONFIGURATION GENERALE
# ==================================================

PORT_TEMPERATURE = "/dev/ttyAMA0"
PORT_DISTANCE = "/dev/ttyAMA2"

BAUD = 9600

BUS_I2C = 1
ADRESSE_SDP810 = 0x25

DUREE_RESPIRATION = 60  # Secondes : 20, 30, 60...
DUREE_CALIBRAGE = 2

SEUIL_RESPIRATION = 0.5  # Pascal
INTERVALLE = 0.040
CONFIRMATION = 0.120

MIN_CYCLE = 1.0
MAX_CYCLE = 10.0

DELAI_SANS_RESPIRATION = 10

ENTETE_TEMP = bytes.fromhex("A4 03 07 07")
COMMANDE_TOF = bytes.fromhex("01 03 00 10 00 01 85 CF")

ARRET = threading.Event()
VERROU = threading.Lock()


# ==================================================
# DONNEES PARTAGEES
# ==================================================

resultats = {
    "distance": None,
    "objet": None,
    "ambiante": None,
    "corps": None,
    "pression": None,
    "respirations": 0,
    "rpm": None,
    "temps": 0,
    "statut_respiration": "Initialisation",
    "statut_temperature": "Initialisation",
    "statut_distance": "Initialisation"
}


def actualiser(**valeurs):
    with VERROU:
        resultats.update(valeurs)


# ==================================================
# 1. CAPTEUR TEMPERATURE GY-614V3DCC
# ==================================================

def entier_signe_16(haut, bas):
    valeur = (haut << 8) | bas
    return valeur - 65536 if valeur >= 32768 else valeur


def extraire_temperature(tampon):

    while True:

        debut = tampon.find(ENTETE_TEMP)

        if debut == -1:
            if len(tampon) > 3:
                del tampon[:-3]
            return None

        if debut:
            del tampon[:debut]

        if len(tampon) < 12:
            return None

        trame = bytes(tampon[:12])

        checksum = sum(trame[:11]) & 0xFF

        if checksum != trame[11]:
            del tampon[0]
            continue

        del tampon[:12]

        objet = entier_signe_16(
            trame[5], trame[6]
        ) / 100.0

        ambiante = entier_signe_16(
            trame[7], trame[8]
        ) / 100.0

        corps = entier_signe_16(
            trame[9], trame[10]
        ) / 100.0

        return objet, ambiante, corps


def tester_temperature():

    while not ARRET.is_set():

        try:

            with serial.Serial(
                PORT_TEMPERATURE,
                baudrate=BAUD,
                timeout=0.1
            ) as capteur:

                tampon = bytearray()
                derniere_trame = time.monotonic()

                actualiser(
                    statut_temperature="UART ouvert"
                )

                while not ARRET.is_set():

                    donnees = capteur.read(
                        capteur.in_waiting or 1
                    )

                    if donnees:

                        tampon.extend(donnees)

                        while True:

                            mesure = extraire_temperature(tampon)

                            if mesure is None:
                                break

                            objet, ambiante, corps = mesure

                            derniere_trame = time.monotonic()

                            actualiser(
                                objet=objet,
                                ambiante=ambiante,
                                corps=corps,
                                statut_temperature="OK"
                            )

                    if time.monotonic() - derniere_trame > 2.5:

                        actualiser(
                            objet=None,
                            ambiante=None,
                            corps=None,
                            statut_temperature="Aucune trame recente"
                        )

        except Exception as erreur:

            actualiser(
                objet=None,
                ambiante=None,
                corps=None,
                statut_temperature=str(erreur)
            )

            ARRET.wait(2)


# ==================================================
# 2. CAPTEUR DISTANCE TOF53200
# ==================================================

def crc16_modbus(donnees):

    crc = 0xFFFF

    for octet in donnees:

        crc ^= octet

        for _ in range(8):

            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1

    return crc


def lire_distance(capteur):

    capteur.reset_input_buffer()
    capteur.write(COMMANDE_TOF)
    capteur.flush()

    tampon = bytearray()

    debut = time.monotonic()

    while (
        time.monotonic() - debut < 0.350
        and not ARRET.is_set()
    ):

        octet = capteur.read(1)

        if not octet:
            continue

        tampon.extend(octet)

        while tampon:

            if tampon[0] != 0x01:
                del tampon[0]

            elif len(tampon) >= 2 and tampon[1] != 0x03:
                del tampon[0]

            elif len(tampon) >= 3 and tampon[2] != 0x02:
                del tampon[0]

            else:
                break

        if len(tampon) < 7:
            continue

        trame = bytes(tampon[:7])

        del tampon[:7]

        crc_recu = trame[5] | (trame[6] << 8)

        if crc16_modbus(trame[:5]) != crc_recu:
            continue

        distance = (trame[3] << 8) | trame[4]

        if 0 < distance <= 2000:
            return distance

    return None


def tester_distance():

    while not ARRET.is_set():

        try:

            with serial.Serial(
                PORT_DISTANCE,
                baudrate=BAUD,
                bytesize=8,
                parity=serial.PARITY_NONE,
                stopbits=1,
                timeout=0.02,
                write_timeout=0.5
            ) as capteur:

                while not ARRET.is_set():

                    distance = None

                    for essai in range(3):

                        distance = lire_distance(capteur)

                        if distance is not None:
                            break

                        ARRET.wait(0.030)

                    if distance is not None:

                        actualiser(
                            distance=distance,
                            statut_distance="OK"
                        )

                    else:

                        actualiser(
                            distance=None,
                            statut_distance="Aucune reponse valide"
                        )

                    ARRET.wait(0.2)

        except Exception as erreur:

            actualiser(
                distance=None,
                statut_distance=str(erreur)
            )

            ARRET.wait(2)


# ==================================================
# 3. CAPTEUR RESPIRATION SDP810-125Pa
# ==================================================

def crc8_sensirion(donnees):

    crc = 0xFF

    for octet in donnees:

        crc ^= octet

        for _ in range(8):

            if crc & 0x80:
                crc = ((crc << 1) ^ 0x31) & 0xFF
            else:
                crc = (crc << 1) & 0xFF

    return crc


def commande_sdp810(bus, commande):

    message = i2c_msg.write(
        ADRESSE_SDP810,
        [
            (commande >> 8) & 0xFF,
            commande & 0xFF
        ]
    )

    bus.i2c_rdwr(message)


def lire_pression(bus):

    message = i2c_msg.read(
        ADRESSE_SDP810, 9
    )

    bus.i2c_rdwr(message)

    donnees = list(message)

    # Verification des trois CRC

    for position in (0, 3, 6):

        if crc8_sensirion(
            donnees[position:position + 2]
        ) != donnees[position + 2]:

            raise ValueError("CRC SDP810 invalide")

    pression_brute = entier_signe_16(
        donnees[0], donnees[1]
    )

    facteur = (donnees[6] << 8) | donnees[7]

    if facteur != 240:

        raise ValueError(
            f"Facteur SDP810-125Pa inattendu : {facteur}"
        )

    return pression_brute / facteur


def tester_respiration():

    while not ARRET.is_set():

        try:

            with SMBus(BUS_I2C) as bus:

                try:
                    commande_sdp810(bus, 0x3FF9)
                except OSError:
                    pass

                ARRET.wait(0.1)

                # Demarrage mesure continue
                commande_sdp810(bus, 0x3615)

                try:

                    ARRET.wait(0.1)

                    # ==============================
                    # CALIBRAGE
                    # ==============================

                    actualiser(
                        statut_respiration=(
                            "Calibrage : masque non porte"
                        ),
                        respirations=0,
                        rpm=None,
                        temps=0
                    )

                    mesures = []

                    debut_calibrage = time.monotonic()

                    while (
                        time.monotonic() - debut_calibrage
                        < DUREE_CALIBRAGE
                        and not ARRET.is_set()
                    ):

                        mesures.append(lire_pression(bus))

                        ARRET.wait(INTERVALLE)

                    if ARRET.is_set():
                        return

                    if not mesures:
                        raise ValueError("Calibrage impossible")

                    offset = sum(mesures) / len(mesures)

                    actualiser(
                        statut_respiration="Portez le masque"
                    )

                    ARRET.wait(5)

                    # ==============================
                    # MESURE RESPIRATOIRE
                    # ==============================

                    debut = time.monotonic()

                    compteur = 0
                    phase = 0

                    candidat = 0
                    debut_confirmation = None

                    dernier_cycle = None
                    dernier_signal = debut

                    while not ARRET.is_set():

                        maintenant = time.monotonic()

                        ecoule = maintenant - debut

                        if ecoule >= DUREE_RESPIRATION:
                            break

                        pression = lire_pression(bus) - offset

                        # Identifier les phases positives
                        # et negatives de la respiration.

                        if pression >= SEUIL_RESPIRATION:
                            nouvelle_phase = 1

                        elif pression <= -SEUIL_RESPIRATION:
                            nouvelle_phase = -1

                        else:
                            nouvelle_phase = 0

                        # Confirmation pendant 120 ms.

                        if nouvelle_phase != candidat:

                            candidat = nouvelle_phase
                            debut_confirmation = maintenant

                        elif (
                            candidat != 0
                            and debut_confirmation is not None
                            and maintenant - debut_confirmation
                            >= CONFIRMATION
                        ):

                            if candidat != phase:

                                dernier_signal = maintenant

                                # Une respiration complete
                                # est comptee au passage de
                                # la phase negative a positive.

                                if phase == -1 and candidat == 1:

                                    if dernier_cycle is None:

                                        compteur += 1
                                        dernier_cycle = maintenant

                                    else:

                                        duree_cycle = (
                                            maintenant - dernier_cycle
                                        )

                                        if MIN_CYCLE <= duree_cycle <= MAX_CYCLE:

                                            compteur += 1
                                            dernier_cycle = maintenant

                                        elif duree_cycle > MAX_CYCLE:

                                            # Resynchronisation
                                            # apres interruption.
                                            dernier_cycle = maintenant

                                phase = candidat

                        # Detection d'une absence de signal.

                        if (
                            maintenant - dernier_signal
                            >= DELAI_SANS_RESPIRATION
                        ):

                            actualiser(
                                pression=pression,
                                respirations=compteur,
                                temps=int(ecoule),
                                rpm=None,
                                statut_respiration=(
                                    "Aucun cycle detecte : "
                                    "verifiez le masque"
                                )
                            )

                            break

                        actualiser(
                            pression=pression,
                            respirations=compteur,
                            temps=int(ecoule),
                            statut_respiration="Respirez normalement"
                        )

                        ARRET.wait(INTERVALLE)

                    else:
                        return

                    if ARRET.is_set():
                        return

                    # Calcul de la frequence respiratoire
                    # uniquement si la duree est complete.

                    duree_reelle = time.monotonic() - debut

                    if duree_reelle >= DUREE_RESPIRATION:

                        if compteur > 0:

                            rpm = compteur * 60 / duree_reelle

                            actualiser(
                                rpm=round(rpm, 1),
                                temps=DUREE_RESPIRATION,
                                respirations=compteur,
                                statut_respiration="Mesure terminee"
                            )

                        else:

                            actualiser(
                                rpm=None,
                                statut_respiration="Mesure invalide"
                            )

                finally:

                    try:
                        commande_sdp810(bus, 0x3FF9)
                    except OSError:
                        pass

                # Conserver le resultat 10 secondes
                # puis recommencer automatiquement.

                ARRET.wait(10)

        except Exception as erreur:

            actualiser(
                pression=None,
                rpm=None,
                statut_respiration=str(erreur)
            )

            ARRET.wait(2)


# ==================================================
# 4. AFFICHAGE GLOBAL
# ==================================================

def format_valeur(valeur, unite):

    if valeur is None:
        return "Indisponible"

    return f"{valeur:.2f} {unite}"


def afficher_resultats():

    with VERROU:
        r = resultats.copy()

    print("\033[2J\033[H", end="")

    print("=" * 54)
    print("        MEWS - TEST DES TROIS CAPTEURS")
    print("=" * 54)

    print("\n[1] RESPIRATION - SDP810-125Pa")
    print("-" * 54)

    print("Statut      :", r["statut_respiration"])

    print("Pression    :", format_valeur(
        r["pression"], "Pa"
    ))

    print("Respirations:", r["respirations"])

    print(
        f"Chronometre : {r['temps']} / "
        f"{DUREE_RESPIRATION} secondes"
    )

    print("Frequence   :", format_valeur(
        r["rpm"], "resp/min"
    ))

    print("\n[2] DISTANCE - TOF53200")
    print("-" * 54)

    print("Statut      :", r["statut_distance"])

    if r["distance"] is not None:

        print(f"Distance    : {r['distance']} mm")

        print(f"Distance    : {r['distance'] / 10:.1f} cm")

    else:

        print("Distance    : Indisponible")

    print("\n[3] TEMPERATURE - GY-614V3DCC")
    print("-" * 54)

    print("Statut      :", r["statut_temperature"])

    print("Objet       :", format_valeur(
        r["objet"], "C"
    ))

    print("Ambiante    :", format_valeur(
        r["ambiante"], "C"
    ))

    print("Corps estime:", format_valeur(
        r["corps"], "C"
    ))

    print("\n" + "=" * 54)
    print("Ctrl+C pour arreter le programme.")
    print("=" * 54, flush=True)


# ==================================================
# 5. PROGRAMME PRINCIPAL
# ==================================================

def main():

    if PORT_TEMPERATURE == PORT_DISTANCE:

        raise SystemExit(
            "ERREUR : les deux capteurs UART "
            "doivent utiliser des ports differents."
        )

    threads = [

        threading.Thread(
            target=tester_temperature,
            name="Temperature",
            daemon=True
        ),

        threading.Thread(
            target=tester_distance,
            name="Distance",
            daemon=True
        ),

        threading.Thread(
            target=tester_respiration,
            name="Respiration",
            daemon=True
        )
    ]

    for thread in threads:
        thread.start()

    try:

        while not ARRET.is_set():

            afficher_resultats()

            ARRET.wait(1)

    except KeyboardInterrupt:

        print("\nArret du programme...")

    finally:

        ARRET.set()

        for thread in threads:
            thread.join(timeout=3)

        print("Programme arrete.")


if __name__ == "__main__":
    main()
