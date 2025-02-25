from django_q.tasks import async_task, result
from .models import MagRun, MagRunInstance, Assembly, Bin, Order
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

        sequences = mag_run.sequences.all()
        for sequence in sequences:
            file_name = re.sub(f"_R1.fastq.gz", f"", sequence.file_1.split('/')[-1])

            sample = sequence.sample
            order = sample.order
            project = order.project

            assembly_file_path = f"{run_folder}/Assembly/MEGAHIT/MEGAHIT-{file_name}.contigs.fa.gz"
            assembly_file = Path(assembly_file_path)
            if assembly_file.is_file():
                assembly = Assembly(sequence=sequence, file=assembly_file_path, order=order)
                assembly.save()
            else:
                mag_run_instance.status = 'partial'
                mag_run.status = 'partial'

            bin_file_path = f"{run_folder}/GenomeBinning/MaxBin2/Maxbin2_bins/MEGAHIT-MaxBin2-{file_name}.[0-9][0-9][0-9].fa.gz"
            bin_files = glob.glob(bin_file_path)
            for bin_file in bin_files:
                bin = Bin(sequence=sequence, file=bin_file_path, order=order)
                bin.save()
            if bin_files == []:
                mag_run_instance.status = 'partial'
                mag_run.status = 'partial'

        mag_run_instance.save()
        mag_run.save()
