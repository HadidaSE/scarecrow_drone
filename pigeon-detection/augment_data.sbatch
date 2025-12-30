#!/bin/bash
#SBATCH --partition main
#SBATCH --time 0-01:00:00
#SBATCH --job-name pigeon_augment
#SBATCH --output pigeon_augment-%J.out
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G

echo "=========================================="
echo "Starting data augmentation: $(date)"
echo "=========================================="

module load anaconda
source activate pigeon_detect

cd $HOME/pigeions

python augment_small_pigeons.py

echo "=========================================="
echo "Augmentation completed: $(date)"
echo "=========================================="
