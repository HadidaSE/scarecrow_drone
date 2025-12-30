#!/bin/bash
### Robustness Testing - BGU HPC Cluster
### sbatch test_robustness.sbatch

#SBATCH --partition main
#SBATCH --time 0-01:00:00           ### 1 hour should be enough
#SBATCH --job-name pigeon_robust
#SBATCH --output pigeon_robust-%J.out
#SBATCH --mail-type=BEGIN,END,FAIL

#SBATCH --gpus=1                    ### Request 1 GPU

### Print job info
echo "=========================================="
echo "SLURM Job ID: $SLURM_JOBID"
echo "Running on node: $SLURM_JOB_NODELIST"
echo "Start time: $(date)"
echo "=========================================="

### Load modules
module load anaconda
module load cuda/11.8

### Activate conda environment
source activate pigeon_detect

### Navigate to project directory
cd $HOME/pigeions

### Show GPU info
echo ""
echo "GPU Information:"
nvidia-smi -L
echo ""

### Run robustness test
python test_robustness.py

### Print completion
echo ""
echo "=========================================="
echo "Job completed: $(date)"
echo "=========================================="
