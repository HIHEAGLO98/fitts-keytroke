
## Environnement de développement

### Installation de Python et PyCharm

Pour ce projet, j'ai utilisé Python 3.9 et l'IDE PyCharm de JetBrains. Voici les étapes d'installation :

**Installation de Python :**
1. Téléchargement de Python 3.9 depuis le site officiel (https://www.python.org/downloads/)
2. Installation avec l'option "Add Python to PATH" activée
3. Vérification de l'installation via la commande `python --version` dans un terminal

**Installation de PyCharm :**
1. Téléchargement de PyCharm Community Edition depuis le site de JetBrains (https://www.jetbrains.com/pycharm/download/)
2. Installation avec les options par défaut
3. Lancement de PyCharm et création d'un nouveau projet

### Configuration de l'environnement virtuel

L'utilisation d'un environnement virtuel permet d'isoler les dépendances du projet et d'éviter les conflits avec d'autres projets. PyCharm facilite grandement cette gestion :

Pour ceux qui souhaiteraient reproduire ce projet sans PyCharm, voici les commandes équivalentes :

```bash
# Création de l'environnement virtuel
python -m venv venv

# Activation sur Windows
venv\Scripts\activate

# Activation sur macOS/Linux
source venv/bin/activate
```

### Installation de PySide6

PySide6 est le binding officiel de Qt pour Python maintenu par The Qt Company. Il s'agit d'une alternative à PyQt, avec une licence plus permissive (LGPL).

Installation via PyCharm :
1. Aller dans File > Settings > Project > Python Interpreter
2. Cliquer sur "+" pour ajouter un package
3. Rechercher "PySide6" et l'installer

Ou via le terminal avec pip :
```bash
pip install PySide6
```

J'ai également installé les dépendances suivantes pour les graphiques statistiques :
```bash
pip install matplotlib numpy
```

### Installation des dépendances et démarrage

Pour faciliter l'installation des dépendances et le démarrage de l'application, suivez ces étapes après avoir configuré l'environnement virtuel :

#### Installation des dépendances

```bash
# Activation de l'environnement virtuel (si ce n'est pas déjà fait)
# Sur Windows
venv\Scripts\activate
# Sur macOS/Linux
source venv/bin/activate

# Installation des dépendances
pip install -r requirements.txt
```

Alternativement, vous pouvez installer directement les packages principaux :

```bash
# Installation des packages essentiels
pip install PySide6 matplotlib numpy
```

#### Démarrage de l'application

Une fois les dépendances installées, vous pouvez lancer l'application :

```bash
# Lancement de l'application (le point d'entrée est main.py)
python main.py
# Alternativement (si vous avez plusieurs versions de Python installées)
python3 main.py
```

##### Remarques importantes :

- Assurez-vous d'avoir Python 3.9 ou supérieur installé sur votre système
- L'environnement virtuel doit être activé à chaque fois que vous souhaitez travailler sur le projet (Sur Pycharm, il suffit d'ouvrir le terminal intégré)
- Si vous rencontrez des problèmes d'affichage avec l'interface graphique, vérifiez que PySide6 est correctement installé
