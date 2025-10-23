from django_q.tasks import async_task, result
# from . import hooks
from .models import MagRun, MagRunInstance, SubMGRunInstance, SubMGRun
import importlib
import math
import logging
from django.conf import settings
import os
import subprocess
import glob


logger = logging.getLogger(__name__)

def run_mag(mag_run, run_folder):
    project_ids = set(mag_run.reads.values_list('sample__order__project_id', flat=True))
    project_ids.discard(None)

    if mag_run.project_id:
        mismatched_projects = project_ids - {mag_run.project_id}
        if mismatched_projects:
            raise ValueError(f'MAG run {mag_run.id} includes reads from multiple projects: {sorted(mismatched_projects | {mag_run.project_id})}')
    else:
        if len(project_ids) == 1:
            mag_run.project_id = project_ids.pop()
            mag_run.save(update_fields=['project'])
        elif len(project_ids) == 0:
            logger.warning('MAG run %s has no associated project and no reads to infer project from.', mag_run.id)
        else:
            raise ValueError(f'MAG run {mag_run.id} includes reads from multiple projects and cannot determine a single project.')

    if settings.MAG_NEXTFLOW_STUB_MODE:
        run_mag_stub(mag_run, run_folder)
    else:
        run_mag_real(mag_run, run_folder)

    return

def run_mag_real(mag_run, run_folder):

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
        print(f"{settings.CONDA_PATH}/envs/broker/bin/nextflow run hzi-bifo/mag -w /tmp --input {sample_sheet} -profile singularity -c {cluster_config} --outdir {run_folder} {settings.MAG_ADDITIONAL_OPTIONS}", file=file)
        print(f"cd {run_folder}", file=file)
        for read in mag_run.reads.all():
            sample = read.sample
            print(f"assembly_file=$(find {run_folder}Assembly/MEGAHIT -name 'MEGAHIT-{sample.sample_id}.contigs.fa.gz')", file=file)
            print(f"bwa index ${{assembly_file}}", file=file)            
            print(f"bwa mem ${{assembly_file}} {read.file_1} {read.file_2} | samtools sort -o {sample.sample_id}.sorted.bam", file=file)
        print(f"cd {run_folder}/GenomeBinning/MaxBin2/Maxbin2_bins", file=file)
        print(f"gunzip *.gz", file=file)
        
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

def run_mag_stub(mag_run, run_folder):

    sample_sheet = f"{run_folder}/samplesheet.csv"
    cluster_config = f"{run_folder}/cluster_config.cfg"

    mag_run.status = 'running'
    mag_run.save()

    with open(os.path.join(run_folder, 'script.sh'), 'w') as file:
        print(f"#!/bin/bash", file=file)

        sample_count = 1
        print(f"cd {run_folder}", file=file)
        print(f"sleep 30", file=file)
        print(f"mkdir -p {run_folder}/Assembly/MEGAHIT", file=file)
        print(f"mkdir -p {run_folder}/GenomeBinning/MaxBin2/Maxbin2_bins", file=file)
        print(f"mkdir -p {run_folder}/GenomeBinning/QC", file=file) 
        print(f"cp {run_folder}/../../checkm_summary_HEADER.tsv {run_folder}/GenomeBinning/QC/checkm_summary.tsv", file=file)
        for read in mag_run.reads.all():
            if sample_count > 2:
                break
            sample = read.sample
            print(f"cp {run_folder}/../../MEGAHIT-sample_{sample_count}.contigs.fa.gz {run_folder}/Assembly/MEGAHIT/MEGAHIT-{sample.sample_id}.contigs.fa.gz", file=file)    
            print(f"cp {run_folder}/../../MEGAHIT-MaxBin2-sample_{sample_count}.001.fa {run_folder}/GenomeBinning/MaxBin2/Maxbin2_bins/MEGAHIT-MaxBin2-{sample.sample_id}.001.fa", file=file)
            print(f"cat {run_folder}/../../checkm_summary_BODY.tsv |sed -e 's/sample_1/{sample.sample_id}.001/g' >> {run_folder}/GenomeBinning/QC/checkm_summary.tsv", file=file)
            print(f"cp {run_folder}/../../sample_{sample_count}.sorted.bam {run_folder}/{sample.sample_id}.sorted.bam", file=file)      
            sample_count += 1  

    os.chmod(os.path.join(run_folder, 'script.sh'), 0o744)

    output = os.path.join(run_folder, 'output')
    error = os.path.join(run_folder, 'error')
    script_location = os.path.join(run_folder, 'script.sh')
    uuid = async_task('subprocess.run', f"{script_location}", shell=True, capture_output=True, hook='app.hooks.process_mag_result')

    mag_run_instance = MagRunInstance(magRun=mag_run)
    mag_run_instance.run_folder = run_folder
    mag_run_instance.status = 'running'
    mag_run_instance.uuid = uuid
    mag_run_instance.save()

    return




def run_submg(submg_run, run_folder):

    staging_dir = f"{run_folder}/staging"
    logging_dir = f"{run_folder}/logging"
    output = os.path.join(run_folder, 'output')
    error = os.path.join(run_folder, 'error')

    yaml_files = sorted(glob.glob(os.path.join(run_folder, "*.yaml")))
    if not yaml_files:
        raise FileNotFoundError(f"No YAML files found in {run_folder} for SubMG run {submg_run.id}")
    total_yaml_files = len(yaml_files)

    submg_run.status = 'running'
    submg_run.save()

    script_location = os.path.join(run_folder, 'script.sh')
    with open(script_location, 'w') as file:
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
        print(f'if [ -L "{staging_dir}" ]; then rm "{staging_dir}"; fi', file=file)
        print(f'if [ -L "{logging_dir}" ]; then rm "{logging_dir}"; fi', file=file)
        print(f'mkdir -p "{staging_dir}"', file=file)
        print(f'mkdir -p "{logging_dir}"', file=file)
        print(f'rm -f "{output}"', file=file)
        print(f'rm -f "{error}"', file=file)
        for index, yaml_path in enumerate(yaml_files):
            staging_with_index = f"{staging_dir}_{index}"
            logging_with_index = f"{logging_dir}_{index}"
            output_with_index = f"{output}_{index}"
            error_with_index = f"{error}_{index}"
            submit_command_parts = [
                f"{settings.CONDA_PATH}/envs/submg/bin/submg submit",
                f'--config "{yaml_path}"',
                f"--staging_dir {staging_dir}",
                f"--logging_dir {logging_dir}"
            ]
            submit_command_parts.append("--submit_samples --submit_reads --submit_assembly --submit_bins --skip_checks")
            submit_command = " ".join(submit_command_parts)
            print(f'{submit_command} > "{output}" 2> "{error}"', file=file)
            print(f'if [ -e "{staging_with_index}" ]; then rm -rf "{staging_with_index}"; fi', file=file)
            print(f'if [ -e "{logging_with_index}" ]; then rm -rf "{logging_with_index}"; fi', file=file)
            print(f'if [ -e "{output_with_index}" ]; then rm -f "{output_with_index}"; fi', file=file)
            print(f'if [ -e "{error_with_index}" ]; then rm -f "{error_with_index}"; fi', file=file)
            print(f'if [ -d "{staging_dir}" ]; then mv "{staging_dir}" "{staging_with_index}"; fi', file=file)
            print(f'if [ -d "{logging_dir}" ]; then mv "{logging_dir}" "{logging_with_index}"; fi', file=file)
            print(f'if [ -f "{output}" ]; then mv "{output}" "{output_with_index}"; fi', file=file)
            print(f'if [ -f "{error}" ]; then mv "{error}" "{error_with_index}"; fi', file=file)
            if index < total_yaml_files - 1:
                print(f'mkdir -p "{staging_dir}"', file=file)
                print(f'mkdir -p "{logging_dir}"', file=file)
            else:
                print(f'if [ -d "{staging_with_index}" ]; then ln -sfn "{staging_with_index}" "{staging_dir}"; fi', file=file)
                print(f'if [ -d "{logging_with_index}" ]; then ln -sfn "{logging_with_index}" "{logging_dir}"; fi', file=file)
                print(f'if [ -f "{output_with_index}" ]; then ln -sf "{output_with_index}" "{output}"; fi', file=file)
                print(f'if [ -f "{error_with_index}" ]; then ln -sf "{error_with_index}" "{error}"; fi', file=file)
    os.chmod(script_location, 0o744)

    if settings.USE_SLURM_FOR_SUBMG:
        submission_command = f"/usr/bin/sbatch -p {settings.MAG_NEXTFLOW_CLUSTER_QUEUE} -W {script_location}"
    else:
        submission_command = f"{script_location}"

    uuid = async_task('subprocess.run', f"{submission_command}", shell=True, capture_output=True, hook='app.hooks.process_submg_result')
    # debug only
    # uuid = async_task('subprocess.run', f"{submission_command}", shell=True, capture_output=True)

    submg_run_instance = SubMGRunInstance(subMGRun=submg_run)
    submg_run_instance.run_folder = run_folder
    submg_run_instance.status = 'running'
    submg_run_instance.uuid = uuid
    submg_run_instance.save()

    return


