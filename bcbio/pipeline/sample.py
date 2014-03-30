"""High level entry point for processing a sample.

Samples may include multiple lanes, or barcoded subsections of lanes,
processed together.
"""
import os
import copy

from bcbio.log import logger
from bcbio.pipeline.merge import (combine_fastq_files, merge_bam_files)
from bcbio.pipeline import config_utils

# ## Merging

def merge_sample(data):
    """Merge fastq and BAM files for multiple samples.
    """
    logger.debug("Combining fastq and BAM files %s" % str(data["name"]))
    config = config_utils.update_w_custom(data["config"], data["info"])
    if config["algorithm"].get("upload_fastq", False):
        fastq1, fastq2 = combine_fastq_files(data["fastq_files"], data["dirs"]["work"],
                                             config)
    else:
        fastq1, fastq2 = None, None

    out_file = os.path.join(data["dirs"]["work"],
                            data["info"]["rgnames"]["sample"] + ".bam")
    sort_bam = merge_bam_files(data["bam_files"], data["dirs"]["work"],
                               config, out_file=out_file)
    return [[{"name": data["name"], "metadata": data["info"].get("metadata", {}),
              "info": data["info"],
              "genome_build": data["genome_build"], "sam_ref": data["sam_ref"],
              "work_bam": sort_bam, "fastq1": fastq1, "fastq2": fastq2,
              "dirs": data["dirs"], "config": config,
              "config_file": data["config_file"]}]]

def delayed_bam_merge(data):
    """Perform a merge on previously prepped files, delayed in processing.
    """
    if data.get("combine"):
        assert len(data["combine"].keys()) == 1
        file_key = data["combine"].keys()[0]
        in_files = sorted(list(set([data[file_key]] + data["combine"][file_key].get("extras", []))))
        out_file = data["combine"][file_key]["out"]
        logger.debug("Combining BAM files to %s" % out_file)
        config = copy.deepcopy(data["config"])
        config["algorithm"]["save_diskspace"] = False
        merged_file = merge_bam_files(in_files, os.path.dirname(out_file), config,
                                      out_file=out_file)
        data.pop("region", None)
        data.pop("combine", None)
        data[file_key] = merged_file
    return [[data]]
