class: Workflow
cwlVersion: v1.2.0-dev2
doc: 'Abstract CWL Automatically generated from the Galaxy workflow file: COVID-19:
  PE Variation'
inputs:
  'GenBank file ':
    format: data
    type: File
  Paired Collection (fastqsanger):
    format: data
    type: File
outputs: {}
steps:
  10_Realign reads:
    in:
      reads: 8_MarkDuplicates/outFile
      reference_source|ref: 2_SnpEff build/output_fasta
    out:
    - realigned
    run:
      class: Operation
      id: toolshed_g2_bx_psu_edu_repos_iuc_lofreq_viterbi_lofreq_viterbi_2_1_3_1+galaxy1
      inputs:
        reads:
          format: Any
          type: File
        reference_source|ref:
          format: Any
          type: File
      outputs:
        realigned:
          doc: bam
          type: File
  11_MultiQC:
    in:
      results_0|software_cond|output_0|input: 8_MarkDuplicates/metrics_file
    out:
    - stats
    - plots
    - html_report
    run:
      class: Operation
      id: toolshed_g2_bx_psu_edu_repos_iuc_multiqc_multiqc_1_7_1
      inputs:
        results_0|software_cond|output_0|input:
          format: Any
          type: File
      outputs:
        html_report:
          doc: html
          type: File
        plots:
          doc: input
          type: File
        stats:
          doc: input
          type: File
  12_Call variants:
    in:
      reads: 10_Realign reads/realigned
      reference_source|ref: 2_SnpEff build/output_fasta
    out:
    - variants
    run:
      class: Operation
      id: toolshed_g2_bx_psu_edu_repos_iuc_lofreq_call_lofreq_call_2_1_3_1+galaxy0
      inputs:
        reads:
          format: Any
          type: File
        reference_source|ref:
          format: Any
          type: File
      outputs:
        variants:
          doc: vcf
          type: File
  13_SnpEff eff:
    in:
      input: 12_Call variants/variants
      snpDb|snpeff_db: 2_SnpEff build/snpeff_output
    out:
    - snpeff_output
    - statsFile
    run:
      class: Operation
      id: toolshed_g2_bx_psu_edu_repos_iuc_snpeff_snpEff_4_3+T_galaxy1
      inputs:
        input:
          format: Any
          type: File
        snpDb|snpeff_db:
          format: Any
          type: File
      outputs:
        snpeff_output:
          doc: vcf
          type: File
        statsFile:
          doc: html
          type: File
  14_SnpSift Extract Fields:
    in:
      input: 13_SnpEff eff/snpeff_output
    out:
    - output
    run:
      class: Operation
      id: toolshed_g2_bx_psu_edu_repos_iuc_snpsift_snpSift_extractFields_4_3+t_galaxy0
      inputs:
        input:
          format: Any
          type: File
      outputs:
        output:
          doc: tabular
          type: File
  15_Convert VCF to VCF_BGZIP:
    in:
      input1: 13_SnpEff eff/snpeff_output
    out:
    - output1
    run:
      class: Operation
      id: CONVERTER_vcf_to_vcf_bgzip_0
      inputs:
        input1:
          format: Any
          type: File
      outputs:
        output1:
          doc: vcf_bgzip
          type: File
  16_Collapse Collection:
    in:
      input_list: 14_SnpSift Extract Fields/output
    out:
    - output
    run:
      class: Operation
      id: toolshed_g2_bx_psu_edu_repos_nml_collapse_collections_collapse_dataset_4_1
      inputs:
        input_list:
          format: Any
          type: File
      outputs:
        output:
          doc: input
          type: File
  2_SnpEff build:
    in:
      input_type|input_gbk: 'GenBank file '
    out:
    - snpeff_output
    - output_fasta
    run:
      class: Operation
      id: toolshed_g2_bx_psu_edu_repos_iuc_snpeff_snpEff_build_gb_4_3+T_galaxy4
      inputs:
        input_type|input_gbk:
          format: Any
          type: File
      outputs:
        output_fasta:
          doc: fasta
          type: File
        snpeff_output:
          doc: snpeffdb
          type: File
  3_fastp:
    in:
      single_paired|paired_input: Paired Collection (fastqsanger)
    out:
    - output_paired_coll
    - report_html
    - report_json
    run:
      class: Operation
      id: toolshed_g2_bx_psu_edu_repos_iuc_fastp_fastp_0_19_5+galaxy1
      inputs:
        single_paired|paired_input:
          format: Any
          type: File
      outputs:
        output_paired_coll:
          doc: input
          type: File
        report_html:
          doc: html
          type: File
        report_json:
          doc: json
          type: File
  4_Map with BWA-MEM:
    in:
      fastq_input|fastq_input1: 3_fastp/output_paired_coll
      reference_source|ref_file: 2_SnpEff build/output_fasta
    out:
    - bam_output
    run:
      class: Operation
      id: toolshed_g2_bx_psu_edu_repos_devteam_bwa_bwa_mem_0_7_17_1
      inputs:
        fastq_input|fastq_input1:
          format: Any
          type: File
        reference_source|ref_file:
          format: Any
          type: File
      outputs:
        bam_output:
          doc: bam
          type: File
  5_MultiQC:
    in:
      results_0|software_cond|input: 3_fastp/report_json
    out:
    - stats
    - plots
    - html_report
    run:
      class: Operation
      id: toolshed_g2_bx_psu_edu_repos_iuc_multiqc_multiqc_1_7_1
      inputs:
        results_0|software_cond|input:
          format: Any
          type: File
      outputs:
        html_report:
          doc: html
          type: File
        plots:
          doc: input
          type: File
        stats:
          doc: input
          type: File
  6_Filter SAM or BAM, output SAM or BAM:
    in:
      input1: 4_Map with BWA-MEM/bam_output
    out:
    - output1
    run:
      class: Operation
      id: toolshed_g2_bx_psu_edu_repos_devteam_samtool_filter2_samtool_filter2_1_8+galaxy1
      inputs:
        input1:
          format: Any
          type: File
      outputs:
        output1:
          doc: sam
          type: File
  7_Samtools stats:
    in:
      input: 6_Filter SAM or BAM, output SAM or BAM/output1
    out:
    - output
    run:
      class: Operation
      id: toolshed_g2_bx_psu_edu_repos_devteam_samtools_stats_samtools_stats_2_0_2+galaxy2
      inputs:
        input:
          format: Any
          type: File
      outputs:
        output:
          doc: tabular
          type: File
  8_MarkDuplicates:
    in:
      inputFile: 6_Filter SAM or BAM, output SAM or BAM/output1
    out:
    - metrics_file
    - outFile
    run:
      class: Operation
      id: toolshed_g2_bx_psu_edu_repos_devteam_picard_picard_MarkDuplicates_2_18_2_2
      inputs:
        inputFile:
          format: Any
          type: File
      outputs:
        metrics_file:
          doc: txt
          type: File
        outFile:
          doc: bam
          type: File
  9_MultiQC:
    in:
      results_0|software_cond|output_0|type|input: 7_Samtools stats/output
    out:
    - stats
    - plots
    - html_report
    run:
      class: Operation
      id: toolshed_g2_bx_psu_edu_repos_iuc_multiqc_multiqc_1_7_1
      inputs:
        results_0|software_cond|output_0|type|input:
          format: Any
          type: File
      outputs:
        html_report:
          doc: html
          type: File
        plots:
          doc: input
          type: File
        stats:
          doc: input
          type: File

