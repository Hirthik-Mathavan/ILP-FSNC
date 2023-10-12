# ILP-FSNC
Meta-Learning and Graph Contrastive Learning in the inductive setting for FSNC.

# Inductive Linear Probing for Few-Shot Node Classification [SBP-BRiMS 2023] [[Paper]](https://link.springer.com/chapter/10.1007/978-3-031-43129-6_27)

## Dataset 
[[Pytorch Link]](https://pytorch-geometric.readthedocs.io/en/latest/modules/datasets.html)

Sufficient number of classes: ***A***. CoraFull    ***B***. Coauthor-CS   

Insufficient number of classes: ***C***. Cora    ***D***. CiteSeer, ***E***. Amazon-Computer

## Methods
### Meta-learning 
[Full Paper List](https://github.com/kaize0409/awesome-few-shot-gnn)
|Name|Paper|Original Code
|---|---|---|
|MAML|[[ICML 2017] Model-agnostic Meta-learning for Fast Adaptation of Deep Networks](http://proceedings.mlr.press/v70/finn17a/finn17a.pdf)|[PyTorch](https://github.com/dragen1860/MAML-Pytorch)
|ProtoNet|[[NeurIPS 2017] Prototypical Networks for Few-shot Learning](https://proceedings.neurips.cc/paper/2017/file/cb8da6767461f2812ae4290eac7cbc42-Paper.pdf)|[PyTorch](https://github.com/sicara/easy-few-shot-learning)
|Meta-GNN|[[CIKM 2019] Meta-GNN: On Few-shot Node Classification in Graph Meta-learning](https://arxiv.org/pdf/1905.09718.pdf)|[PyTorch](https://github.com/ChengtaiCao/Meta-GNN)
|GPN|[[CIKM 2020] Graph Prototypical Networks for Few-shot Learning on Attributed Networks](https://arxiv.org/pdf/2006.12739.pdf)|[PyTorch](https://github.com/kaize0409/GPN_Graph-Few-shot)
|AMM-GNN|[[CIKM 2020] Graph Few-shot Learning with Attribute Matching](http://www.public.asu.edu/~kding9/pdf/CIKM2020_AMM.pdf)|[N/A]
|G-Meta|[[NeurIPS 2020] Graph Meta Learning via Local Subgraphs](https://arxiv.org/pdf/2006.07889.pdf)|[PyTorch](https://github.com/mims-harvard/G-Meta)
|TENT|[[SIGKDD 2022] Task-Adaptive Few-shot Node Classification](https://arxiv.org/pdf/2206.11972.pdf)|[PyTorch](https://github.com/SongW-SW/TENT)


## Citation
```
@InProceedings{10.1007/978-3-031-43129-6_27,
author="Mathavan, Hirthik
and Tan, Zhen
and Mudiam, Nivedh
and Liu, Huan",
editor="Thomson, Robert
and Al-khateeb, Samer
and Burger, Annetta
and Park, Patrick
and A. Pyke, Aryn",
title="Inductive Linear Probing for Few-Shot Node Classification",
booktitle="Social, Cultural, and Behavioral Modeling",
year="2023",
publisher="Springer Nature Switzerland",
address="Cham",
pages="274--284",
abstract="Meta-learning has emerged as a powerful training strategy for few-shot node classification, demonstrating its effectiveness in the transductive setting. However, the existing literature predominantly focuses on transductive few-shot node classification, neglecting the widely studied inductive setting in the broader few-shot learning community. This oversight limits our comprehensive understanding of the performance of meta-learning based methods on graph data. In this work, we conduct an empirical study to highlight the limitations of current frameworks in the inductive few-shot node classification setting. Additionally, we propose applying a competitive baseline approach specifically tailored for inductive few-shot node classification tasks. We hope our work can provide a new path forward to better understand how the meta-learning paradigm works in the graph domain.",
isbn="978-3-031-43129-6"
}
```



