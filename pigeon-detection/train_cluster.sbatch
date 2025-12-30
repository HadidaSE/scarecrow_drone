#!/bin/bash
### Pigeon Detection Training - BGU HPC Cluster
### sbatch train_cluster.sbatch

#SBATCH --partition main
#SBATCH --time 0-04:00:00           ### 4 hours should be plenty for YOLOv8n
#SBATCH --job-name pigeon_yolo
#SBATCH --output pigeon_train-%J.out
#SBATCH --mail-type=BEGIN,END,FAIL
##SBATCH --mail-user=YOUR_EMAIL@post.bgu.ac.il   ### Uncomment and set your email

#SBATCH --gpus=rtx_6000:1            ### Request 1x RTX 6000
#SBATCH --mem=64G                     ### Request 64GB RAM for large dataset

### Print job info
echo "=========================================="
echo "SLURM Job ID: $SLURM_JOBID"
echo "Running on node: $SLURM_JOB_NODELIST"
echo "Start time: $(date)"
echo "=========================================="

### Load modules
module load anaconda
module load cuda/11.8

### Activate conda environment (create first if needed - see setup instructions below)
source activate pigeon_detect

### Navigate to project directory
cd $HOME/pigeions

### Show GPU info
echo ""
echo "GPU Information:"
nvidia-smi -L
echo ""

### Run training with GPU
python train_gpu.py

### Print completion
echo ""
echo "=========================================="
echo "Job completed: $(date)"
echo "=========================================="

### ============================================
### SETUP INSTRUCTIONS (run once on login node):
### ============================================
###
### 1. SSH to cluster:
###    ssh YOUR_USER@slurm.bgu.ac.il
###
### 2. Create conda environment:
###    conda create -n pigeon_detect python=3.10
###    conda activate pigeon_detect
###    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
###    pip install ultralytics opencv-python numpy pyyaml
###    conda deactivate
###
### 3. Upload project files:
###    - Use WinSCP or scp to copy pigeon-detection/ folder to $HOME/pigeon-detection/
###    - Make sure to include the dataset in data/images/pigeons.v1i.yolov8/
###
### 4. Submit job:
###    sbatch train_cluster.sbatch
###
### 5. Monitor job:
###    squeue --me                    # Check job status
###    tail -f pigeon_train-JOBID.out # Watch output
###    scancel JOBID                  # Cancel if needed
### ============================================
