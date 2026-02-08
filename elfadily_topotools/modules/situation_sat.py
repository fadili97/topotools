"""
Module Situation Satellite
- Capture de la vue courante (le basemap satellite est déjà ouvert par l'équipe)
- Deux modes : capture simple (PNG/JPEG) ou PDF avec cartouche
- Pas de gestion de source satellite - on utilise ce qui est déjà affiché
"""

import os
import datetime
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QComboBox, QCheckBox, QSpinBox, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QFormLayout, QFrame,
    QRadioButton, QWidget, QSizePolicy
)
from qgis.PyQt.QtGui import QFont
from qgis.PyQt.QtCore import Qt, QSize, QEventLoop, QSettings
from qgis.core import (
    QgsProject, QgsVectorLayer,
    QgsCoordinateTransform, QgsRectangle,
    QgsLayoutExporter, QgsPrintLayout,
    QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutItemPicture, QgsLayoutItemShape,
    QgsLayoutPoint, QgsLayoutSize, QgsUnitTypes,
    QgsMapSettings, QgsMapRendererParallelJob,
    QgsFillSymbol, QgsLayoutMeasurement
)

from ..base_module import BaseModule


class SituationSatDialog(QDialog):
    """Dialogue pour la capture satellite."""

    PAPER_SIZES = {
        "A4 Paysage": (297, 210),
        "A4 Portrait": (210, 297),
        "A3 Paysage": (420, 297),
        "A3 Portrait": (297, 420),
    }

    SETTINGS_PREFIX = "ElfadilyTopoTools/SituationSat/"

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.settings = QSettings()
        self.setWindowTitle("Situation sur Image Satellite")
        self.setMinimumWidth(500)
        self._setup_ui()
        self._load_settings()
        # Fixer la taille du dialogue pour éviter le resize au toggle
        self.setFixedHeight(self.sizeHint().height())

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # === TITRE ===
        title = QLabel("Situation sur Image Satellite")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 6px;")
        layout.addWidget(title)

        hint = QLabel("Utilise le fond de carte actuellement affiché dans QGIS.")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #7f8c8d; font-size: 11px; padding-bottom: 4px;")
        layout.addWidget(hint)

        # === ZONE DE CAPTURE ===
        grp_extent = QGroupBox("Zone de capture")
        ext_layout = QVBoxLayout()

        self.rb_canvas = QRadioButton("Vue courante du canevas")
        self.rb_layer = QRadioButton("Emprise d'une couche :")
        self.rb_canvas.setChecked(True)
        ext_layout.addWidget(self.rb_canvas)

        h_layer = QHBoxLayout()
        h_layer.addWidget(self.rb_layer)
        self.cmb_layers = QComboBox()
        self._populate_layers()
        h_layer.addWidget(self.cmb_layers, 1)
        ext_layout.addLayout(h_layer)

        h_buffer = QHBoxLayout()
        h_buffer.addWidget(QLabel("Marge autour (%) :"))
        self.spn_buffer = QSpinBox()
        self.spn_buffer.setRange(0, 200)
        self.spn_buffer.setValue(15)
        h_buffer.addWidget(self.spn_buffer)
        h_buffer.addStretch()
        ext_layout.addLayout(h_buffer)

        grp_extent.setLayout(ext_layout)
        layout.addWidget(grp_extent)

        # === MODE D'EXPORT ===
        grp_mode = QGroupBox("Mode d'export")
        mode_layout = QVBoxLayout()

        self.rb_simple = QRadioButton("Capture simple (image PNG/JPEG)")
        self.rb_cartouche = QRadioButton("PDF avec cartouche professionnel")
        self.rb_simple.setChecked(True)
        self.rb_simple.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.rb_simple)
        mode_layout.addWidget(self.rb_cartouche)

        grp_mode.setLayout(mode_layout)
        layout.addWidget(grp_mode)

        # === OPTIONS CAPTURE SIMPLE ===
        self.grp_simple = QGroupBox("Options image")
        simple_layout = QFormLayout()

        self.cmb_format = QComboBox()
        self.cmb_format.addItems(["PNG", "JPEG"])
        simple_layout.addRow("Format :", self.cmb_format)

        self.spn_dpi = QSpinBox()
        self.spn_dpi.setRange(72, 600)
        self.spn_dpi.setValue(300)
        simple_layout.addRow("Résolution (DPI) :", self.spn_dpi)

        self.spn_width = QSpinBox()
        self.spn_width.setRange(500, 10000)
        self.spn_width.setValue(2000)
        simple_layout.addRow("Largeur (px) :", self.spn_width)

        self.grp_simple.setLayout(simple_layout)
        layout.addWidget(self.grp_simple)

        # === OPTIONS CARTOUCHE ===
        self.grp_cart = QGroupBox("Cartouche")
        cart_form = QFormLayout()

        self.txt_titre = QLineEdit("PLAN DE SITUATION")
        cart_form.addRow("Titre :", self.txt_titre)

        self.txt_projet = QLineEdit()
        self.txt_projet.setPlaceholderText("Ex: Lotissement Al Amal - Laâyoune")
        cart_form.addRow("Projet :", self.txt_projet)

        self.txt_commune = QLineEdit()
        self.txt_commune.setPlaceholderText("Commune / Province")
        cart_form.addRow("Commune :", self.txt_commune)

        self.txt_client = QLineEdit()
        self.txt_client.setPlaceholderText("Nom du client / maître d'ouvrage")
        cart_form.addRow("Client :", self.txt_client)

        self.txt_operateur = QLineEdit()
        self.txt_operateur.setPlaceholderText("Nom de l'opérateur")
        cart_form.addRow("Opérateur :", self.txt_operateur)

        self.cmb_paper = QComboBox()
        self.cmb_paper.addItems(self.PAPER_SIZES.keys())
        cart_form.addRow("Format papier :", self.cmb_paper)

        self.spn_dpi_cart = QSpinBox()
        self.spn_dpi_cart.setRange(72, 600)
        self.spn_dpi_cart.setValue(300)
        cart_form.addRow("Résolution (DPI) :", self.spn_dpi_cart)

        self.txt_logo = QLineEdit()
        h_logo = QHBoxLayout()
        h_logo.addWidget(self.txt_logo)
        btn_logo = QPushButton("...")
        btn_logo.setFixedWidth(40)
        btn_logo.clicked.connect(self._browse_logo)
        h_logo.addWidget(btn_logo)
        cart_form.addRow("Logo :", h_logo)

        self.grp_cart.setLayout(cart_form)
        self.grp_cart.setVisible(False)
        layout.addWidget(self.grp_cart)

        # === INFOS SOCIÉTÉ (optionnel) ===
        self.grp_societe = QGroupBox("Société (optionnel)")
        soc_layout = QVBoxLayout()
        self.txt_soc_nom = QLineEdit()
        self.txt_soc_devise = QLineEdit()
        self.txt_soc_adresse = QLineEdit()
        soc_layout.addWidget(self.txt_soc_nom)
        soc_layout.addWidget(self.txt_soc_devise)
        soc_layout.addWidget(self.txt_soc_adresse)
        self.grp_societe.setLayout(soc_layout)
        self.grp_societe.setVisible(False)
        layout.addWidget(self.grp_societe)

        # === BOUTONS ===
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        layout.addWidget(sep)

        h_buttons = QHBoxLayout()
        h_buttons.addStretch()

        btn_preview = QPushButton("Prévisualiser")
        btn_preview.clicked.connect(self._preview)
        h_buttons.addWidget(btn_preview)

        btn_export = QPushButton("Exporter")
        btn_export.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; "
            "font-weight: bold; padding: 8px 20px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #2ecc71; }"
        )
        btn_export.clicked.connect(self._export)
        h_buttons.addWidget(btn_export)

        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.reject)
        h_buttons.addWidget(btn_close)

        layout.addLayout(h_buttons)

        # === COPYRIGHT ===
        lbl_copyright = QLabel("© ELFADILY GEOCONSEIL — Tous droits réservés")
        lbl_copyright.setAlignment(Qt.AlignCenter)
        lbl_copyright.setStyleSheet("color: #aaa; font-size: 10px; padding-top: 2px;")
        layout.addWidget(lbl_copyright)

    # ----------------------------------------------------------------
    # UI helpers
    # ----------------------------------------------------------------

    def _on_mode_changed(self, is_simple):
        self.grp_simple.setVisible(is_simple)
        self.grp_cart.setVisible(not is_simple)
        self.grp_societe.setVisible(not is_simple)
        # Recalculer la taille pour éviter que le dialogue grandisse
        self.setFixedHeight(self.sizeHint().height())

    def _populate_layers(self):
        """Remplit la liste des couches vectorielles du projet."""
        self.cmb_layers.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                self.cmb_layers.addItem(layer.name(), layer.id())

    def _browse_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choisir le logo", "",
            "Images (*.png *.jpg *.jpeg *.svg)"
        )
        if path:
            self.txt_logo.setText(path)

    def _load_settings(self):
        """Charge les valeurs sauvegardées (société, logo, etc.)."""
        s = self.settings
        p = self.SETTINGS_PREFIX
        self.txt_soc_nom.setText(s.value(p + "soc_nom", "ELFADILY GEOCONSEIL"))
        self.txt_soc_devise.setText(s.value(p + "soc_devise", "TOPOGRAPHIE - SIG - ETUDES"))
        self.txt_soc_adresse.setText(s.value(p + "soc_adresse", "LAAYOUNE"))
        self.txt_logo.setText(s.value(p + "logo_path", ""))

    def _save_settings(self):
        """Sauvegarde les valeurs pour la prochaine ouverture."""
        s = self.settings
        p = self.SETTINGS_PREFIX
        s.setValue(p + "soc_nom", self.txt_soc_nom.text())
        s.setValue(p + "soc_devise", self.txt_soc_devise.text())
        s.setValue(p + "soc_adresse", self.txt_soc_adresse.text())
        s.setValue(p + "logo_path", self.txt_logo.text())

    def reject(self):
        """Sauvegarde les paramètres en fermant."""
        self._save_settings()
        super().reject()

    def accept(self):
        """Sauvegarde les paramètres en validant."""
        self._save_settings()
        super().accept()

    # ----------------------------------------------------------------
    # Extent helpers
    # ----------------------------------------------------------------

    def _get_extent(self):
        """Retourne l'emprise selon le choix utilisateur."""
        if self.rb_layer.isChecked():
            layer_id = self.cmb_layers.currentData()
            if layer_id:
                layer = QgsProject.instance().mapLayer(layer_id)
                if layer:
                    canvas_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
                    transform = QgsCoordinateTransform(
                        layer.crs(), canvas_crs, QgsProject.instance()
                    )
                    return transform.transformBoundingBox(layer.extent())
        return self.iface.mapCanvas().extent()

    def _get_buffered_extent(self):
        """Emprise + marge en %."""
        extent = self._get_extent()
        buf = self.spn_buffer.value() / 100.0
        dx = extent.width() * buf / 2
        dy = extent.height() * buf / 2
        return QgsRectangle(
            extent.xMinimum() - dx, extent.yMinimum() - dy,
            extent.xMaximum() + dx, extent.yMaximum() + dy
        )

    # ----------------------------------------------------------------
    # Preview
    # ----------------------------------------------------------------

    def _preview(self):
        """Zoom le canevas sur l'emprise choisie."""
        extent = self._get_buffered_extent()
        self.iface.mapCanvas().setExtent(extent)
        self.iface.mapCanvas().refresh()

    # ----------------------------------------------------------------
    # Export
    # ----------------------------------------------------------------

    def _export(self):
        self._save_settings()
        if self.rb_simple.isChecked():
            self._do_export_simple()
        else:
            self._do_export_cartouche()

    # ---------- EXPORT SIMPLE (PNG / JPEG) ----------

    def _do_export_simple(self):
        fmt = self.cmb_format.currentText()
        ext = "jpg" if fmt == "JPEG" else "png"
        default_name = f"situation_{datetime.date.today().isoformat()}.{ext}"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer l'image",
            os.path.expanduser(f"~/{default_name}"),
            f"{fmt} (*.{ext})"
        )
        if not file_path:
            return

        extent = self._get_buffered_extent()
        width = self.spn_width.value()
        ratio = extent.height() / extent.width() if extent.width() else 1
        height = int(width * ratio)

        # Clone les settings du canevas (garde toutes les couches visibles)
        ms = QgsMapSettings(self.iface.mapCanvas().mapSettings())
        ms.setExtent(extent)
        ms.setOutputSize(QSize(width, height))
        ms.setOutputDpi(self.spn_dpi.value())

        job = QgsMapRendererParallelJob(ms)
        loop = QEventLoop()
        job.finished.connect(loop.quit)
        job.start()
        loop.exec_()

        img = job.renderedImage()
        if fmt == "JPEG":
            img.save(file_path, "JPEG", 95)
        else:
            img.save(file_path, "PNG")

        QMessageBox.information(
            self, "Succès",
            f"Image exportée :\n{file_path}\n"
            f"Taille : {width} x {height} px"
        )

    # ---------- EXPORT PDF AVEC CARTOUCHE ----------

    def _do_export_cartouche(self):
        default_name = f"situation_{datetime.date.today().isoformat()}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le PDF",
            os.path.expanduser(f"~/{default_name}"),
            "PDF (*.pdf)"
        )
        if not file_path:
            return

        project = QgsProject.instance()
        manager = project.layoutManager()

        # Créer un layout temporaire et l'enregistrer dans le manager
        # (nécessaire pour que l'export fonctionne correctement)
        ts = datetime.datetime.now().strftime('%H%M%S')
        layout_name = f"_TopoTools_Situation_{ts}"
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        layout.setName(layout_name)
        manager.addLayout(layout)

        try:
            self._build_cartouche_layout(layout)

            # Export PDF
            exporter = QgsLayoutExporter(layout)
            pdf_settings = QgsLayoutExporter.PdfExportSettings()
            pdf_settings.dpi = self.spn_dpi_cart.value()

            result = exporter.exportToPdf(file_path, pdf_settings)

            if result == QgsLayoutExporter.Success:
                QMessageBox.information(
                    self, "Succès",
                    f"PDF avec cartouche exporté :\n{file_path}"
                )
            else:
                error_map = {
                    QgsLayoutExporter.FileError: "Erreur d'accès au fichier",
                    QgsLayoutExporter.MemoryError: "Mémoire insuffisante",
                    QgsLayoutExporter.PrintError: "Erreur d'impression",
                    QgsLayoutExporter.SvgLayerError: "Erreur couche SVG",
                    QgsLayoutExporter.Canceled: "Export annulé",
                }
                err_msg = error_map.get(result, f"Erreur inconnue (code {result})")
                QMessageBox.warning(
                    self, "Erreur",
                    f"Échec de l'export PDF :\n{err_msg}"
                )

        except Exception as e:
            QMessageBox.warning(
                self, "Erreur",
                f"Erreur lors de la création du layout :\n{str(e)}"
            )

        finally:
            # Nettoyer : retirer le layout temporaire du manager
            manager.removeLayout(layout)

    def _build_cartouche_layout(self, layout):
        """Construit le layout complet : carte + cartouche."""

        paper_name = self.cmb_paper.currentText()
        pw, ph = self.PAPER_SIZES[paper_name]

        # --- Configurer la page ---
        page = layout.pageCollection().page(0)
        page.setPageSize(QgsLayoutSize(pw, ph, QgsUnitTypes.LayoutMillimeters))

        # --- Dimensions ---
        margin = 5        # marge extérieure (mm)
        cart_h = 35        # hauteur du cartouche (mm)
        gap = 2            # espace entre carte et cartouche

        map_x = margin
        map_y = margin
        map_w = pw - 2 * margin
        map_h = ph - margin - cart_h - gap - margin

        cart_x = margin
        cart_y = map_y + map_h + gap
        cart_w = map_w

        # ============================================================
        # 1. CARTE
        # ============================================================
        map_item = QgsLayoutItemMap(layout)
        map_item.attemptMove(
            QgsLayoutPoint(map_x, map_y, QgsUnitTypes.LayoutMillimeters)
        )
        map_item.attemptResize(
            QgsLayoutSize(map_w, map_h, QgsUnitTypes.LayoutMillimeters)
        )

        # IMPORTANT : assigner explicitement les couches visibles du canevas
        canvas = self.iface.mapCanvas()
        visible_layers = canvas.layers()
        map_item.setLayers(visible_layers)
        map_item.setCrs(canvas.mapSettings().destinationCrs())

        # Définir l'emprise
        map_item.setExtent(self._get_buffered_extent())

        # Cadre
        map_item.setFrameEnabled(True)
        map_item.setFrameStrokeWidth(
            QgsLayoutMeasurement(0.3, QgsUnitTypes.LayoutMillimeters)
        )
        map_item.setBackgroundEnabled(True)

        layout.addLayoutItem(map_item)

        # Forcer le rendu
        map_item.refresh()

        # ============================================================
        # 2. FLECHE NORD (coin haut-droit de la carte)
        # ============================================================
        north = QgsLayoutItemPicture(layout)

        # Chercher la flèche nord dans les SVG de QGIS
        from qgis.core import QgsApplication
        north_svg_path = None
        for svg_dir in QgsApplication.svgPaths():
            for candidate in ['arrows/NorthArrow_02.svg',
                              'arrows/NorthArrow_01.svg',
                              'arrows/north_arrow.svg']:
                full = os.path.join(svg_dir, candidate)
                if os.path.exists(full):
                    north_svg_path = full
                    break
            if north_svg_path:
                break

        # Fallback : flèche nord intégrée au plugin
        if not north_svg_path:
            north_svg_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'icons', 'north_arrow.svg'
            )

        north.setPicturePath(north_svg_path)

        north_size = 12  # mm
        north.attemptMove(QgsLayoutPoint(
            map_x + map_w - north_size - 3,
            map_y + 3,
            QgsUnitTypes.LayoutMillimeters
        ))
        north.attemptResize(QgsLayoutSize(
            north_size, north_size, QgsUnitTypes.LayoutMillimeters
        ))
        north.setFrameEnabled(False)
        layout.addLayoutItem(north)

        # ============================================================
        # 3. CADRE DU CARTOUCHE (rectangle de fond)
        # ============================================================
        cart_rect = QgsLayoutItemShape(layout)
        cart_rect.setShapeType(QgsLayoutItemShape.Rectangle)
        cart_rect.attemptMove(
            QgsLayoutPoint(cart_x, cart_y, QgsUnitTypes.LayoutMillimeters)
        )
        cart_rect.attemptResize(
            QgsLayoutSize(cart_w, cart_h, QgsUnitTypes.LayoutMillimeters)
        )
        sym = QgsFillSymbol.createSimple({
            'color': '255,255,255,255',
            'outline_color': '0,0,0,255',
            'outline_width': '0.4',
        })
        cart_rect.setSymbol(sym)
        cart_rect.setFrameEnabled(False)
        layout.addLayoutItem(cart_rect)

        # ============================================================
        # 4. CONTENU DU CARTOUCHE
        #    | Logo | Infos projet | Titre | Bureau |
        # ============================================================

        pad = 2  # padding interne

        # Calculer les colonnes
        col1_x = cart_x + pad          # Logo
        col1_w = 28
        col2_x = col1_x + col1_w + pad  # Infos projet
        col2_w = cart_w * 0.32
        col4_w = cart_w * 0.22          # Bureau (droite)
        col4_x = cart_x + cart_w - col4_w - pad
        col3_x = col2_x + col2_w + pad  # Titre (centre)
        col3_w = col4_x - col3_x - pad

        row_y = cart_y + pad
        row_h = cart_h - 2 * pad

        # --- Logo ---
        logo_path = self.txt_logo.text().strip()
        if logo_path and os.path.exists(logo_path):
            logo = QgsLayoutItemPicture(layout)
            logo.setPicturePath(logo_path)
            logo.attemptMove(QgsLayoutPoint(
                col1_x + 2, row_y + 2, QgsUnitTypes.LayoutMillimeters
            ))
            logo.attemptResize(QgsLayoutSize(
                col1_w - 4, row_h - 4, QgsUnitTypes.LayoutMillimeters
            ))
            logo.setFrameEnabled(False)
            layout.addLayoutItem(logo)

        # --- Infos projet (colonne 2) ---
        info_parts = []
        if self.txt_projet.text():
            info_parts.append(f"Projet: {self.txt_projet.text()}")
        if self.txt_commune.text():
            info_parts.append(f"Commune: {self.txt_commune.text()}")
        if self.txt_client.text():
            info_parts.append(f"Client: {self.txt_client.text()}")
        if self.txt_operateur.text():
            info_parts.append(f"Opérateur: {self.txt_operateur.text()}")
        info_parts.append(f"Date: {datetime.date.today().strftime('%d/%m/%Y')}")

        lbl_info = QgsLayoutItemLabel(layout)
        lbl_info.setText("\n".join(info_parts))
        lbl_info.setFont(QFont("Arial", 7))
        lbl_info.setVAlign(Qt.AlignTop)
        lbl_info.attemptMove(QgsLayoutPoint(
            col2_x, row_y, QgsUnitTypes.LayoutMillimeters
        ))
        lbl_info.attemptResize(QgsLayoutSize(
            col2_w, row_h, QgsUnitTypes.LayoutMillimeters
        ))
        lbl_info.setFrameEnabled(False)
        layout.addLayoutItem(lbl_info)

        # --- Titre (colonne 3, centré) ---
        lbl_titre = QgsLayoutItemLabel(layout)
        lbl_titre.setText(self.txt_titre.text() or "PLAN DE SITUATION")
        lbl_titre.setFont(QFont("Arial", 12, QFont.Bold))
        lbl_titre.setHAlign(Qt.AlignCenter)
        lbl_titre.setVAlign(Qt.AlignVCenter)
        lbl_titre.attemptMove(QgsLayoutPoint(
            col3_x, row_y, QgsUnitTypes.LayoutMillimeters
        ))
        lbl_titre.attemptResize(QgsLayoutSize(
            col3_w, row_h, QgsUnitTypes.LayoutMillimeters
        ))
        lbl_titre.setFrameEnabled(False)
        layout.addLayoutItem(lbl_titre)

        # --- Société (colonne 4, droite) ---
        soc_parts = []
        nom = self.txt_soc_nom.text().strip()
        devise = self.txt_soc_devise.text().strip()
        adresse = self.txt_soc_adresse.text().strip()
        if nom:
            soc_parts.append(nom)
        if devise:
            soc_parts.append(devise)
        if adresse:
            soc_parts.append(adresse)

        if soc_parts:
            lbl_bureau = QgsLayoutItemLabel(layout)
            lbl_bureau.setText("\n".join(soc_parts))
            # Nom en gras : on met tout en même police,
            # le nom est la première ligne et ressort naturellement
            lbl_bureau.setFont(QFont("Arial", 7))
            lbl_bureau.setHAlign(Qt.AlignCenter)
            lbl_bureau.setVAlign(Qt.AlignVCenter)
            lbl_bureau.attemptMove(QgsLayoutPoint(
                col4_x, row_y, QgsUnitTypes.LayoutMillimeters
            ))
            lbl_bureau.attemptResize(QgsLayoutSize(
                col4_w, row_h, QgsUnitTypes.LayoutMillimeters
            ))
            lbl_bureau.setFrameEnabled(False)
            layout.addLayoutItem(lbl_bureau)

        # --- Lignes séparatrices verticales ---
        sep_positions = [
            col1_x + col1_w,    # après logo
            col2_x + col2_w,    # après infos
            col4_x - pad,       # avant bureau
        ]
        for sx in sep_positions:
            vline = QgsLayoutItemShape(layout)
            vline.setShapeType(QgsLayoutItemShape.Rectangle)
            vline.attemptMove(QgsLayoutPoint(
                sx, cart_y, QgsUnitTypes.LayoutMillimeters
            ))
            vline.attemptResize(QgsLayoutSize(
                0.3, cart_h, QgsUnitTypes.LayoutMillimeters
            ))
            line_sym = QgsFillSymbol.createSimple({
                'color': '0,0,0,255',
                'outline_color': '0,0,0,255',
                'outline_width': '0',
            })
            vline.setSymbol(line_sym)
            vline.setFrameEnabled(False)
            layout.addLayoutItem(vline)


class SituationSatModule(BaseModule):
    MODULE_NAME = "Situation Satellite"
    MODULE_ICON = "sat.png"
    MODULE_TOOLTIP = "Situation sur Image Satellite"

    def run(self):
        dlg = SituationSatDialog(self.iface, self.iface.mainWindow())
        dlg.exec_()
