#!/usr/bin/env python3
"""Test continu TOF53200 par UART/Modbus RTU sur Raspberry Pi 5.

Commande de lecture experimentee: esclave 1, fonction 03, registre 0x0010.
Ce registre est utilise par des ToF Modbus similaires, mais n'est pas confirme
pour toutes les revisions de TOF53200. Aucun resultat n'est invente.
"""
import argparse
import time

try:
    import serial
except ImportError:
    raise SystemExit("Bibliotheque absente. Installer: sudo apt install python3-serial")


def crc16_modbus(data):
    crc = 0xFFFF
    for octet in data:
        crc ^= octet
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def fabriquer_requete():
    contenu = bytes([0x01, 0x03, 0x00, 0x10, 0x00, 0x01])
    crc = crc16_modbus(contenu)
    return contenu + crc.to_bytes(2, 'little')


def decoder(buffer):
    """Retourne (etat, mm ou message), ou None si aucune trame reconnue."""
    for i in range(len(buffer)):
        if buffer[i] != 0x01 or i + 2 > len(buffer):
            continue
        if i + 2 > len(buffer):
            continue
        fonction = buffer[i + 1]
        if fonction == 0x83 and i + 5 <= len(buffer):
            trame = bytes(buffer[i:i+5])
            if crc16_modbus(trame[:-2]) == int.from_bytes(trame[-2:], 'little'):
                return ("erreur", f"Exception Modbus 0x{trame[2]:02X} (registre ou commande refuse)")
        if fonction == 0x03 and i + 3 <= len(buffer):
            longueur = buffer[i + 2]
            total = 3 + longueur + 2
            if longueur > 32 or i + total > len(buffer):
                continue
            trame = bytes(buffer[i:i+total])
            if crc16_modbus(trame[:-2]) != int.from_bytes(trame[-2:], 'little'):
                continue
            if longueur != 2:
                return ("erreur", f"Longueur de donnees inattendue: {longueur}")
            return ("distance", int.from_bytes(trame[3:5], 'big'))
    return None


def main():
    p = argparse.ArgumentParser(description="Test TOF53200 par UART (mode Modbus)")
    p.add_argument('--port', default='/dev/ttyAMA0', help='Port UART du Raspberry Pi 5')
    p.add_argument('--baud', default=115200, type=int, help='Debit UART')
    args = p.parse_args()

    requete = fabriquer_requete()
    print("=== TOF53200 - TEST DE DISTANCE EN CONTINU ===")
    print(f"Port : {args.port} | Debit : {args.baud} bauds")
    print("Mode d'essai : Modbus RTU, registre 0x0010 (a confirmer selon module)")
    print("Requete envoyee :", requete.hex(' ').upper())
    print("Arret : Ctrl+C\n")

    try:
        with serial.Serial(args.port, args.baud, timeout=0.05) as port:
            numero = 0
            while True:
                debut = time.monotonic()
                numero += 1
                try:
                    port.reset_input_buffer()
                    port.write(requete)
                    port.flush()
                    reponse = bytearray()
                    delai = time.monotonic() + 0.5
                    resultat = None
                    while time.monotonic() < delai:
                        paquet = port.read(max(1, min(port.in_waiting, 64)))
                        if paquet:
                            reponse.extend(paquet)
                            resultat = decoder(reponse)
                            if resultat is not None:
                                break

                    print(f"[{numero}] ", end='')
                    if resultat and resultat[0] == "distance":
                        mm = resultat[1]
                        if 0 < mm <= 2000:
                            print(f"Distance : {mm / 10:.1f} cm ({mm} mm)")
                        else:
                            print(f"Valeur hors plage / invalide : {mm} mm")
                    elif resultat:
                        print(resultat[1])
                    elif reponse:
                        print("Trame recue mais non reconnue :", reponse.hex(' ').upper())
                    else:
                        print("Aucune reponse UART (verifier TXD/RXD, port, mode et protocole)")
                except serial.SerialException as e:
                    print("Erreur UART pendant la lecture :", e)
                time.sleep(max(0, 1.0 - (time.monotonic() - debut)))
    except serial.SerialException as e:
        print(f"Impossible d'ouvrir {args.port}: {e}")
        print("Verifier l'activation d'UART0 (overlay uart0-pi5) et le port disponible.")
    except KeyboardInterrupt:
        print("\nTest arrete manuellement.")


if __name__ == '__main__':
    main()
