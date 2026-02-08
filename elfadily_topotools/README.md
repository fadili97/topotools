# ELFADILY TopoTools - Plugin QGIS

Plugin QGIS modulaire pour les bureaux d'études topographiques.  
Développé pour **ELFADILY GEOCONSEIL** - Laâyoune, Maroc.

## 📦 Installation

### Méthode 1 : Installation manuelle
1. Copier le dossier `elfadily_topotools` dans le répertoire des plugins QGIS :
   - **Windows** : `C:\Users\<user>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux** : `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **macOS** : `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
2. Redémarrer QGIS
3. Aller dans **Extensions → Gérer les extensions**
4. Chercher "ELFADILY TopoTools" et l'activer

### Méthode 2 : ZIP
1. Compresser le dossier `elfadily_topotools` en `.zip`
2. QGIS → **Extensions → Gérer → Installer depuis un ZIP**

## 🛠 Modules disponibles

### 1. 📡 Situation sur Image Satellite
- Capture rapide d'une zone sur fond satellite (Google, Bing, ESRI)
- Export PNG/JPEG simple (sans cartouche) pour captures rapides
- Export PDF avec cartouche professionnel (titre, projet, commune, logo)
- Choix de l'emprise : vue courante ou couche spécifique
- Marge (buffer) paramétrable autour de l'emprise

### 2. 📐 Points → Géométrie
- Coller des coordonnées directement (copier depuis Excel, bloc-notes, etc.)
- Séparateurs : espace, point-virgule, virgule, tabulation, personnalisé
- Formats : N° X Y Z, X Y Z, N° Y X Z, Y X Z
- Génération : Polygone, Polyligne ou Points
- CRS prédéfinis pour le Maroc (Merchich, UTM)
- Numérotation automatique des sommets
- Export direct en shapefile

### 3. 📁 Création Shapefile
- Créer un shapefile vide dans un dossier choisi (pas de temp)
- Table attributaire personnalisable (nom, type, longueur)
- Templates prédéfinis : Parcelle/Lot, Borne, Voirie, Réseau, Bâtiment
- Sauvegarder ses propres modèles de table (persistants)
- Ouvrir en mode édition automatiquement
- Tab dédié pour ajouter des features à un shapefile existant

## 🏗 Architecture extensible

```
elfadily_topotools/
├── __init__.py              # Point d'entrée QGIS
├── plugin_main.py           # Gestionnaire principal (charge les modules)
├── base_module.py           # Classe de base pour tous les modules
├── metadata.txt             # Métadonnées du plugin
├── user_templates.json      # Templates sauvegardés (auto-généré)
├── icons/                   # Icônes des modules
│   ├── main_icon.png
│   ├── sat.png
│   ├── points.png
│   └── shapefile.png
└── modules/                 # Dossier des modules
    ├── __init__.py
    ├── situation_sat.py     # Module satellite
    ├── points_to_geometry.py# Module points→géométrie
    └── shapefile_creator.py # Module création shapefile
```

## ➕ Ajouter un nouveau module

1. Créer un fichier dans `modules/mon_module.py`
2. Hériter de `BaseModule` :

```python
from ..base_module import BaseModule

class MonModule(BaseModule):
    MODULE_NAME = "Mon Module"
    MODULE_ICON = "mon_icon.png"
    MODULE_TOOLTIP = "🔧 Mon Nouveau Module"

    def run(self):
        # Votre code ici
        pass
```

3. L'enregistrer dans `plugin_main.py` :

```python
self._register_module("modules.mon_module", "MonModule")
```

4. Redémarrer QGIS. C'est tout !

## 🗂 CRS Marocains pré-configurés

| Nom | EPSG |
|-----|------|
| Merchich / Nord Maroc | 26191 |
| Merchich / Sud Maroc | 26192 |
| Merchich / Sahara Nord | 26194 |
| Merchich / Sahara Sud | 26195 |
| WGS 84 / UTM 28N | 32628 |
| WGS 84 / UTM 29N | 32629 |
| WGS 84 / UTM 30N | 32630 |

## 📋 Versions

- **v1.0.0** : Modules Situation Satellite, Points→Géométrie, Création Shapefile

## 📞 Support

ELFADILY GEOCONSEIL  
Laâyoune, Maroc  
contact@elfadilygeoconseil.com
