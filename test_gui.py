import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QLabel, QPushButton
)

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("WaveletBC7 Research Studio")
window.resize(500, 300)

layout = QVBoxLayout(window)

title = QLabel("WaveletBC7 Research Studio")
button = QPushButton("PySide6 is working!")

layout.addWidget(title)
layout.addWidget(button)

window.show()
sys.exit(app.exec())