class: Workflow
cwlVersion: v1.2.0-dev2
doc: 'Abstract CWL Automatically generated from the Galaxy workflow file: Workflow
  constructed from history ''Minimal-history'''
inputs:
  dataset1_txt:
    format: data
    type: File
  dataset2_txt:
    format: data
    type: File
outputs: {}
steps:
  2_Concatenate datasets:
    in:
      input1: dataset2_txt
      queries_0|input2: dataset1_txt
    out:
    - out_file1
    run:
      class: Operation
      id: cat1
      inputs:
        input1:
          format: Any
          type: File
        queries_0|input2:
          format: Any
          type: File
      outputs:
        out_file1:
          doc: input
          type: File
  3_Select random lines:
    in:
      input: 2_Concatenate datasets/out_file1
    out:
    - out_file1
    run:
      class: Operation
      id: random_lines1
      inputs:
        input:
          format: Any
          type: File
      outputs:
        out_file1:
          doc: input
          type: File

