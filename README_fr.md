# Générateur de Labyrinthe pour Blender

Un plugin Blender pour générer des labyrinthes 3D complexes et personnalisables.

[English version](README_en.md)

## Fonctionnalités

- Génère des labyrinthes 3D avec des dimensions personnalisables
- S'intègre parfaitement dans l'interface de Blender
- Crée des structures de labyrinthe optimisées et prêtes à l'emploi
- Offre des options de personnalisation pour l'épaisseur des murs et l'espacement

## Installation

1. Clonez ce dépôt :
   ```
   git clone https://github.com/votre-nom/blender-maze.git
   ```

2. Copiez le fichier `python_maze_blender_addon.py` dans le dossier des addons de Blender :
   - Windows : `%APPDATA%\\Blender Foundation\\Blender\\<version>\\scripts\\addons`
   - macOS : `/Users/<user>/Library/Application Support/Blender/<version>/scripts/addons`
   - Linux : `~/.config/blender/<version>/scripts/addons`

3. Activez l'addon dans Blender :
   - Allez dans Edit > Preferences > Add-ons
   - Recherchez "Maze Generator"
   - Cochez la case pour activer l'addon

## Utilisation

1. Dans Blender, allez dans "Add > Mesh > Maze v0.1"
2. Un labyrinthe 3D sera généré avec les dimensions par défaut (18x15x4)
3. Modifiez les propriétés du labyrinthe dans le panneau des propriétés de l'objet si nécessaire

## Configuration

Le projet utilise Poetry pour la gestion des dépendances. Pour installer les dépendances :

```
poetry install
```

## Développement

Pour contribuer au projet :

1. Forkez le dépôt
2. Créez votre branche de fonctionnalité (`git checkout -b feature/NouvellefonctionnaliteIncroyable`)
3. Committez vos changements (`git commit -m 'Ajout de NouvellefonctionnaliteIncroyable'`)
4. Poussez vers la branche (`git push origin feature/NouvellefonctionnaliteIncroyable`)
5. Ouvrez une Pull Request

## Licence

Distribué sous la licence MIT. Voir `LICENSE` pour plus d'informations.

## Contact

Olivier Pons - olivier.pons@gmail.com

Lien du projet : [https://github.com/votre-nom/blender-maze](https://github.com/votre-nom/blender-maze)
