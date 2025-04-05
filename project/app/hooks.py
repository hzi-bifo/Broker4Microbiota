from django_q.tasks import async_task, result
from .models import MagRun, MagRunInstance, Assembly, Bin, Order, Alignment
import re
from pathlib import Path
import glob


def process_mag_result(task):


    mag_run_instance = MagRunInstance.objects.get(uuid=task.id)
    mag_run = MagRun.objects.get(id=mag_run_instance.MagRun.id)

    if task.result.returncode != 0:
        mag_run_instance.status = 'failed'
        mag_run.status = 'failed'
    else:
        mag_run_instance.status = 'completed'
        mag_run.status = 'completed'

        run_folder = mag_run_instance.run_folder

        reads = mag_run.reads.all()
        for read in reads:
            # file_name = re.sub(f"_R1.fastq.gz", f"", re.sub(f"_1.fastq.gz", f"", read.file_1.split('/')[-1]))

            sample = read.sample
            order = sample.order
            project = order.project

            assembly_file_path = f"{run_folder}/Assembly/MEGAHIT/MEGAHIT-{sample.sample_id}.contigs.fa.gz"
            assembly_file = Path(assembly_file_path)
            if assembly_file.is_file():
                assembly = Assembly(read=read, file=assembly_file, order=order)
                assembly.save()
            else:
                mag_run_instance.status = 'partial'
                mag_run.status = 'partial'

            bin_file_path = f"{run_folder}/GenomeBinning/MaxBin2/Maxbin2_bins/MEGAHIT-MaxBin2-{sample.sample_id}.[0-9][0-9][0-9].fa.gz"
            bin_files = glob.glob(bin_file_path)
            for bin_file in bin_files:
                bin = Bin(read=read, file=bin_file, order=order)
                bin.save()
            if bin_files == []:
                mag_run_instance.status = 'partial'
                mag_run.status = 'partial'

            alignment_file_path = f"{run_folder}/Assembly/MEGAHIT/{sample.sample_id}.sorted.bam"
            alignment_files = Path(alignment_file_path)
            for alignment_file in alignment_files:
                alignment = Alignment(read=read, file=alignment_file, order=order)
                alignment.save()
            if alignment_files == []:
                mag_run_instance.status = 'partial'
                mag_run.status = 'partial'

        mag_run_instance.save()
        mag_run.save()

def process_submg_result(task):
    pass