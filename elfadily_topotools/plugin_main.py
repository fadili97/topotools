"""
ELFADILY TopoTools - Plugin principal
Architecture modulaire et extensible
© ELFADILY GEOCONSEIL — Tous droits réservés
"""

import os
from qgis.PyQt.QtWidgets import QAction, QToolBar, QMenu, QToolButton
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt


class ElfadilyTopoTools:
    """Plugin principal - conteneur pour tous les modules."""

    PLUGIN_NAME = "ELFADILY TopoTools"
    VERSION = "1.0.2"

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.toolbar = None
        self.menu_name = self.PLUGIN_NAME
        self.modules = []
        self.actions = []

    def initGui(self):
        """Initialise l'interface du plugin."""
        # Créer la toolbar dédiée
        self.toolbar = self.iface.addToolBar(self.PLUGIN_NAME)
        self.toolbar.setObjectName("ElfadilyTopoToolsToolbar")
        self.toolbar.setToolTip(f"{self.PLUGIN_NAME} v{self.VERSION}")

        # ============================================================
        # ENREGISTREMENT DES MODULES
        # Pour ajouter un nouveau module, il suffit d'ajouter une ligne ici
        # ============================================================
        self._register_module("modules.situation_sat", "SituationSatModule")
        self._register_module("modules.points_to_geometry", "PointsToGeometryModule")
        self._register_module("modules.shapefile_creator", "ShapefileCreatorModule")
        self._register_module("modules.qr_location", "QRLocationModule")
        # --- Ajouter vos futurs modules ici ---
        # self._register_module("modules.profil_en_long", "ProfilEnLongModule")
        # self._register_module("modules.calcul_surfaces", "CalculSurfacesModule")
        # self._register_module("modules.cartouche", "CartoucheModule")

    def _register_module(self, module_path, class_name):
        """Charge et enregistre un module dynamiquement."""
        try:
            # Import dynamique
            full_path = f"elfadily_topotools.{module_path}"
            mod = __import__(full_path, fromlist=[class_name])
            klass = getattr(mod, class_name)

            # Instancier le module
            module_instance = klass(self.iface, self.toolbar, self.plugin_dir)
            module_instance.register()
            self.modules.append(module_instance)

        except Exception as e:
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(
                f"Erreur chargement module {module_path}: {str(e)}",
                self.PLUGIN_NAME, Qgis.Warning
            )

    def unload(self):
        """Nettoie le plugin."""
        # Décharger tous les modules
        for module in self.modules:
            try:
                module.unload()
            except Exception:
                pass

        # Supprimer la toolbar
        if self.toolbar:
            del self.toolbar

        # Supprimer les entrées de menu
        for action in self.actions:
            self.iface.removePluginMenu(self.menu_name, action)
