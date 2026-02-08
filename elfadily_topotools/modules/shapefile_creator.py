"""
Module Création Shapefile
- Créer un shapefile vide avec table attributaire personnalisée
- Choix du type de géométrie
- Choix du CRS
- Enregistrement dans un dossier choisi
- Réutilisation de schémas précédents (templates)
- Ajout de features lors d'un 2ème usage
"""

import os
import json
import datetime
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QComboBox, QCheckBox, QSpinBox, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QFormLayout, QFrame, QTextEdit,
    QRadioButton, QButtonGroup, QTableWidget, QTableWidgetItem,
    QHeaderView, QWidget, QTabWidget, QListWidget, QListWidgetItem,
    QInputDialog, QAbstractItemView
)
from qgis.PyQt.QtGui import QFont, QColor, QIcon
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsField, QgsFields, QgsCoordinateReferenceSystem,
    QgsVectorFileWriter, QgsWkbTypes, QgsEditorWidgetSetup
)

from ..base_module import BaseModule


class ShapefileCreatorDialog(QDialog):
    """Dialogue pour créer des shapefiles."""

    FIELD_TYPES = {
        "Texte (String)": QVariant.String,
        "Entier (Integer)": QVariant.Int,
        "Décimal (Double)": QVariant.Double,
        "Date": QVariant.Date,
        "Booléen": QVariant.Bool,
    }

    GEOM_TYPES = {
        "Point": "Point",
        "Ligne (LineString)": "LineString",
        "Polygone": "Polygon",
        "Multi-Point": "MultiPoint",
        "Multi-Ligne": "MultiLineString",
        "Multi-Polygone": "MultiPolygon",
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

    # Templates prédéfinis pour les tâches courantes topo
    PRESET_TEMPLATES = {
        "Parcelle / Lot": [
            ("num_lot", "Texte (String)", 20),
            ("surface_m2", "Décimal (Double)", 0),
            ("perimetre_m", "Décimal (Double)", 0),
            ("proprietaire", "Texte (String)", 100),
            ("titre_foncier", "Texte (String)", 50),
            ("observation", "Texte (String)", 200),
        ],
        "Borne topographique": [
            ("num_borne", "Texte (String)", 20),
            ("x", "Décimal (Double)", 0),
            ("y", "Décimal (Double)", 0),
            ("z", "Décimal (Double)", 0),
            ("type_borne", "Texte (String)", 50),
            ("etat", "Texte (String)", 50),
        ],
        "Voirie / Route": [
            ("nom", "Texte (String)", 100),
            ("type_voie", "Texte (String)", 50),
            ("largeur_m", "Décimal (Double)", 0),
            ("longueur_m", "Décimal (Double)", 0),
            ("revetement", "Texte (String)", 50),
        ],
        "Réseau (AEP/Assainissement)": [
            ("type_reseau", "Texte (String)", 50),
            ("diametre_mm", "Entier (Integer)", 0),
            ("materiau", "Texte (String)", 50),
            ("profondeur_m", "Décimal (Double)", 0),
            ("etat", "Texte (String)", 50),
        ],
        "Bâtiment": [
            ("nom", "Texte (String)", 100),
            ("type", "Texte (String)", 50),
            ("nb_etages", "Entier (Integer)", 0),
            ("surface_m2", "Décimal (Double)", 0),
            ("usage", "Texte (String)", 50),
        ],
        "Vide (personnalisé)": [],
    }

    # Fichier de sauvegarde des templates utilisateur
    TEMPLATES_FILE = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "user_templates.json"
    )

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle("📁 Création Shapefile")
        self.setMinimumSize(750, 650)
        self._setup_ui()
        self._load_user_templates()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Créer un Shapefile")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 8px;")
        layout.addWidget(title)

        tabs = QTabWidget()

        # ============ TAB 1: Nouveau Shapefile ============
        tab_new = QWidget()
        new_layout = QVBoxLayout(tab_new)

        # Infos de base
        grp_base = QGroupBox("Paramètres de base")
        base_layout = QFormLayout()

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Ex: parcelles_lotissement_al_amal")
        base_layout.addRow("Nom du fichier :", self.txt_name)

        h_folder = QHBoxLayout()
        self.txt_folder = QLineEdit()
        self.txt_folder.setPlaceholderText("Choisir le dossier de destination")
        h_folder.addWidget(self.txt_folder)
        btn_browse = QPushButton("📂")
        btn_browse.setFixedWidth(40)
        btn_browse.clicked.connect(self._browse_folder)
        h_folder.addWidget(btn_browse)
        base_layout.addRow("Dossier :", h_folder)

        self.cmb_geom = QComboBox()
        self.cmb_geom.addItems(self.GEOM_TYPES.keys())
        self.cmb_geom.setCurrentText("Polygone")
        base_layout.addRow("Type géométrie :", self.cmb_geom)

        self.cmb_crs = QComboBox()
        for label, code in self.COMMON_CRS:
            self.cmb_crs.addItem(label, code)
        self.cmb_crs.currentIndexChanged.connect(self._on_crs_changed)
        base_layout.addRow("Système coord. :", self.cmb_crs)

        grp_base.setLayout(base_layout)
        new_layout.addWidget(grp_base)

        # Template prédéfini
        grp_template = QGroupBox("Modèle de table attributaire")
        tpl_layout = QHBoxLayout()

        self.cmb_template = QComboBox()
        self.cmb_template.addItems(self.PRESET_TEMPLATES.keys())
        self.cmb_template.currentTextChanged.connect(self._load_template)
        tpl_layout.addWidget(self.cmb_template, 1)

        btn_apply_tpl = QPushButton("Appliquer")
        btn_apply_tpl.clicked.connect(lambda: self._load_template(self.cmb_template.currentText()))
        tpl_layout.addWidget(btn_apply_tpl)

        grp_template.setLayout(tpl_layout)
        new_layout.addWidget(grp_template)

        # Table attributaire
        grp_fields = QGroupBox("Champs de la table attributaire")
        fields_layout = QVBoxLayout()

        self.table_fields = QTableWidget()
        self.table_fields.setColumnCount(3)
        self.table_fields.setHorizontalHeaderLabels(["Nom du champ", "Type", "Longueur"])
        self.table_fields.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_fields.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_fields.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_fields.setAlternatingRowColors(True)
        fields_layout.addWidget(self.table_fields)

        h_field_btns = QHBoxLayout()
        btn_add_field = QPushButton("➕ Ajouter champ")
        btn_add_field.clicked.connect(self._add_field_row)
        h_field_btns.addWidget(btn_add_field)

        btn_remove_field = QPushButton("➖ Supprimer champ")
        btn_remove_field.clicked.connect(self._remove_field_row)
        h_field_btns.addWidget(btn_remove_field)

        btn_save_tpl = QPushButton("💾 Sauver comme modèle")
        btn_save_tpl.clicked.connect(self._save_as_template)
        h_field_btns.addWidget(btn_save_tpl)

        h_field_btns.addStretch()
        fields_layout.addLayout(h_field_btns)

        grp_fields.setLayout(fields_layout)
        new_layout.addWidget(grp_fields)

        # Option: ouvrir en édition
        self.chk_edit = QCheckBox("Ouvrir en mode édition après création")
        self.chk_edit.setChecked(True)
        new_layout.addWidget(self.chk_edit)

        tabs.addTab(tab_new, "📄 Nouveau Shapefile")

        # ============ TAB 2: Ajouter des features à un shapefile existant ============
        tab_add = QWidget()
        add_layout = QVBoxLayout(tab_add)

        grp_existing = QGroupBox("Shapefile existant")
        exist_layout = QFormLayout()

        self.cmb_existing_layers = QComboBox()
        self._populate_existing_layers()
        exist_layout.addRow("Couche :", self.cmb_existing_layers)

        h_or = QHBoxLayout()
        h_or.addWidget(QLabel("— ou —"))
        exist_layout.addRow("", h_or)

        h_file = QHBoxLayout()
        self.txt_existing_file = QLineEdit()
        self.txt_existing_file.setPlaceholderText("Charger un shapefile existant...")
        h_file.addWidget(self.txt_existing_file)
        btn_load = QPushButton("📂")
        btn_load.setFixedWidth(40)
        btn_load.clicked.connect(self._browse_existing_shp)
        h_file.addWidget(btn_load)
        exist_layout.addRow("Fichier :", h_file)

        grp_existing.setLayout(exist_layout)
        add_layout.addWidget(grp_existing)

        # Info sur la structure
        grp_info = QGroupBox("Structure de la couche")
        info_layout = QVBoxLayout()
        self.lbl_layer_info = QLabel("Sélectionnez une couche pour voir sa structure.")
        self.lbl_layer_info.setWordWrap(True)
        self.lbl_layer_info.setStyleSheet("color: #7f8c8d;")
        info_layout.addWidget(self.lbl_layer_info)

        btn_inspect = QPushButton("🔍 Inspecter la couche")
        btn_inspect.clicked.connect(self._inspect_existing)
        info_layout.addWidget(btn_inspect)

        grp_info.setLayout(info_layout)
        add_layout.addWidget(grp_info)

        # Bouton pour ouvrir en édition
        btn_open_edit = QPushButton("✏️ Ouvrir en mode édition")
        btn_open_edit.setStyleSheet(
            "QPushButton { background-color: #f39c12; color: white; "
            "font-weight: bold; padding: 8px; border-radius: 4px; }"
        )
        btn_open_edit.clicked.connect(self._open_for_editing)
        add_layout.addWidget(btn_open_edit)

        add_layout.addStretch()
        tabs.addTab(tab_add, "✏️ Ajouter à un existant")

        # ============ TAB 3: Mes modèles ============
        tab_templates = QWidget()
        tpl_main_layout = QVBoxLayout(tab_templates)

        self.list_templates = QListWidget()
        tpl_main_layout.addWidget(self.list_templates)

        h_tpl_btns = QHBoxLayout()
        btn_del_tpl = QPushButton("🗑 Supprimer le modèle")
        btn_del_tpl.clicked.connect(self._delete_template)
        h_tpl_btns.addWidget(btn_del_tpl)
        h_tpl_btns.addStretch()
        tpl_main_layout.addLayout(h_tpl_btns)

        tabs.addTab(tab_templates, "📋 Mes Modèles")

        layout.addWidget(tabs)

        # === BOUTONS PRINCIPAUX ===
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        layout.addWidget(sep)

        h_buttons = QHBoxLayout()
        h_buttons.addStretch()

        btn_create = QPushButton("✅ Créer le Shapefile")
        btn_create.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; "
            "font-weight: bold; padding: 8px 20px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #2ecc71; }"
        )
        btn_create.clicked.connect(self._create_shapefile)
        h_buttons.addWidget(btn_create)

        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.reject)
        h_buttons.addWidget(btn_close)

        layout.addLayout(h_buttons)

        # Charger le template par défaut
        self._load_template("Parcelle / Lot")

    def _on_crs_changed(self, index):
        if self.cmb_crs.currentData() is None:
            from qgis.gui import QgsProjectionSelectionDialog
            dlg = QgsProjectionSelectionDialog(self)
            if dlg.exec_():
                crs = dlg.crs()
                self.cmb_crs.setItemText(index, f"{crs.description()} - {crs.authid()}")
                self.cmb_crs.setItemData(index, crs.authid())

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choisir le dossier de destination",
            os.path.expanduser("~")
        )
        if folder:
            self.txt_folder.setText(folder)

    def _browse_existing_shp(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un Shapefile",
            os.path.expanduser("~"),
            "Shapefile (*.shp);;GeoPackage (*.gpkg);;Tous (*.*)"
        )
        if path:
            self.txt_existing_file.setText(path)

    def _populate_existing_layers(self):
        self.cmb_existing_layers.clear()
        self.cmb_existing_layers.addItem("-- Choisir une couche --", None)
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                self.cmb_existing_layers.addItem(
                    f"{layer.name()} ({layer.featureCount()} features)",
                    layer.id()
                )

    def _add_field_row(self, name="", field_type="Texte (String)", length=50):
        """Ajoute une ligne au tableau des champs."""
        row = self.table_fields.rowCount()
        self.table_fields.insertRow(row)

        # Nom
        item_name = QTableWidgetItem(name)
        self.table_fields.setItem(row, 0, item_name)

        # Type
        cmb_type = QComboBox()
        cmb_type.addItems(self.FIELD_TYPES.keys())
        cmb_type.setCurrentText(field_type)
        self.table_fields.setCellWidget(row, 1, cmb_type)

        # Longueur
        spn_length = QSpinBox()
        spn_length.setRange(0, 1000)
        spn_length.setValue(length)
        self.table_fields.setCellWidget(row, 2, spn_length)

    def _remove_field_row(self):
        row = self.table_fields.currentRow()
        if row >= 0:
            self.table_fields.removeRow(row)

    def _load_template(self, template_name):
        """Charge un template prédéfini."""
        # Chercher dans les presets
        if template_name in self.PRESET_TEMPLATES:
            fields = self.PRESET_TEMPLATES[template_name]
        else:
            # Chercher dans les templates utilisateur
            fields = self._get_user_template(template_name)

        if fields is None:
            return

        self.table_fields.setRowCount(0)
        for name, ftype, length in fields:
            self._add_field_row(name, ftype, length)

    def _save_as_template(self):
        """Sauvegarde la config actuelle comme template."""
        name, ok = QInputDialog.getText(
            self, "Nom du modèle",
            "Nom pour ce modèle de table attributaire :"
        )
        if not ok or not name:
            return

        fields = self._get_fields_from_table()
        templates = self._load_user_templates_file()
        templates[name] = [(f["name"], f["type_name"], f["length"]) for f in fields]
        self._save_user_templates_file(templates)

        # Ajouter au combo
        if name not in [self.cmb_template.itemText(i) for i in range(self.cmb_template.count())]:
            self.cmb_template.addItem(name)

        self._refresh_templates_list()
        QMessageBox.information(self, "Succès", f"Modèle '{name}' sauvegardé.")

    def _delete_template(self):
        item = self.list_templates.currentItem()
        if not item:
            return
        name = item.text()
        templates = self._load_user_templates_file()
        if name in templates:
            del templates[name]
            self._save_user_templates_file(templates)
            self._refresh_templates_list()
            QMessageBox.information(self, "Supprimé", f"Modèle '{name}' supprimé.")

    def _get_fields_from_table(self):
        """Récupère les champs depuis le tableau."""
        fields = []
        for row in range(self.table_fields.rowCount()):
            name_item = self.table_fields.item(row, 0)
            type_widget = self.table_fields.cellWidget(row, 1)
            length_widget = self.table_fields.cellWidget(row, 2)

            if name_item and name_item.text().strip():
                type_name = type_widget.currentText() if type_widget else "Texte (String)"
                length = length_widget.value() if length_widget else 50

                fields.append({
                    "name": name_item.text().strip().replace(" ", "_"),
                    "type": self.FIELD_TYPES.get(type_name, QVariant.String),
                    "type_name": type_name,
                    "length": length
                })
        return fields

    def _load_user_templates_file(self):
        """Charge les templates utilisateur depuis le fichier JSON."""
        if os.path.exists(self.TEMPLATES_FILE):
            try:
                with open(self.TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_user_templates_file(self, templates):
        """Sauvegarde les templates utilisateur."""
        try:
            with open(self.TEMPLATES_FILE, 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de sauvegarder : {e}")

    def _load_user_templates(self):
        """Charge les templates utilisateur au démarrage."""
        templates = self._load_user_templates_file()
        for name in templates:
            if name not in [self.cmb_template.itemText(i) for i in range(self.cmb_template.count())]:
                self.cmb_template.addItem(name)
        self._refresh_templates_list()

    def _get_user_template(self, name):
        templates = self._load_user_templates_file()
        return templates.get(name)

    def _refresh_templates_list(self):
        self.list_templates.clear()
        templates = self._load_user_templates_file()
        for name in templates:
            self.list_templates.addItem(name)

    def _inspect_existing(self):
        """Affiche les infos de la couche existante."""
        layer = self._get_existing_layer()
        if not layer:
            return

        fields_info = []
        for field in layer.fields():
            fields_info.append(f"  • {field.name()} ({field.typeName()})")

        info = (
            f"Nom : {layer.name()}\n"
            f"Type : {QgsWkbTypes.displayString(layer.wkbType())}\n"
            f"CRS : {layer.crs().authid()}\n"
            f"Features : {layer.featureCount()}\n"
            f"Champs :\n" + "\n".join(fields_info)
        )
        self.lbl_layer_info.setText(info)
        self.lbl_layer_info.setStyleSheet("color: #2c3e50; font-family: Consolas;")

    def _get_existing_layer(self):
        """Retourne la couche existante sélectionnée."""
        # D'abord vérifier le fichier
        if self.txt_existing_file.text():
            path = self.txt_existing_file.text()
            layer = QgsVectorLayer(path, os.path.basename(path), "ogr")
            if layer.isValid():
                return layer

        # Sinon la couche du projet
        layer_id = self.cmb_existing_layers.currentData()
        if layer_id:
            return QgsProject.instance().mapLayer(layer_id)

        QMessageBox.warning(self, "Attention", "Aucune couche sélectionnée.")
        return None

    def _open_for_editing(self):
        """Ouvre la couche existante en mode édition."""
        layer = self._get_existing_layer()
        if not layer:
            return

        # Ajouter au projet si pas déjà fait
        if not QgsProject.instance().mapLayer(layer.id()):
            QgsProject.instance().addMapLayer(layer)

        layer.startEditing()
        self.iface.setActiveLayer(layer)
        self.iface.actionToggleEditing().setChecked(True)
        QMessageBox.information(
            self, "Mode édition",
            f"La couche '{layer.name()}' est maintenant en mode édition.\n"
            f"Utilisez les outils de digitalisation de QGIS pour ajouter des features."
        )

    def _create_shapefile(self):
        """Crée le shapefile."""
        name = self.txt_name.text().strip()
        folder = self.txt_folder.text().strip()

        if not name:
            QMessageBox.warning(self, "Attention", "Veuillez entrer un nom de fichier.")
            return
        if not folder or not os.path.isdir(folder):
            QMessageBox.warning(self, "Attention", "Veuillez choisir un dossier valide.")
            return

        # Nettoyer le nom
        name = name.replace(" ", "_")
        if not name.endswith(".shp"):
            name += ".shp"

        file_path = os.path.join(folder, name)

        # Vérifier si existe déjà
        if os.path.exists(file_path):
            reply = QMessageBox.question(
                self, "Fichier existant",
                f"Le fichier {name} existe déjà.\nVoulez-vous l'écraser ?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        # CRS
        crs_code = self.cmb_crs.currentData() or "EPSG:4326"
        crs = QgsCoordinateReferenceSystem(crs_code)

        # Type de géométrie
        geom_key = self.cmb_geom.currentText()
        geom_type = self.GEOM_TYPES[geom_key]

        # Champs
        fields_config = self._get_fields_from_table()
        qgs_fields = QgsFields()
        for f in fields_config:
            field = QgsField(f["name"], f["type"])
            if f["type"] == QVariant.String:
                field.setLength(f["length"] if f["length"] > 0 else 50)
            qgs_fields.append(field)

        # Créer le writer
        writer = QgsVectorFileWriter(
            file_path, "UTF-8", qgs_fields,
            QgsWkbTypes.parseType(geom_type),
            crs, "ESRI Shapefile"
        )

        if writer.hasError():
            QMessageBox.warning(
                self, "Erreur",
                f"Erreur création shapefile : {writer.errorMessage()}"
            )
            return

        del writer  # Fermer le fichier

        # Charger dans QGIS
        layer = QgsVectorLayer(file_path, os.path.splitext(name)[0], "ogr")
        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)

            if self.chk_edit.isChecked():
                layer.startEditing()
                self.iface.setActiveLayer(layer)

            QMessageBox.information(
                self, "Succès",
                f"Shapefile créé :\n{file_path}\n\n"
                f"Type : {geom_key}\n"
                f"CRS : {crs_code}\n"
                f"Champs : {len(fields_config)}"
            )
        else:
            QMessageBox.warning(self, "Erreur", "Le shapefile créé n'est pas valide.")


class ShapefileCreatorModule(BaseModule):
    MODULE_NAME = "Création Shapefile"
    MODULE_ICON = "shapefile.png"
    MODULE_TOOLTIP = "📁 Créer un Shapefile"

    def run(self):
        dlg = ShapefileCreatorDialog(self.iface, self.iface.mainWindow())
        dlg.exec_()
