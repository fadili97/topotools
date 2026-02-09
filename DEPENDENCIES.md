# Dépendances ELFADILY TopoTools

## ✅ Aucune dépendance externe requise !

Tous les modules du plugin **ELFADILY TopoTools** fonctionnent sans aucune installation de bibliothèque Python supplémentaire.

### Module QR Code Localisation

Le module **QR Code Localisation** utilise des **APIs en ligne gratuites** avec système de secours (fallback) pour générer les QR codes.

**Avantages :**
- ✅ Aucune installation requise
- ✅ Fonctionne immédiatement après installation du plugin
- ✅ Pas de problèmes de dépendances
- ✅ Système de secours multi-API (3 APIs différentes)
- ✅ Très fiable grâce aux fallbacks

**APIs utilisées (dans l'ordre) :**
1. QRServer.com (API principale)
2. QRServer.com (format alternatif)
3. QuickChart.io (secours)

Si une API est indisponible, le module essaie automatiquement la suivante.

**Prérequis :**
- Connexion internet active pour générer les QR codes
- Aucune configuration nécessaire

---

## Notes

- Tous les modules utilisent uniquement les bibliothèques intégrées à QGIS
- Le module QR Code nécessite une connexion internet lors de la génération du QR code
- Le système de fallback multi-API garantit une haute disponibilité
- Toutes les APIs utilisées sont gratuites et ne nécessitent pas d'authentification
