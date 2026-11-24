#!/usr/bin/env python3
"""Test continu du GY-614V3 / MLX90614-DCC en mode UART sur Raspberry Pi 4.

Cablage de test (capteur seul):
  VCC -> Pi 3,3 V (pin physique 1, si compatible avec le module)
  GND -> Pi GND (pin physique 6)
  TD (TX capteur) -> Pi GPIO15 RXD (pin physique 10)
  RC (RX capteur) -> non connecte (sortie automatique par defaut)

Necessite: python3-serial, UART expose comme /dev/ttyAMA0.
Trame attendue: A4 03 07 07 E TO_H TO_L TA_H TA_L BO_H BO_L CHECKSUM.
"""

import time

try:
    import serial
except ImportError:
    raise SystemExit("Bibliotheque manquante : sudo apt install python3-serial")

PORT = "/dev/ttyAMA0"
BAUD = 9600
ENTETE = bytes([0xA4, 0x03, 0x07, 0x07])
TAILLE_TRAME = 12
INTERVALLE_AFFICHAGE = 1.0  # secondes
AGE_MAX_MESURE = 2.5  # evite de repeter une ancienne mesure


def entier_signe_16(haut, bas):
    valeur = (haut << 8) | bas
    return valeur - 65536 if valeur >= 32768 else valeur


def extraire_mesure(tampon):
    """Extrait une trame complete valide si possible; modifie le tampon sur place."""
    while True:
        debut = tampon.find(ENTETE)
        if debut == -1:
            # conserver les derniers octets pour une entete coupee en deux lectures
            if len(tampon) > len(ENTETE) - 1:
                del tampon[:-(len(ENTETE) - 1)]
            return None
        if debut:
            del tampon[:debut]
        if len(tampon) < TAILLE_TRAME:
            return None

        trame = bytes(tampon[:TAILLE_TRAME])
        checksum = sum(trame[:11]) & 0xFF
        if checksum != trame[11]:
            # supprimer un octet puis chercher la prochaine entete
            del tampon[0]
            continue

        del tampon[:TAILLE_TRAME]
        objet = entier_signe_16(trame[5], trame[6]) / 100.0
        ambiante = entier_signe_16(trame[7], trame[8]) / 100.0
        corps = entier_signe_16(trame[9], trame[10]) / 100.0
        return (objet, ambiante, corps)


def surveiller_temperature(port):
    tampon = bytearray()
    derniers_octets = bytearray()
    derniere_mesure = None
    date_derniere_mesure = 0.0
    prochain_affichage = time.monotonic() + INTERVALLE_AFFICHAGE
    compteur = 0

    with serial.Serial(port, baudrate=BAUD, timeout=0.1) as capteur:
        print(f"Port UART ouvert : {port} a {BAUD} bauds", flush=True)
        print("Attente des donnees du capteur...", flush=True)

        while True:
            donnees = capteur.read(capteur.in_waiting or 1)
            if donnees:
                tampon.extend(donnees)
                derniers_octets.extend(donnees)
                if len(derniers_octets) > 32:
                    del derniers_octets[:-32]

                while True:
                    mesure = extraire_mesure(tampon)
                    if mesure is None:
                        break
                    derniere_mesure = mesure
                    date_derniere_mesure = time.monotonic()

            maintenant = time.monotonic()
            if maintenant >= prochain_affichage:
                compteur += 1
                print(f"\n--- Mesure {compteur} ({compteur} s environ) ---")
                if (derniere_mesure is not None
                        and maintenant - date_derniere_mesure <= AGE_MAX_MESURE):
                    objet, ambiante, corps = derniere_mesure
                    print(f"Temperature objet              : {objet:.2f} C")
                    print(f"Temperature ambiante           : {ambiante:.2f} C")
                    print(f"Temperature corporelle estimee : {corps:.2f} C")
                    print(f"Age de la derniere trame       : {maintenant - date_derniere_mesure:.1f} s")
                else:
                    print("Mesure indisponible : aucune trame valide recente.")
                    if derniers_octets:
                        print("Derniers octets recus (HEX) :", derniers_octets.hex(" ").upper())
                    else:
                        print("Aucun octet recu : verifier TD -> GPIO15, GND, alimentation et UART.")
                prochain_affichage += INTERVALLE_AFFICHAGE
                if prochain_affichage < maintenant:
                    prochain_affichage = maintenant + INTERVALLE_AFFICHAGE


def main():
    print("=== TEST TEMPERATURE GY-614V3 / DCC - RASPBERRY PI ===")
    print("Lecture UART continue, affichage toutes les secondes.")
    print("Arret : Ctrl+C\n")
    while True:
        try:
            surveiller_temperature(PORT)
        except KeyboardInterrupt:
            print("\nTest arrete.")
            return
        except (serial.SerialException, OSError) as exc:
            print(f"\nErreur du port UART : {exc}")
            print("Nouvelle tentative dans 2 secondes...")
            try:
                time.sleep(2)
            except KeyboardInterrupt:
                print("\nTest arrete.")
                return


if __name__ == "__main__":
    main()
