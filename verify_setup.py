#!/usr/bin/env python3
"""
ELFADILY TopoTools - Setup Verification Script
Vérifie que tout est correctement configuré pour le déploiement
"""

import os
import sys
import re
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}[OK] {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}[WARN] {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}[ERROR] {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}[INFO] {msg}{Colors.END}")

def print_header(msg):
    print(f"\n{Colors.BOLD}{msg}{Colors.END}")
    print("=" * 60)

def check_file_exists(filepath, name):
    """Check if a file exists"""
    if Path(filepath).exists():
        print_success(f"{name} existe")
        return True
    else:
        print_error(f"{name} manquant: {filepath}")
        return False

def check_metadata():
    """Vérifie metadata.txt"""
    print_header("Verification metadata.txt")

    metadata_path = "elfadily_topotools/metadata.txt"
    if not check_file_exists(metadata_path, "metadata.txt"):
        return False

    metadata = {}
    with open(metadata_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('['):
                key, value = line.split('=', 1)
                metadata[key.strip()] = value.strip()

    required_fields = [
        'name', 'version', 'qgisMinimumVersion', 'description',
        'author', 'email', 'repository', 'tracker'
    ]

    all_ok = True
    for field in required_fields:
        if field in metadata and metadata[field]:
            print_success(f"{field}: {metadata[field][:50]}...")
        else:
            print_error(f"{field} manquant ou vide")
            all_ok = False

    # Check repository URL format
    if 'repository' in metadata:
        repo_url = metadata['repository']
        if re.match(r'https://github\.com/[\w-]+/[\w-]+', repo_url):
            print_success(f"URL repository valide: {repo_url}")
        else:
            print_warning(f"URL repository peut être invalide: {repo_url}")

    return all_ok

def check_github_workflow():
    """Vérifie le workflow GitHub Actions"""
    print_header("Verification GitHub Actions Workflow")

    workflow_path = ".github/workflows/release.yml"
    if not check_file_exists(workflow_path, "release.yml"):
        return False

    with open(workflow_path, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = [
        ('on:', 'Trigger configuré'),
        ('tags:', 'Tags configurés'),
        ('v*.*.*', 'Pattern de version correct'),
        ('actions/checkout@v4', 'Checkout action présent'),
        ('Create GitHub Release', 'Étape de release présente'),
        ('Generate plugins.xml', 'Génération XML présente'),
        ('GitHub Pages', 'Déploiement Pages présent'),
    ]

    all_ok = True
    for pattern, desc in checks:
        if pattern in content:
            print_success(desc)
        else:
            print_error(f"{desc} manquant")
            all_ok = False

    return all_ok

def check_plugin_structure():
    """Vérifie la structure du plugin"""
    print_header("Verification Structure du Plugin")

    required_files = [
        ('elfadily_topotools/__init__.py', '__init__.py'),
        ('elfadily_topotools/plugin_main.py', 'plugin_main.py'),
        ('elfadily_topotools/base_module.py', 'base_module.py'),
        ('elfadily_topotools/metadata.txt', 'metadata.txt'),
    ]

    required_dirs = [
        ('elfadily_topotools/modules', 'modules/'),
        ('elfadily_topotools/icons', 'icons/'),
    ]

    all_ok = True
    for filepath, name in required_files:
        if not check_file_exists(filepath, name):
            all_ok = False

    for dirpath, name in required_dirs:
        if Path(dirpath).is_dir():
            print_success(f"{name} existe")
        else:
            print_error(f"{name} manquant")
            all_ok = False

    # Count modules
    modules_path = Path('elfadily_topotools/modules')
    if modules_path.exists():
        modules = [f for f in modules_path.glob('*.py') if f.name != '__init__.py']
        print_info(f"{len(modules)} module(s) trouvé(s): {', '.join([m.stem for m in modules])}")

    return all_ok

def check_git():
    """Vérifie la configuration Git"""
    print_header("Verification Configuration Git")

    if not Path('.git').exists():
        print_error("Pas de dépôt Git initialisé")
        print_info("Exécutez: git init")
        return False

    print_success("Dépôt Git initialisé")

    # Check remote
    try:
        import subprocess
        result = subprocess.run(['git', 'remote', '-v'],
                              capture_output=True, text=True)
        if result.stdout:
            print_success("Remote Git configuré")
            print_info(result.stdout.strip())
        else:
            print_warning("Aucun remote Git configuré")
            print_info("Exécutez: git remote add origin <url>")
    except:
        print_warning("Impossible de vérifier les remotes")

    return True

def check_gitignore():
    """Vérifie .gitignore"""
    print_header("Verification .gitignore")

    if not check_file_exists('.gitignore', '.gitignore'):
        print_warning("Créez un .gitignore pour exclure les fichiers inutiles")
        return False

    with open('.gitignore', 'r') as f:
        content = f.read()

    important_patterns = [
        ('__pycache__', 'Cache Python'),
        ('*.pyc', 'Fichiers compilés Python'),
        ('user_templates.json', 'Données utilisateur'),
    ]

    for pattern, desc in important_patterns:
        if pattern in content:
            print_success(f"{desc} exclu")
        else:
            print_warning(f"{desc} non exclu ({pattern})")

    return True

def print_summary(checks):
    """Affiche le résumé"""
    print_header("Résumé")

    total = len(checks)
    passed = sum(checks.values())

    print(f"\nRésultat: {passed}/{total} vérifications réussies")

    if passed == total:
        print_success("Tout est configuré correctement!")
        print_info("\nProchaines étapes:")
        print("  1. git add .")
        print("  2. git commit -m 'Setup automated releases'")
        print("  3. git push origin main")
        print("  4. Créez une release avec: release.bat 1.0.0 'Initial release'")
    else:
        print_warning(f"{total - passed} problème(s) détecté(s)")
        print_info("Corrigez les erreurs ci-dessus avant de déployer")

def main():
    # Set UTF-8 encoding for Windows console
    if sys.platform == 'win32':
        import codecs
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

    print(f"{Colors.BOLD}")
    print("=" * 60)
    print("   ELFADILY TopoTools - Verification de Configuration")
    print("=" * 60)
    print(f"{Colors.END}")

    checks = {
        'metadata': check_metadata(),
        'workflow': check_github_workflow(),
        'structure': check_plugin_structure(),
        'git': check_git(),
        'gitignore': check_gitignore(),
    }

    print_summary(checks)

    # Exit code
    sys.exit(0 if all(checks.values()) else 1)

if __name__ == '__main__':
    main()
