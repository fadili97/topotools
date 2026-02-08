"""
Module Points → Géométrie (Polygone / Polyligne / Points)
- Coller des coordonnées depuis n'importe quelle source
- Choix du séparateur (espace, ;, tab, virgule, etc.)
- Choix du système de coordonnées
- Prévisualisation et export
"""

import os
import re
import datetime
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QComboBox, QCheckBox, QSpinBox, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QFormLayout, QFrame, QTextEdit,
    QRadioButton, QButtonGroup, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QWidget
)
from qgis.PyQt.QtGui import QFont, QColor
from qgis.PyQt.QtCore import Qt
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsField, QgsFields, QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, QgsWkbTypes, QgsVectorFileWriter,
    QgsMarkerSymbol, QgsLineSymbol, QgsFillSymbol
)
from qgis.PyQt.QtCore import QVariant

from ..base_module import BaseModule


class PointsToGeometryDialog(QDialog):
    """Dialogue pour convertir des points en géométrie."""

    SEPARATORS = {
        "Espace": r"\s+",
        "Point-virgule (;)": ";",
        "Virgule (,)": ",",
        "Tabulation": "\t",
        "Pipe (|)": r"\|",
        "Personnalisé": None,
    }

    COMMON_CRS = [
        ("WGS 84 (GPS) - EPSG:4326", "EPSG:4326"),
        ("WGS 84 / UTM zone 28N - EPSG:32628", "EPSG:32628"),
        ("WGS 84 / UTM zone 29N - EPSG:32629", "EPSG:32629"),
        ("WGS 84 / UTM zone 30N - EPSG:32630", "EPSG:32630"),
        ("Merchich / Nord Maroc - EPSG:26191", "EPSG:26191"),
        ("Merchich / Sud Maroc - EPSG:26192", "EPSG:26192"),
        ("Merchich / Sahara Nord - EPSG:26194", "EPSG:26194"),
        ("Merchich / Sahara Sud - EPSG:26195", "EPSG:26195"),
        ("Autre (sélection manuelle)...", None),
    ]

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.parsed_points = []
        self.setWindowTitle("📐 Points → Géométrie")
        self.setMinimumSize(700, 600)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Points → Polygone / Polyligne / Points")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 8px;")
        layout.addWidget(title)

        splitter = QSplitter(Qt.Horizontal)

        # === PANNEAU GAUCHE : Saisie ===
        left = QWidget()
        left_layout = QVBoxLayout(left)

        # Zone de texte pour coller les points
        grp_input = QGroupBox("Coller les coordonnées")
        inp_layout = QVBoxLayout()

        hint = QLabel(
            "Collez vos points (un par ligne). Format : N° X Y [Z]\n"
            "Le numéro de point est optionnel."
        )
        hint.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        inp_layout.addWidget(hint)

        self.txt_points = QTextEdit()
        self.txt_points.setPlaceholderText(
            "Exemples :\n"
            "1 234567.89 345678.90\n"
            "2 234568.12 345679.45 120.5\n"
            "ou sans numéro :\n"
            "234567.89 345678.90\n"
            "234568.12 345679.45"
        )
        self.txt_points.setFont(QFont("Consolas", 10))
        inp_layout.addWidget(self.txt_points)

        grp_input.setLayout(inp_layout)
        left_layout.addWidget(grp_input)

        # Options de parsing
        grp_options = QGroupBox("Options")
        opt_layout = QFormLayout()

        # Séparateur
        self.cmb_separator = QComboBox()
        self.cmb_separator.addItems(self.SEPARATORS.keys())
        self.cmb_separator.currentTextChanged.connect(self._on_separator_changed)
        opt_layout.addRow("Séparateur :", self.cmb_separator)

        self.txt_custom_sep = QLineEdit()
        self.txt_custom_sep.setPlaceholderText("Séparateur personnalisé")
        self.txt_custom_sep.setEnabled(False)
        opt_layout.addRow("Personnalisé :", self.txt_custom_sep)

        # Ordre des colonnes
        self.cmb_col_order = QComboBox()
        self.cmb_col_order.addItems([
            "N° X Y [Z]",
            "X Y [Z]",
            "N° Y X [Z]",
            "Y X [Z]",
        ])
        opt_layout.addRow("Ordre colonnes :", self.cmb_col_order)

        # CRS
        self.cmb_crs = QComboBox()
        for label, code in self.COMMON_CRS:
            self.cmb_crs.addItem(label, code)
        self.cmb_crs.currentIndexChanged.connect(self._on_crs_changed)
        opt_layout.addRow("Système coord. :", self.cmb_crs)

        # Type de géométrie
        h_geom = QHBoxLayout()
        self.rb_polygon = QRadioButton("Polygone")
        self.rb_polyline = QRadioButton("Polyligne")
        self.rb_points = QRadioButton("Points")
        self.rb_polygon.setChecked(True)
        h_geom.addWidget(self.rb_polygon)
        h_geom.addWidget(self.rb_polyline)
        h_geom.addWidget(self.rb_points)
        opt_layout.addRow("Géométrie :", h_geom)

        # Fermer le polygone automatiquement
        self.chk_close = QCheckBox("Fermer automatiquement le polygone")
        self.chk_close.setChecked(True)
        opt_layout.addRow("", self.chk_close)

        # Numérotation des sommets
        self.chk_labels = QCheckBox("Afficher les numéros de sommets")
        self.chk_labels.setChecked(True)
        opt_layout.addRow("", self.chk_labels)

        grp_options.setLayout(opt_layout)
        left_layout.addWidget(grp_options)

        # Bouton parser
        btn_parse = QPushButton("🔄 Analyser les points")
        btn_parse.setStyleSheet(
            "QPushButton { background-color: #3498db; color: white; "
            "font-weight: bold; padding: 6px; border-radius: 4px; }"
        )
        btn_parse.clicked.connect(self._parse_points)
        left_layout.addWidget(btn_parse)

        splitter.addWidget(left)

        # === PANNEAU DROIT : Aperçu ===
        right = QWidget()
        right_layout = QVBoxLayout(right)

        grp_preview = QGroupBox("Aperçu des points")
        prev_layout = QVBoxLayout()

        self.lbl_count = QLabel("Aucun point analysé")
        self.lbl_count.setStyleSheet("font-weight: bold; color: #2c3e50;")
        prev_layout.addWidget(self.lbl_count)

        self.table_points = QTableWidget()
        self.table_points.setColumnCount(4)
        self.table_points.setHorizontalHeaderLabels(["N°", "X", "Y", "Z"])
        self.table_points.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_points.setAlternatingRowColors(True)
        prev_layout.addWidget(self.table_points)

        grp_preview.setLayout(prev_layout)
        right_layout.addWidget(grp_preview)

        splitter.addWidget(right)
        splitter.setSizes([400, 300])
        layout.addWidget(splitter)

        # === BOUTONS ===
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        layout.addWidget(sep)

        h_buttons = QHBoxLayout()
        h_buttons.addStretch()

        btn_add_layer = QPushButton("➕ Ajouter au projet")
        btn_add_layer.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; "
            "font-weight: bold; padding: 8px 20px; border-radius: 4px; }"
        )
        btn_add_layer.clicked.connect(self._add_to_project)
        h_buttons.addWidget(btn_add_layer)

        btn_save = QPushButton("💾 Enregistrer Shapefile")
        btn_save.clicked.connect(self._save_shapefile)
        h_buttons.addWidget(btn_save)

        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.reject)
        h_buttons.addWidget(btn_close)

        layout.addLayout(h_buttons)

    def _on_separator_changed(self, text):
        self.txt_custom_sep.setEnabled(text == "Personnalisé")

    def _on_crs_changed(self, index):
        if self.cmb_crs.currentData() is None:
            from qgis.gui import QgsProjectionSelectionDialog
            dlg = QgsProjectionSelectionDialog(self)
            if dlg.exec_():
                crs = dlg.crs()
                # Remplacer le dernier item
                self.cmb_crs.setItemText(index, f"{crs.description()} - {crs.authid()}")
                self.cmb_crs.setItemData(index, crs.authid())

    def _get_separator_pattern(self):
        """Retourne le pattern regex du séparateur."""
        text = self.cmb_separator.currentText()
        if text == "Personnalisé":
            custom = self.txt_custom_sep.text()
            return re.escape(custom) if custom else r"\s+"
        return self.SEPARATORS[text]

    def _parse_points(self):
        """Analyse le texte et extrait les points."""
        raw = self.txt_points.toPlainText().strip()
        if not raw:
            QMessageBox.warning(self, "Attention", "Aucun texte à analyser.")
            return

        sep = self._get_separator_pattern()
        col_order = self.cmb_col_order.currentText()
        has_num = "N°" in col_order
        is_yx = "Y X" in col_order

        self.parsed_points = []
        errors = []

        for i, line in enumerate(raw.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = re.split(sep, line)

            try:
                if has_num:
                    num = parts[0]
                    x_str, y_str = parts[1], parts[2]
                    z_str = parts[3] if len(parts) > 3 else "0"
                else:
                    num = str(len(self.parsed_points) + 1)
                    x_str, y_str = parts[0], parts[1]
                    z_str = parts[2] if len(parts) > 2 else "0"

                x = float(x_str.replace(",", "."))
                y = float(y_str.replace(",", "."))
                z = float(z_str.replace(",", "."))

                if is_yx:
                    x, y = y, x

                self.parsed_points.append({
                    "num": num, "x": x, "y": y, "z": z
                })
            except (IndexError, ValueError) as e:
                errors.append(f"Ligne {i}: {line} → {str(e)}")

        # Mise à jour du tableau
        self.table_points.setRowCount(len(self.parsed_points))
        for row, pt in enumerate(self.parsed_points):
            self.table_points.setItem(row, 0, QTableWidgetItem(pt["num"]))
            self.table_points.setItem(row, 1, QTableWidgetItem(f"{pt['x']:.3f}"))
            self.table_points.setItem(row, 2, QTableWidgetItem(f"{pt['y']:.3f}"))
            self.table_points.setItem(row, 3, QTableWidgetItem(f"{pt['z']:.3f}"))

        msg = f"{len(self.parsed_points)} points analysés"
        if errors:
            msg += f" ({len(errors)} erreurs)"
        self.lbl_count.setText(msg)

        if errors:
            QMessageBox.warning(
                self, "Erreurs de parsing",
                "Lignes ignorées :\n" + "\n".join(errors[:10])
            )

    def _create_layer(self):
        """Crée la couche vecteur à partir des points parsés."""
        if not self.parsed_points:
            QMessageBox.warning(self, "Attention", "Analysez d'abord les points.")
            return None

        crs_code = self.cmb_crs.currentData()
        if not crs_code:
            crs_code = "EPSG:4326"
        crs = QgsCoordinateReferenceSystem(crs_code)

        points = [QgsPointXY(p["x"], p["y"]) for p in self.parsed_points]

        if self.rb_polygon.isChecked():
            geom_type = "Polygon"
            layer = QgsVectorLayer(f"{geom_type}?crs={crs_code}", "Points_Polygone", "memory")
            pr = layer.dataProvider()
            pr.addAttributes([
                QgsField("id", QVariant.Int),
                QgsField("surface_m2", QVariant.Double),
                QgsField("perimetre_m", QVariant.Double),
            ])
            layer.updateFields()

            feat = QgsFeature()
            geom = QgsGeometry.fromPolygonXY([points])
            feat.setGeometry(geom)
            feat.setAttributes([
                1,
                round(geom.area(), 2),
                round(geom.length(), 2),
            ])
            pr.addFeatures([feat])
            layer.updateExtents()

            # Style
            symbol = QgsFillSymbol.createSimple({
                'color': '52,152,219,60',
                'outline_color': '#e74c3c',
                'outline_width': '0.8'
            })
            layer.renderer().setSymbol(symbol)

        elif self.rb_polyline.isChecked():
            geom_type = "LineString"
            layer = QgsVectorLayer(f"{geom_type}?crs={crs_code}", "Points_Polyligne", "memory")
            pr = layer.dataProvider()
            pr.addAttributes([
                QgsField("id", QVariant.Int),
                QgsField("longueur_m", QVariant.Double),
            ])
            layer.updateFields()

            feat = QgsFeature()
            geom = QgsGeometry.fromPolylineXY(points)
            feat.setGeometry(geom)
            feat.setAttributes([1, round(geom.length(), 2)])
            pr.addFeatures([feat])
            layer.updateExtents()

            symbol = QgsLineSymbol.createSimple({
                'color': '#e74c3c',
                'width': '0.8'
            })
            layer.renderer().setSymbol(symbol)

        else:  # Points
            geom_type = "Point"
            layer = QgsVectorLayer(f"{geom_type}?crs={crs_code}", "Points_Import", "memory")
            pr = layer.dataProvider()
            pr.addAttributes([
                QgsField("num", QVariant.String),
                QgsField("x", QVariant.Double),
                QgsField("y", QVariant.Double),
                QgsField("z", QVariant.Double),
            ])
            layer.updateFields()

            features = []
            for p in self.parsed_points:
                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(p["x"], p["y"])))
                feat.setAttributes([p["num"], p["x"], p["y"], p["z"]])
                features.append(feat)
            pr.addFeatures(features)
            layer.updateExtents()

        # Ajouter les sommets comme couche séparée si polygon/polyline
        if geom_type != "Point" and self.chk_labels.isChecked():
            pts_layer = QgsVectorLayer(f"Point?crs={crs_code}", "Sommets", "memory")
            pr2 = pts_layer.dataProvider()
            pr2.addAttributes([
                QgsField("num", QVariant.String),
                QgsField("x", QVariant.Double),
                QgsField("y", QVariant.Double),
                QgsField("z", QVariant.Double),
            ])
            pts_layer.updateFields()

            features = []
            for p in self.parsed_points:
                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(p["x"], p["y"])))
                feat.setAttributes([p["num"], p["x"], p["y"], p["z"]])
                features.append(feat)
            pr2.addFeatures(features)
            pts_layer.updateExtents()

            # Labels
            from qgis.core import QgsPalLayerSettings, QgsVectorLayerSimpleLabeling
            label_settings = QgsPalLayerSettings()
            label_settings.fieldName = "num"
            label_settings.isExpression = False
            labeling = QgsVectorLayerSimpleLabeling(label_settings)
            pts_layer.setLabeling(labeling)
            pts_layer.setLabelsEnabled(True)

            QgsProject.instance().addMapLayer(pts_layer)

        return layer

    def _add_to_project(self):
        """Ajoute la couche au projet QGIS."""
        layer = self._create_layer()
        if layer:
            QgsProject.instance().addMapLayer(layer)
            self.iface.mapCanvas().setExtent(layer.extent())
            self.iface.mapCanvas().refresh()
            QMessageBox.information(self, "Succès", "Couche ajoutée au projet.")

    def _save_shapefile(self):
        """Sauvegarde en shapefile."""
        layer = self._create_layer()
        if not layer:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le Shapefile",
            os.path.expanduser("~/points_geometry.shp"),
            "Shapefile (*.shp)"
        )
        if not file_path:
            return

        crs_code = self.cmb_crs.currentData() or "EPSG:4326"
        crs = QgsCoordinateReferenceSystem(crs_code)

        error = QgsVectorFileWriter.writeAsVectorFormat(
            layer, file_path, "UTF-8", crs, "ESRI Shapefile"
        )

        if error[0] == QgsVectorFileWriter.NoError:
            # Charger le shapefile sauvegardé
            saved_layer = QgsVectorLayer(file_path, os.path.basename(file_path), "ogr")
            QgsProject.instance().addMapLayer(saved_layer)
            QMessageBox.information(self, "Succès", f"Shapefile enregistré :\n{file_path}")
        else:
            QMessageBox.warning(self, "Erreur", f"Erreur d'écriture : {error[1]}")


class PointsToGeometryModule(BaseModule):
    MODULE_NAME = "Points → Géométrie"
    MODULE_ICON = "points.png"
    MODULE_TOOLTIP = "📐 Points → Polygone / Polyligne"

    def run(self):
        dlg = PointsToGeometryDialog(self.iface, self.iface.mainWindow())
        dlg.exec_()
