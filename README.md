# ELFADILY TopoTools

Plugin QGIS modulaire pour les bureaux d'études topographiques.

## 📦 Installation

### Méthode 1: Dépôt QGIS (Recommandé)
1. QGIS → **Extensions** → **Gérer et installer les extensions**
2. **Paramètres** → **Ajouter**
3. Nom: `ELFADILY TopoTools`
4. URL: `https://gist.githubusercontent.com/fadili97/bb96bd92f5b47efc70bb43c846a408bd/raw/plugins.xml`
5. **OK** → Installer le plugin

🔄 **Les mises à jour seront automatiques**

### Méthode 2: Installation manuelle
1. Télécharger le dernier ZIP depuis [Releases](https://github.com/fadili97/topotools/releases)
2. QGIS → **Extensions** → **Installer depuis un ZIP**

## 🛠 Modules

### 📡 Situation sur Image Satellite
- Capture rapide d'une zone sur fond satellite (Google, Bing, ESRI)
- Export PNG/JPEG simple ou PDF avec cartouche professionnel
- Choix de l'emprise et marge paramétrable

### 📐 Points → Géométrie
- Import de coordonnées (Excel, CSV, texte)
- Formats supportés: N° X Y Z, X Y Z, N° Y X Z, Y X Z
- Génération: Polygone, Polyligne ou Points
- CRS prédéfinis pour le Maroc

### 📁 Création Shapefile
- Création de shapefile avec table attributaire personnalisable
- Templates prédéfinis: Parcelle, Borne, Voirie, Réseau, Bâtiment
- Sauvegarde de modèles personnalisés

### 🗺️ QR Code Localisation
- Cliquer sur la carte pour générer un QR code Google Maps
- Transformation automatique des coordonnées vers WGS84
- Taille du QR code paramétrable (100-1000 px)
- Export en PNG
- Copie du lien Google Maps dans le presse-papier
- **Aucune dépendance** : utilise une API en ligne gratuite

## 🚀 Développement

### Créer une nouvelle version
```bash
# Windows
release.bat 1.2.0 "Description"

# Linux/Mac
./release.sh 1.2.0 "Description"
```

### Ajouter un module
1. Créer `modules/mon_module.py`
2. Hériter de `BaseModule`
3. Enregistrer dans `plugin_main.py`

Voir `elfadily_topotools/README.md` pour plus de détails.

## 📞 Support

- **Issues**: https://github.com/fadili97/topotools/issues
- **Email**: contact@elfadilygeoconseil.com

## 📝 License

© ELFADILY GEOCONSEIL - Tous droits réservés
