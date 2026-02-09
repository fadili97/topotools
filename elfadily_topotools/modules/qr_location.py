"""
Module QR Code Localisation
- Cliquer sur la carte pour obtenir les coordonnées
- Génération automatique d'un QR code avec lien Google Maps
- Taille paramétrable du QR code
- Export en image PNG
"""

import os
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QSpinBox, QMessageBox, QFormLayout,
    QFileDialog, QSizePolicy
)
from qgis.PyQt.QtGui import QFont, QPixmap, QImage
from qgis.PyQt.QtCore import Qt, QSize
from qgis.core import (
    QgsProject, QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, QgsPointXY
)
from qgis.gui import QgsMapToolEmitPoint

from ..base_module import BaseModule


class QRLocationDialog(QDialog):
    """Dialogue pour afficher et paramétrer le QR code."""

    def __init__(self, lat, lon, parent=None):
        super().__init__(parent)
        self.lat = lat
        self.lon = lon
        self.qr_image = None
        self.setWindowTitle("QR Code - Localisation Google Maps")
        self.setMinimumWidth(400)
        self._setup_ui()
        self._generate_qr()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # === TITRE ===
        title = QLabel("QR Code - Localisation")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 6px;")
        layout.addWidget(title)

        # === INFOS COORDONNÉES ===
        grp_coords = QGroupBox("Coordonnées (WGS84)")
        coords_layout = QFormLayout()

        self.lbl_lat = QLabel(f"{self.lat:.6f}")
        self.lbl_lat.setTextInteractionFlags(Qt.TextSelectableByMouse)
        coords_layout.addRow("Latitude :", self.lbl_lat)

        self.lbl_lon = QLabel(f"{self.lon:.6f}")
        self.lbl_lon.setTextInteractionFlags(Qt.TextSelectableByMouse)
        coords_layout.addRow("Longitude :", self.lbl_lon)

        self.lbl_link = QLabel()
        self.lbl_link.setWordWrap(True)
        self.lbl_link.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse
        )
        self.lbl_link.setOpenExternalLinks(True)
        self.lbl_link.setStyleSheet("color: #3498db;")
        gmaps_url = f"https://www.google.com/maps?q={self.lat},{self.lon}"
        self.lbl_link.setText(f'<a href="{gmaps_url}">Ouvrir dans Google Maps</a>')
        coords_layout.addRow("Lien :", self.lbl_link)

        grp_coords.setLayout(coords_layout)
        layout.addWidget(grp_coords)

        # === OPTIONS QR CODE ===
        grp_options = QGroupBox("Options QR Code")
        opt_layout = QFormLayout()

        self.spn_size = QSpinBox()
        self.spn_size.setRange(100, 1000)
        self.spn_size.setValue(300)
        self.spn_size.setSuffix(" px")
        self.spn_size.valueChanged.connect(self._generate_qr)
        opt_layout.addRow("Taille :", self.spn_size)

        grp_options.setLayout(opt_layout)
        layout.addWidget(grp_options)

        # === APERÇU QR CODE ===
        grp_preview = QGroupBox("Aperçu")
        preview_layout = QVBoxLayout()

        self.lbl_qr = QLabel()
        self.lbl_qr.setAlignment(Qt.AlignCenter)
        self.lbl_qr.setMinimumSize(320, 320)
        self.lbl_qr.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_qr.setStyleSheet(
            "QLabel { background-color: white; border: 2px solid #bdc3c7; "
            "border-radius: 8px; padding: 10px; }"
        )
        preview_layout.addWidget(self.lbl_qr)

        grp_preview.setLayout(preview_layout)
        layout.addWidget(grp_preview)

        # === BOUTONS ===
        h_buttons = QHBoxLayout()
        h_buttons.addStretch()

        btn_copy = QPushButton("Copier le lien")
        btn_copy.clicked.connect(self._copy_link)
        h_buttons.addWidget(btn_copy)

        btn_export = QPushButton("Exporter PNG")
        btn_export.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; "
            "font-weight: bold; padding: 8px 20px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #2ecc71; }"
        )
        btn_export.clicked.connect(self._export_qr)
        h_buttons.addWidget(btn_export)

        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        h_buttons.addWidget(btn_close)

        layout.addLayout(h_buttons)

        # === COPYRIGHT ===
        lbl_copyright = QLabel("© ELFADILY GEOCONSEIL — Tous droits réservés")
        lbl_copyright.setAlignment(Qt.AlignCenter)
        lbl_copyright.setStyleSheet("color: #aaa; font-size: 10px; padding-top: 2px;")
        layout.addWidget(lbl_copyright)

    def _generate_qr(self):
        """Génère le QR code avec le lien Google Maps via APIs en ligne (avec fallback)."""
        from qgis.PyQt.QtNetwork import QNetworkAccessManager, QNetworkRequest
        from qgis.PyQt.QtCore import QUrl, QEventLoop
        from urllib.parse import quote

        gmaps_url = f"https://www.google.com/maps?q={self.lat},{self.lon}"
        size = self.spn_size.value()
        encoded_url = quote(gmaps_url, safe='')

        # Liste d'APIs de secours (fallback) - si une échoue, essaie la suivante
        api_urls = [
            # API 1: QRServer.com (très fiable)
            f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={gmaps_url}",
            # API 2: goQR.me (backup)
            f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&format=png&data={encoded_url}",
            # API 3: QuickChart.io (backup)
            f"https://quickchart.io/qr?size={size}&text={encoded_url}",
        ]

        # Afficher un message de chargement
        self.lbl_qr.setText("⏳ Génération du QR code...")
        self.lbl_qr.setStyleSheet(
            "QLabel { color: #3498db; background-color: #ebf5fb; "
            "border: 2px solid #3498db; border-radius: 8px; padding: 20px; }"
        )

        # Essayer chaque API jusqu'à ce qu'une fonctionne
        manager = QNetworkAccessManager()

        for i, api_url in enumerate(api_urls):
            request = QNetworkRequest(QUrl(api_url))
            request.setRawHeader(b"User-Agent", b"QGIS-TopoTools/1.0")

            # Créer une boucle d'événements pour attendre la réponse
            loop = QEventLoop()
            reply = manager.get(request)
            reply.finished.connect(loop.quit)
            loop.exec_()

            # Si pas d'erreur, essayer de charger l'image
            if not reply.error():
                image_data = reply.readAll()
                qimage = QImage()
                qimage.loadFromData(image_data)

                if not qimage.isNull():
                    # Succès! Afficher l'image
                    pixmap = QPixmap.fromImage(qimage)
                    self.qr_image = qimage
                    self.lbl_qr.setPixmap(pixmap)
                    self.lbl_qr.setStyleSheet(
                        "QLabel { background-color: white; border: 2px solid #27ae60; "
                        "border-radius: 8px; padding: 10px; }"
                    )
                    return  # Terminé avec succès!

        # Si toutes les APIs ont échoué
        self.lbl_qr.setText(
            "❌ Erreur de génération\n\n"
            "Impossible de générer le QR code.\n"
            "Vérifiez votre connexion internet.\n\n"
            "Vous pouvez toujours copier le lien\n"
            "et utiliser un générateur en ligne."
        )
        self.lbl_qr.setStyleSheet(
            "QLabel { color: #e74c3c; background-color: #fdecea; "
            "border: 2px solid #e74c3c; border-radius: 8px; padding: 20px; }"
        )

    def _copy_link(self):
        """Copie le lien Google Maps dans le presse-papier."""
        from qgis.PyQt.QtWidgets import QApplication
        gmaps_url = f"https://www.google.com/maps?q={self.lat},{self.lon}"
        QApplication.clipboard().setText(gmaps_url)
        QMessageBox.information(
            self, "Copié",
            "Lien Google Maps copié dans le presse-papier."
        )

    def _export_qr(self):
        """Exporte le QR code en image PNG."""
        if not self.qr_image:
            QMessageBox.warning(
                self, "Erreur",
                "Aucun QR code à exporter."
            )
            return

        default_name = f"qr_location_{self.lat:.4f}_{self.lon:.4f}.png"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le QR code",
            os.path.expanduser(f"~/{default_name}"),
            "PNG (*.png)"
        )

        if file_path:
            # Redimensionner l'image à la taille souhaitée
            size = self.spn_size.value()
            scaled_img = self.qr_image.scaled(
                size, size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            if scaled_img.save(file_path, "PNG"):
                QMessageBox.information(
                    self, "Succès",
                    f"QR code exporté :\n{file_path}\nTaille : {size}x{size} px"
                )
            else:
                QMessageBox.warning(
                    self, "Erreur",
                    "Impossible d'enregistrer le fichier."
                )


class QRLocationMapTool(QgsMapToolEmitPoint):
    """Outil de carte pour capturer les clics."""

    def __init__(self, canvas, iface):
        super().__init__(canvas)
        self.canvas = canvas
        self.iface = iface

    def canvasReleaseEvent(self, event):
        """Appelé quand l'utilisateur clique sur la carte."""
        # Obtenir le point cliqué dans le CRS du canevas
        point = self.toMapCoordinates(event.pos())

        # Transformer en WGS84 (EPSG:4326) pour Google Maps
        canvas_crs = self.canvas.mapSettings().destinationCrs()
        wgs84_crs = QgsCoordinateReferenceSystem("EPSG:4326")

        if canvas_crs != wgs84_crs:
            transform = QgsCoordinateTransform(
                canvas_crs,
                wgs84_crs,
                QgsProject.instance()
            )
            point_wgs84 = transform.transform(point)
        else:
            point_wgs84 = point

        lat = point_wgs84.y()
        lon = point_wgs84.x()

        # Afficher le dialogue avec le QR code
        dlg = QRLocationDialog(lat, lon, self.iface.mainWindow())
        dlg.exec_()

        # Désactiver l'outil après utilisation
        self.canvas.unsetMapTool(self)


class QRLocationModule(BaseModule):
    """Module pour générer des QR codes de localisation."""

    MODULE_NAME = "QR Localisation"
    MODULE_ICON = "qr.svg"
    MODULE_TOOLTIP = "Créer un QR code Google Maps depuis un point de la carte"

    def __init__(self, iface, toolbar, plugin_dir):
        super().__init__(iface, toolbar, plugin_dir)
        self.map_tool = None

    def run(self):
        """Active l'outil de sélection sur la carte."""
        # Créer l'outil de carte
        self.map_tool = QRLocationMapTool(
            self.iface.mapCanvas(),
            self.iface
        )

        # Activer l'outil
        self.iface.mapCanvas().setMapTool(self.map_tool)

        # Message dans la barre de status
        self.iface.mainWindow().statusBar().showMessage(
            "🗺️ Cliquez sur la carte pour générer un QR code Google Maps",
            5000  # 5 secondes
        )

    def unload(self):
        """Nettoie le module."""
        if self.map_tool:
            self.iface.mapCanvas().unsetMapTool(self.map_tool)
            self.map_tool = None
        super().unload()
