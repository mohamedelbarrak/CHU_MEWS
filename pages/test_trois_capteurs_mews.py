"""Test de 5 secondes pour Raspberry Pi 5.
Matériel visé : GY-614V3 UART + TOF10120 I2C + SDP810 I2C.
Ne pas brancher deux sorties UART TX sur le même GPIO15.
"""
import time
import statistics

try:
    import serial
    from smbus2 import SMBus, i2c_msg
except ImportError as exc:
    raise SystemExit("Installez les modules : pip install pyserial smbus2") from exc

PORT_TEMPERATURE = "/dev/ttyAMA0"  # UART0 sur GPIO14/15 (Pi 5, si active)
DEBIT_TEMPERATURE = 9600
I2C_BUS = 1
ADRESSE_TOF10120 = 0x52
ADRESSE_SDP810 = 0x25
DUREE_S = 5
SEUIL_RESPIRATION_PA = 0.5  # ajustable apres essais
INVERSER_RESPIRATION = False  # True si les tuyaux inversent inspiration/expiration


def crc8_sensirion(octets):
    crc = 0xFF
    for octet in octets:
        crc ^= octet
        for _ in range(8):
            crc = ((crc << 1) ^ 0x31) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


class TemperatureUART:
    def __init__(self):
        self.port = None
        self.buffer = bytearray()
        self.valeurs = None
        self.derniere_reception = 0.0
        self.erreur = "en attente"
        try:
            self.port = serial.Serial(PORT_TEMPERATURE, DEBIT_TEMPERATURE, timeout=0)
        except (OSError, serial.SerialException) as exc:
            self.erreur = str(exc)

    def poll(self):
        if self.port is None:
            return
        try:
            n = self.port.in_waiting
            if n:
                self.buffer.extend(self.port.read(n))
            if len(self.buffer) > 256:
                self.buffer = self.buffer[-256:]
            while len(self.buffer) >= 12:
                debut = self.buffer.find(b"\xA4\x03")
                if debut < 0:
                    self.buffer.clear()
                    break
                if debut:
                    del self.buffer[:debut]
                if len(self.buffer) < 12:
                    break
                frame = self.buffer[:12]
                if (frame[2] == 0x07 and frame[3] == 0x07
                        and (sum(frame[:11]) & 0xFF) == frame[11]):
                    to = (frame[5] * 256 + frame[6]) / 100.0
                    ta = (frame[7] * 256 + frame[8]) / 100.0
                    bo = (frame[9] * 256 + frame[10]) / 100.0
                    self.valeurs = (to, ta, bo)
                    self.derniere_reception = time.monotonic()
                    self.erreur = ""
                    del self.buffer[:12]
                else:
                    del self.buffer[0]
        except (OSError, serial.SerialException) as exc:
            self.erreur = str(exc)
            self.port = None

    def texte(self):
        if self.valeurs and (time.monotonic() - self.derniere_reception) < 2:
            to, ta, bo = self.valeurs
            return f"objet {to:.2f} °C | ambiante {ta:.2f} °C | corps estimé {bo:.2f} °C"
        return "indisponible (UART : " + self.erreur + ")"

    def fermer(self):
        if self.port:
            self.port.close()


class SDP810:
    def __init__(self, bus):
        self.bus = bus
        self.pret = False
        self.erreur = "en attente"
        self.zero = 0.0
        self.filtre = 0.0
        self.pression = None
        self.phase = 0
        self.nombre = 0
        self.dernier_cycle = -100.0
        try:
            # Stopper une ancienne session, puis mesurer la pression differentielle.
            self.bus.write_i2c_block_data(ADRESSE_SDP810, 0x3F, [0xF9])
            time.sleep(0.025)
            self.bus.write_i2c_block_data(ADRESSE_SDP810, 0x36, [0x15])
            time.sleep(0.025)
            self.pret = True
            self.erreur = ""
        except OSError as exc:
            self.erreur = str(exc)

    def lire_pa(self):
        if not self.pret:
            return None
        try:
            msg = i2c_msg.read(ADRESSE_SDP810, 9)
            self.bus.i2c_rdwr(msg)
            d = list(msg)
            if (crc8_sensirion(d[0:2]) != d[2]
                    or crc8_sensirion(d[6:8]) != d[8]):
                raise ValueError("CRC SDP810 incorrect")
            brut = (d[0] << 8) | d[1]
            if brut >= 32768:
                brut -= 65536
            facteur = (d[6] << 8) | d[7]
            if facteur == 0:
                raise ValueError("facteur SDP810 nul")
            self.erreur = ""
            self.pression = brut / facteur
            return self.pression
        except (OSError, ValueError) as exc:
            self.erreur = str(exc)
            return None

    def calibrer(self):
        if not self.pret:
            return
        print("Calibration respiration (~0,7 s) : laissez le masque au repos...")
        lectures = []
        fin = time.monotonic() + 0.7
        while time.monotonic() < fin:
            v = self.lire_pa()
            if v is not None:
                lectures.append(v)
            time.sleep(0.025)
        if lectures:
            self.zero = statistics.median(lectures)
            print(f"Zéro SDP810 : {self.zero:+.2f} Pa")
        else:
            print("SDP810 : pas de mesure valide pendant la calibration.")

    def traiter(self, maintenant):
        valeur = self.lire_pa()
        if valeur is None:
            return
        delta = valeur - self.zero
        if INVERSER_RESPIRATION:
            delta = -delta
        self.filtre = 0.75 * self.filtre + 0.25 * delta
        # Un cycle = franchissement negatif puis positif.
        if self.phase == 0 and self.filtre < -SEUIL_RESPIRATION_PA:
            self.phase = 1
        elif (self.phase == 1 and self.filtre > SEUIL_RESPIRATION_PA
              and maintenant - self.dernier_cycle >= 1.0):
            self.nombre += 1
            self.dernier_cycle = maintenant
            self.phase = 0

    def fermer(self):
        if self.pret:
            try:
                self.bus.write_i2c_block_data(ADRESSE_SDP810, 0x3F, [0xF9])
            except OSError:
                pass


def lire_distance_cm(bus):
    """TOF10120 I2C, 0x52. Ne convient pas au TOF53200 en UART."""
    try:
        bus.write_byte(ADRESSE_TOF10120, 0x00)
        time.sleep(0.002)
        msg = i2c_msg.read(ADRESSE_TOF10120, 2)
        bus.i2c_rdwr(msg)
        d = list(msg)
        mm = (d[0] << 8) | d[1]
        if mm in (0, 65535):
            return "mesure invalide"
        cm = mm / 10.0
        if not 10 <= cm <= 180:
            return f"{cm:.1f} cm (hors plage fiable 10–180 cm)"
        return f"{cm:.1f} cm"
    except OSError as exc:
        return f"indisponible (I2C : {exc})"


def main():
    print("=== TEST MEWS : 3 capteurs, 5 secondes ===")
    print("Température : GY-614V3 UART | Distance : TOF10120 I2C | Respiration : SDP810 I2C")
    temp = TemperatureUART()
    try:
        bus = SMBus(I2C_BUS)
    except OSError as exc:
        temp.fermer()
        raise SystemExit(f"Impossible d'ouvrir I2C /dev/i2c-{I2C_BUS}: {exc}")

    resp = SDP810(bus)
    try:
        resp.calibrer()
        debut = time.monotonic()
        prochain_echantillon = debut
        for seconde in range(1, DUREE_S + 1):
            limite = debut + seconde
            while time.monotonic() < limite:
                maintenant = time.monotonic()
                temp.poll()
                if maintenant >= prochain_echantillon:
                    resp.traiter(maintenant)
                    prochain_echantillon += 0.04  # ~25 lectures par seconde
                time.sleep(0.005)

            distance = lire_distance_cm(bus)
            print(f"\n[{seconde}/5 secondes]")
            print("  Température  :", temp.texte())
            print("  Distance     :", distance)
            if resp.pret:
                print(f"  Respiration  : {resp.nombre} cycle(s) en {seconde} s"
                      f" | pression {resp.filtre:+.2f} Pa"
                      + (f" | erreur : {resp.erreur}" if resp.erreur else ""))
            else:
                print("  Respiration  : indisponible (" + resp.erreur + ")")
        print("\n=== TEST TERMINÉ ===")
        print(f"Respirations complètes détectées pendant 5 s : {resp.nombre}")
    finally:
        resp.fermer()
        bus.close()
        temp.fermer()


if __name__ == "__main__":
    main()
