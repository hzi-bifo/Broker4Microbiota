from django_q.tasks import async_task, result
# from . import hooks
from .models import MagRun, MagRunInstance
import importlib
import math
from django.conf import settings


def run_mag(mag_run, run_folder):

    sample_sheet = f"{run_folder}/samplesheet.csv"
    cluster_config = f"{run_folder}/cluster_config.cfg"

    mag_run.status = 'running'
    mag_run.save()


    # command = f"nextflow run nf-core/mag -profile docker -c {config_path} --outdir {output_folder}"
    # process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # stdout, stderr = process.communicate()

    # async_task('subprocess.run', settings.MAG_NEXTFLOW_COMMAND_STEM, f" --input {sample_sheet}", f" -profile {settings.MAG_PROFILE}", f" -c {cluster_config}", f" --outdir {run_folder}", " ", settings.MAG_ADDITIONAL_OPTIONS, shell=True, capture_output=True, hook='app.hooks.print_result')
    uuid = async_task('subprocess.run', 'sleep 30', shell=True, capture_output=True, hook='app.hooks.process_mag_result')

    mag_run_instance = MagRunInstance(MagRun=mag_run)
    mag_run_instance.run_folder = run_folder
    mag_run_instance.status = 'running'
    mag_run_instance.uuid = uuid
    mag_run_instance.save()

