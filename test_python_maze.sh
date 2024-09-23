#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.

for x in $(seq 2 1 20); do
    for y in $(seq 2 1 20); do
        for z in $(seq 2 1 20); do
            echo "Taille: $x x $y x $z"
            output=$(python ./python_maze.py --clear -x $x -y $y -z $z -s 1 2>&1) || {
                echo "Erreur détectée pour la taille $x x $y x $z"
                echo "Sortie du programme :"
                echo "$output"
                exit 1
            }
        done
    done
done

echo "Tous les tests ont réussi!"
