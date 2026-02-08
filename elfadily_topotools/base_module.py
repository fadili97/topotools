"""
Classe de base pour tous les modules du plugin.
Chaque module hérite de BaseModule et implémente register() et run().
"""

import os
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon


class BaseModule:
    """Classe de base pour les modules TopoTools."""

    # À surcharger dans chaque module
    MODULE_NAME = "Module"
    MODULE_ICON = "default.png"
    MODULE_TOOLTIP = "Module TopoTools"

    def __init__(self, iface, toolbar, plugin_dir):
        self.iface = iface
        self.toolbar = toolbar
        self.plugin_dir = plugin_dir
        self.action = None
        self.dialog = None

    def _icon_path(self, icon_name=None):
        """Retourne le chemin complet vers une icône."""
        name = icon_name or self.MODULE_ICON
        return os.path.join(self.plugin_dir, "icons", name)

    def register(self):
        """Enregistre le module dans la toolbar et le menu."""
        icon = QIcon(self._icon_path())
        self.action = QAction(icon, self.MODULE_TOOLTIP, self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.toolbar.addAction(self.action)

        # Aussi dans le menu Sketches
        self.iface.addPluginToMenu("ELFADILY TopoTools", self.action)

    def run(self):
        """Exécute le module. À surcharger."""
        raise NotImplementedError("Chaque module doit implémenter run()")

    def unload(self):
        """Nettoie le module."""
        if self.action:
            self.iface.removePluginMenu("ELFADILY TopoTools", self.action)
            self.toolbar.removeAction(self.action)
