from django_q.tasks import async_task, result
# from . import hooks
from .models import MagRun, MagRunInstance, SubMGRunInstance, SubMGRun
import importlib
import math
from django.conf import settings
import os
import subprocess
import glob


def run_mag(mag_run, run_folder):

    sample_sheet = f"{run_folder}/samplesheet.csv"
    cluster_config = f"{run_folder}/cluster_config.cfg"

    mag_run.status = 'running'
    mag_run.save()

    with open(os.path.join(run_folder, 'script.sh'), 'w') as file:
        print(f"#!/bin/bash", file=file)
        print(f"#SBATCH -p {settings.MAG_NEXTFLOW_CLUSTER_QUEUE}", file=file)
        print(f"#SBATCH -c {settings.MAG_NEXTFLOW_CLUSTER_CORES}", file=file)
        print(f"#SBATCH --mem='{settings.MAG_NEXTFLOW_CLUSTER_MEMORY}'", file=file)
        print(f"#SBATCH -t {settings.MAG_NEXTFLOW_CLUSTER_TIME_LIMIT}:0:0", file=file)
        print(f"#SBATCH {settings.MAG_NEXTFLOW_CLUSTER_OPTIONS}", file=file)
        print(f"source {settings.CONDA_PATH}/bin/activate broker", file=file)
        print(f"cd /tmp")        
        print(f"{settings.CONDA_PATH}/envs/broker/bin/nextflow run hzi-bifo/mag -r 3.4.0 -w /tmp --input {sample_sheet} -profile singularity -c {cluster_config} --outdir {run_folder} {settings.MAG_ADDITIONAL_OPTIONS}", file=file)
        print(f"assembly_file=$(find {run_folder} -name '*.contigs.fa.gz')", file=file)
        print(f"cd {run_folder}", file=file)
        for read in mag_run.reads.all():
            sample = read.sample
            print(f"bwa index ${{assembly_file}}", file=file)            
            print(f"bwa mem ${{assembly_file}} {read.file_1} {read.file_2} | samtools sort -o {sample.sample_id}.sorted.bam", file=file)
        print(f"cd {run_folder}/GenomeBinning/MaxBin2/Maxbin2_bins", file=file)

        bin_file_path = f"{run_folder}/GenomeBinning/MaxBin2/Maxbin2_bins/*.gz"
        bin_files = glob.glob(bin_file_path)
        for bin_file in bin_files:
            print(f"gunzip {bin_file}", file=file)
        
    os.chmod(os.path.join(run_folder, 'script.sh'), 0o744)

    output = os.path.join(run_folder, 'output')
    error = os.path.join(run_folder, 'error')
    script_location = os.path.join(run_folder, 'script.sh')
    uuid = async_task('subprocess.run', f"/usr/bin/sbatch -p cpu --output={output} --error={error} -W {script_location} ", shell=True, capture_output=True, hook='app.hooks.process_mag_result')

    mag_run_instance = MagRunInstance(magRun=mag_run)
    mag_run_instance.run_folder = run_folder
    mag_run_instance.status = 'running'
    mag_run_instance.uuid = uuid
    mag_run_instance.save()

    return

def run_submg(submg_run, run_folder):

    submg_yaml = f"{run_folder}/submg.yaml"
    staging_dir = f"{run_folder}/staging"
    logging_dir = f"{run_folder}/logging"

    submg_run.status = 'running'
    submg_run.save()

    with open(os.path.join(run_folder, 'script.sh'), 'w') as file:
        print(f"#!/bin/bash", file=file)
        print(f"#SBATCH -p {settings.MAG_NEXTFLOW_CLUSTER_QUEUE}", file=file)
        print(f"#SBATCH -c {settings.MAG_NEXTFLOW_CLUSTER_CORES}", file=file)
        print(f"#SBATCH --mem='{settings.MAG_NEXTFLOW_CLUSTER_MEMORY}'", file=file)
        print(f"#SBATCH -t {settings.MAG_NEXTFLOW_CLUSTER_TIME_LIMIT}:0:0", file=file)
        print(f"#SBATCH {settings.MAG_NEXTFLOW_CLUSTER_OPTIONS}", file=file)
        print(f"export ENA_USERNAME={settings.ENA_USERNAME}", file=file)
        print(f"export ENA_USER={settings.ENA_USER}", file=file)
        print(f"export ENA_PASSWORD={settings.ENA_PASSWORD}", file=file)
        print(f"source {settings.CONDA_PATH}/bin/activate submg", file=file)
        print(f"{settings.CONDA_PATH}/envs/submg/bin/submg submit --config {submg_yaml} --staging_dir {staging_dir} --logging_dir {logging_dir} --submit_samples --submit_reads --submit_assembly --submit_bins --skip_checks", file=file)

    os.chmod(os.path.join(run_folder, 'script.sh'), 0o744)

    output = os.path.join(run_folder, 'output')
    error = os.path.join(run_folder, 'error')
    script_location = os.path.join(run_folder, 'script.sh')

    if settings.USE_SLURM_FOR_SUBMG:
        submission_command = f"/usr/bin/sbatch -p {settings.MAG_NEXTFLOW_CLUSTER_QUEUE} --output={output} --error={error} -W {script_location}"
    else:
        submission_command = f"{script_location} > {output} 2> {error}"

    uuid = async_task('subprocess.run', f"{submission_command}", shell=True, capture_output=True, hook='app.hooks.process_submg_result')

    submg_run_instance = SubMGRunInstance(subMGRun=submg_run)
    submg_run_instance.run_folder = run_folder
    submg_run_instance.status = 'running'
    submg_run_instance.uuid = uuid
    submg_run_instance.save()

    return


