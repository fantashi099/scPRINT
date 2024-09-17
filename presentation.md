# icon and intro slide

What can 50M cells teach us about gene networks?

# Introduction

add a math part in all slides

explain the problem and issues by also presenting existing works


## Explain scRNAseq, very large amount of data generated

Omics technologies have dramatically improved, with new modalities called single-cell RNA-seq, allowing us to measure the gene expression of individual cells.

This has dramatically increase in scale with tens of millions of cells being sequenced.

transcriptome slide:
....

Unfortunately, this has led to a challenge in data analysis due to the large scale of the input space. With over 20,000 genes or features.  x_j ∈ ℝ^n represent the gene expression vector for a single cell, where n > 20,000. d_j = f(x_j), where d_j ∈ ℝ^m and m << n.
tools to compress the data are...

large batch effects where datasets groups more by technical features like sequencer used, and how many transcripts we sequenced (also called depth)
than biological features like cell type, etc.(tools to correct for batch effects are...)
depth_j=sum_i(c_ij)

Some of the largest database of such dataset is cellxgene from the czi, totalling more than 50M cells withing 500+ datasets.
Although this still pales in comparison to the number of cells in the human body (10^13) and the human diversity of etchnicity age, disease, etc.

## Explain Gene networks

number of genes

choose other slide titles


## transformer models

re-explain the input and transformer model really well

# scPRINT

## training

## in depth overview


what do we propose that is new?


## encoder and input

## denoising & decoder

## cell embedding and bottleneck learning

## label prediction

# abilities

# showcase slide

## Assessment

# Current methods

GRN inference methods, Large Cell Models claiming to map a model of the cell and doing so, can infer meaningful gene networks

LCM == ->

GENIE3 but also GNN based, other modalities, a bunch of models

train on one dataset only, need ground truth, slow to run and small networks, mostly on ODE generated fake data

# General overview

## omnipath

## MC. Calla

## GWPS

# issues in other models and zero shot abilities

## denoising

## batch effect correction and embedding

## cell type prediction

# analysing BPH

## hubs and centrality

## overlap and gene-gene comparison

## finding communities

# availability of scPRINT

## usability example 1

## usability example 2


