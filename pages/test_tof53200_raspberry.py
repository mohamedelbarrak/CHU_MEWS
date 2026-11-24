#!/usr/bin/env python3
"""Test continu du capteur TOF53200 sur le Raspberry Pi 4 (UART/Modbus).

Reprise fidèle du croquis Arduino fourni :
- UART 9600 bauds, 8N1
- commande Modbus 01 03 00 10 00 01 85 CF
- réponse 7 octets : 01 03 02 DIST_H DIST_L CRC_LO CRC_HI
- CRC16 Modbus, 3 tentatives, timeout 350 ms
"""

import time
import serial

# Raspberry Pi 4 : GPIO14 (TX), GPIO15 (RX), UART0 après configuration
PORT = "/dev/ttyAMA0"
BAUD = 9600
COMMANDE = bytes.fromhex("01 03 00 10 00 01 85 CF")
DELAI_REPONSE = 0.350       # secondes
NB_TENTATIVES = 3
PAUSE_TENTATIVES = 0.030  # secondes
PAUSE_MESURES = 0.200     # secondes


def crc16_modbus(donnees: bytes) -> int:
    crc = 0xFFFF
    for octet in donnees:
        crc ^= octet
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def lire_distance_mm(port: serial.Serial):
    """Retourne (distance_mm, diagnostic), ou (None, diagnostic)."""
    port.reset_input_buffer()
    port.write(COMMANDE)
    port.flush()

    tampon = bytearray()
    donnees_recues = bytearray()
    erreur_crc = False
    debut = time.monotonic()

    while time.monotonic() - debut < DELAI_REPONSE:
        octet = port.read(1)
        if not octet:
            continue

        donnees_recues.extend(octet)
        tampon.extend(octet)

        # Se synchroniser sur l'en-tête 01 03 02
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
        crc_calcule = crc16_modbus(trame[:5])

        if crc_recu != crc_calcule:
            erreur_crc = True
            continue

        distance_mm = (trame[3] << 8) | trame[4]
        if 0 < distance_mm <= 2000:
            return distance_mm, "OK"
        return None, f"Valeur hors plage : {distance_mm} mm"

    if erreur_crc:
        return None, "CRC invalide (vérifier les connexions UART)"
    if donnees_recues:
        return None, "Réponse non reconnue : " + donnees_recues.hex(" ").upper()
    return None, "Aucune réponse du capteur (port/fils/alimentation/débit)"


def main():
    print("=== TEST TOF53200 - RASPBERRY PI 4 ===", flush=True)
    print(f"Port : {PORT} | Débit : {BAUD} bauds", flush=True)
    print("Distance affichée en continu. Arrêt : Ctrl+C\n", flush=True)
    compteur = 0

    while True:
        try:
            with serial.Serial(PORT, baudrate=BAUD, bytesize=8,
                               parity=serial.PARITY_NONE, stopbits=1,
                               timeout=0.02, write_timeout=0.5) as tof:
                print("[OK] Port UART ouvert.", flush=True)

                while True:
                    compteur += 1
                    distance = None
                    diagnostic = ""
                    for essai in range(NB_TENTATIVES):
                        distance, diagnostic = lire_distance_mm(tof)
                        if distance is not None:
                            break
                        if essai < NB_TENTATIVES - 1:
                            time.sleep(PAUSE_TENTATIVES)

                    if distance is not None:
                        print(f"[{compteur}] Distance : {distance / 10:.1f} cm | "
                              f"{distance} mm", flush=True)
                    else:
                        print(f"[{compteur}] Mesure indisponible — {diagnostic}",
                              flush=True)
                    time.sleep(PAUSE_MESURES)

        except KeyboardInterrupt:
            print("\nTest arrêté par l'utilisateur.")
            return
        except (serial.SerialException, OSError) as exc:
            print(f"[ERREUR UART] {exc}", flush=True)
            print("Nouvel essai dans 2 secondes...", flush=True)
            time.sleep(2)


if __name__ == "__main__":
    main()
