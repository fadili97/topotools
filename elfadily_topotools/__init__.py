"""
ELFADILY TopoTools - Plugin QGIS pour bureaux d'études topographiques
© ELFADILY GEOCONSEIL — Tous droits réservés
"""


def classFactory(iface):
    from .plugin_main import ElfadilyTopoTools
    return ElfadilyTopoTools(iface)
