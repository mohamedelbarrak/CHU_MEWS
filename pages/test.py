from PySide6.QtGui import QGuiApplication

screen = QGuiApplication.primaryScreen()

print("Résolution :", screen.size())
print("Résolution disponible :", screen.availableGeometry().size())
print("Facteur DPI :", screen.devicePixelRatio())
print("DPI physique :", screen.physicalDotsPerInch())