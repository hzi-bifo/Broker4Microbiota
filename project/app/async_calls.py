from django_q.tasks import async_task, result
# from . import hooks
from .models import MagRun, MagRunInstance, SubMGRunInstance, SubMGRun
import importlib
import math
from django.conf import settings
import os
import subprocess


def run_mag(mag_run, run_folder):

    sample_sheet = f"{run_folder}/samplesheet.csv"
    cluster_config = f"{run_folder}/cluster_config.cfg"

    mag_run.status = 'running'
    mag_run.save()


    # command = f"nextflow run nf-core/mag -profile docker -c {config_path} --outdir {output_folder}"
    # process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # stdout, stderr = process.communicate()

    # async_task('subprocess.run', settings.MAG_NEXTFLOW_COMMAND_STEM, f" --input {sample_sheet}", f" -profile {settings.MAG_PROFILE}", f" -c {cluster_config}", f" --outdir {run_folder}", " ", settings.MAG_ADDITIONAL_OPTIONS, shell=True, capture_output=True, hook='app.hooks.print_result')
    # uuid = async_task('subprocess.run', 'sleep 30', shell=True, capture_output=True, hook='app.hooks.process_mag_result')

    with open(os.path.join(run_folder, 'script.sh'), 'w') as file:
        print(f"#!/bin/bash", file=file)
        print(f"#SBATCH -p {settings.MAG_NEXTFLOW_CLUSTER_QUEUE}", file=file)
        print(f"#SBATCH -c {settings.MAG_NEXTFLOW_CLUSTER_CORES}", file=file)
        print(f"#SBATCH --mem='{settings.MAG_NEXTFLOW_CLUSTER_MEMORY}'", file=file)
        print(f"#SBATCH -t {settings.MAG_NEXTFLOW_CLUSTER_TIME_LIMIT}:0:0", file=file)
        print(f"#SBATCH {settings.MAG_NEXTFLOW_CLUSTER_OPTIONS}", file=file)
        print(f"source /net/broker/test/miniconda3/bin/activate broker", file=file)
        print(f"/net/broker/test/miniconda3/envs/broker/bin/nextflow run hzi-bifo/mag --input {sample_sheet} -profile singularity -c {cluster_config} --outdir {run_folder} {settings.MAG_ADDITIONAL_OPTIONS}", file=file)
        print(f"assembly_file=$(find {run_folder} -name '*.contigs.fa.gz')", file=file)
        for read in mag_run.reads.all():
            sample = read.sample
            print(f"bwa mem ${{assembly_file}} {read.file_1} {read.file_2} | samtools sort -o {sample.sample_id}.sorted.bam", file=file)
        
        # print(f"/usr/bin/srun -p cpu . /net/broker/test/miniconda3/bin/activate broker; /net/broker/test/miniconda3/envs/broker/bin/nextflow run hzi-bifo/mag --input {sample_sheet} -profile singularity -c {cluster_config} --outdir {run_folder} {settings.MAG_ADDITIONAL_OPTIONS}", file=file)
    os.chmod(os.path.join(run_folder, 'script.sh'), 0o744)

    output = os.path.join(run_folder, 'output')
    error = os.path.join(run_folder, 'error')
    script_location = os.path.join(run_folder, 'script.sh')
    uuid = async_task('subprocess.run', f"/usr/bin/sbatch -p cpu --output={output} --error={error} -W {script_location} ", shell=True, capture_output=True, hook='app.hooks.process_mag_result')
    # subprocess.run', f"/usr/bin/sbatch", f" -p cpu --output={output} --error={error} -W ", os.path.join(run_folder, 'script.sh'), shell=True, capture_output=True, hook='app.hooks.process_mag_result')

    mag_run_instance = MagRunInstance(MagRun=mag_run)
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


    # command = f"nextflow run nf-core/mag -profile docker -c {config_path} --outdir {output_folder}"
    # process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # stdout, stderr = process.communicate()

    # async_task('subprocess.run', settings.MAG_NEXTFLOW_COMMAND_STEM, f" --input {sample_sheet}", f" -profile {settings.MAG_PROFILE}", f" -c {cluster_config}", f" --outdir {run_folder}", " ", settings.MAG_ADDITIONAL_OPTIONS, shell=True, capture_output=True, hook='app.hooks.print_result')
    # uuid = async_task('subprocess.run', 'sleep 30', shell=True, capture_output=True, hook='app.hooks.process_mag_result')

    with open(os.path.join(run_folder, 'script.sh'), 'w') as file:
        print(f"#!/bin/bash", file=file)
        print(f"#SBATCH -p {settings.MAG_NEXTFLOW_CLUSTER_QUEUE}", file=file)
        print(f"#SBATCH -c {settings.MAG_NEXTFLOW_CLUSTER_CORES}", file=file)
        print(f"#SBATCH --mem='{settings.MAG_NEXTFLOW_CLUSTER_MEMORY}'", file=file)
        print(f"#SBATCH -t {settings.MAG_NEXTFLOW_CLUSTER_TIME_LIMIT}:0:0", file=file)
        print(f"#SBATCH {settings.MAG_NEXTFLOW_CLUSTER_OPTIONS}", file=file)
        # print(f"source /net/broker/test/miniconda3/bin/activate submg", file=file)
        # print(f"/net/broker/test/miniconda3/envs/brokersubmg/bin/submg submit --config {submg_yaml} --staging_dir {staging_dir} --logging_dir {logging_dir} --submit_samples --submit_reads --submit_assembly --submit_bins --skip_checks", file=file)
        print(f"conda activate submg", file=file)
        print(f"/home/gary/miniforge3/envs/submg/bin/submg submit --config {submg_yaml} --staging_dir {staging_dir} --logging_dir {logging_dir} --submit_samples --submit_reads --submit_assembly --submit_bins --skip_checks", file=file)

    os.chmod(os.path.join(run_folder, 'script.sh'), 0o744)

    output = os.path.join(run_folder, 'output')
    error = os.path.join(run_folder, 'error')
    script_location = os.path.join(run_folder, 'script.sh')
    # uuid = async_task('subprocess.run', f"/usr/bin/sbatch -p cpu --output={output} --error={error} -W {script_location} ", shell=True, capture_output=True, hook='app.hooks.process_submg_result')
    uuid = async_task('subprocess.run', f"{script_location} > /tmp/out 2> /tmp/err", shell=True, capture_output=True, hook='app.hooks.process_submg_result')
    # subprocess.run', f"/usr/bin/sbatch", f" -p cpu --output={output} --error={error} -W ", os.path.join(run_folder, 'script.sh'), shell=True, capture_output=True, hook='app.hooks.process_mag_result')

    submg_run_instance = SubMGRunInstance(subMGRun=submg_run)
    submg_run_instance.run_folder = run_folder
    submg_run_instance.status = 'running'
    submg_run_instance.uuid = uuid
    submg_run_instance.save()

    return


