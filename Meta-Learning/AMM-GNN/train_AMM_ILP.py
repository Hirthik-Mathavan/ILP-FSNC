import networkx as nx
import numpy as np
import random
import torch
import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from sklearn.model_selection import StratifiedKFold
import sys
import scipy
import sklearn
import json
from collections import defaultdict
import torch.optim as optim
import torch.nn as nn
import torch.nn.functional as F
import argparse
import math
import pickle as pkl
import scipy.sparse as sp
import time
import scipy.io as sio
import random
from sklearn import preprocessing
from sklearn.metrics import f1_score
# import contrast_util
import json
import os
# import GCL.losses as L
# import GCL.augmentors as A

# from GCL.eval import get_split, LREvaluator
# from GCL.models import DualBranchContrast
from base_model_SSL import GCN_dense
from base_model_SSL import Linear
from base_model_SSL import GCN_emb


# from base_model import GCN

def normalize(mx):
    """Row-normalize sparse matrix"""
    rowsum = np.array(mx.sum(1))
    r_inv = np.power(rowsum, -1).flatten()
    r_inv[np.isinf(r_inv)] = 0.
    r_mat_inv = sp.diags(r_inv)
    mx = r_mat_inv.dot(mx)
    return mx


def normalize_adj(adj):
    """Symmetrically normalize adjacency matrix."""
    adj = sp.coo_matrix(adj)
    rowsum = np.array(adj.sum(1))
    d_inv_sqrt = np.power(rowsum, -0.5).flatten()
    d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.
    d_mat_inv_sqrt = sp.diags(d_inv_sqrt)
    return adj.dot(d_mat_inv_sqrt).transpose().dot(d_mat_inv_sqrt).tocoo()


def accuracy(output, labels):
    preds = output.max(1)[1].type_as(labels)
    correct = preds.eq(labels).double()
    correct = correct.sum()
    return correct / len(labels)


def f1(output, labels):
    preds = output.max(1)[1].type_as(labels)
    f1 = f1_score(labels, preds, average='weighted')
    return f1


def sparse_mx_to_torch_sparse_tensor(sparse_mx):
    """Convert a scipy sparse matrix to a torch sparse tensor."""
    sparse_mx = sparse_mx.tocoo().astype(np.float32)
    indices = torch.from_numpy(
        np.vstack((sparse_mx.row, sparse_mx.col)).astype(np.int64))
    values = torch.from_numpy(sparse_mx.data)
    shape = torch.Size(sparse_mx.shape)
    return torch.sparse.FloatTensor(indices, values, shape)


def cal_euclidean(input):
    # input tensor
    #a = input.unsqueeze(0).repeat([input.shape[0], 1, 1])
    #b = input.unsqueeze(1).repeat([1, input.shape[0], 1])
    #distance = (a - b).square().sum(-1)
    distance = torch.cdist(input.unsqueeze(0),input.unsqueeze(0)).squeeze()
    
    return distance


def load_npz_to_sparse_graph(file_name):
    """Load a SparseGraph from a Numpy binary file.
    Parameters
    ----------
    file_name : str
        Name of the file to load.
    Returns
    -------
    sparse_graph : SparseGraph
        Graph in sparse matrix format.
    """
    with np.load(file_name) as loader:
        loader = dict(loader)
        adj_matrix = sp.csr_matrix((loader['adj_data'], loader['adj_indices'], loader['adj_indptr']),
                                   shape=loader['adj_shape'])

        if 'attr_data' in loader:
            # Attributes are stored as a sparse CSR matrix
            attr_matrix = sp.csr_matrix((loader['attr_data'], loader['attr_indices'], loader['attr_indptr']),
                                        shape=loader['attr_shape'])
        elif 'attr_matrix' in loader:
            # Attributes are stored as a (dense) np.ndarray
            attr_matrix = loader['attr_matrix']
        else:
            attr_matrix = None

        if 'labels_data' in loader:
            # Labels are stored as a CSR matrix
            labels = sp.csr_matrix((loader['labels_data'], loader['labels_indices'], loader['labels_indptr']),
                                   shape=loader['labels_shape'])
        elif 'labels' in loader:
            # Labels are stored as a numpy array
            labels = loader['labels']
        else:
            labels = None

        node_names = loader.get('node_names')
        attr_names = loader.get('attr_names')
        class_names = loader.get('class_names')
        metadata = loader.get('metadata')

    return adj_matrix, attr_matrix, labels, node_names, attr_names, class_names, metadata


valid_num_dic = {'Amazon_clothing': 17, 'Amazon_eletronics': 36, 'dblp': 27}





class_split = {
    "CoraFull": {"train": 38, 'dev': 13, 'test': 19},  # Sufficient number of base classes
    "ogbn-arxiv": {"train": 20, 'dev': 10, 'test': 10},
    "Coauthor-CS": {"train": 5, 'dev': 5, 'test': 5},
    "Amazon-Computer": {"train": 4, 'dev': 3, 'test': 3},
    "Cora": {"train": 3, 'dev': 2, 'test': 2},
    "CiteSeer": {"train": 2, 'dev': 2, 'test': 2},
}


config = {
    "seed": 1234,
    "dataset": "Amazon-Computer", # CoraFull(70)/Coauthor-CS(15)/ogbn-arxiv(40)/Cora(7)/Amazon-Computer(10)/CiteSeer(6)
    "batch_size": 4,
    "n_way": 2,
    "k_shot": 5,
    "m_qry": 10,
    "test_num": 20,
    "patience": 10,
    "sup": False,
    "epoch_num": 10000,
}



def load_data_pretrain(dataset_source, inductive = False):
    from torch_geometric.utils import to_dense_adj, dense_to_sparse, subgraph
    from ogb.nodeproppred import PygNodePropPredDataset
    from torch_geometric.datasets import CoraFull, Coauthor, Planetoid, Amazon

    if dataset_source=='ogbn-arxiv':
        dataset = PygNodePropPredDataset(root='../dataset/ogbn-arxiv', name='ogbn-arxiv')
    elif dataset_source=='CoraFull':
        dataset = CoraFull(root='../dataset/corafull')
    elif dataset_source=='Coauthor-CS':
        dataset= Coauthor(root='../dataset/coauthor-cs',name='CS')
    elif dataset_source=='Cora':
        dataset=Planetoid(root='../dataset/cora',name='Cora')
    elif dataset_source=='CiteSeer':
        dataset=Planetoid(root='../dataset/citeseer',name='CiteSeer')
    elif dataset_source=='Amazon-Computer':
        dataset=Amazon(root='../dataset/amazon',name='Computers')

    graph=dataset[0]


    labels = graph.y.squeeze()
    class_num=(labels.max()+1).item()

    n1s=graph.edge_index[0]
    n2s=graph.edge_index[1]

    num_nodes = graph.x.shape[0]
    print('nodes num',num_nodes)
    adj = sp.coo_matrix((np.ones(len(n1s)), (n1s, n2s)),
                            shape=(num_nodes, num_nodes))    
    degree = np.sum(adj, axis=1)
    degree = torch.FloatTensor(degree)
    adj = normalize(adj + sp.eye(adj.shape[0]))
    adj = sparse_mx_to_torch_sparse_tensor(adj)

    features=graph.x

    train_class_num=class_split[dataset_source]['train']
    valid_class_num=class_split[dataset_source]['dev']
    test_class_num=class_split[dataset_source]['test']
        
    class_list_test = np.random.choice(list(range(class_num)),test_class_num,replace=False).tolist()
    train_class=list(set(list(range(class_num))).difference(set(class_list_test)))
    class_list_valid = np.random.choice(train_class,valid_class_num, replace=False).tolist()
    class_list_train = list(set(train_class).difference(set(class_list_valid)))
    


    idx_train, idx_valid, idx_test = [], [], []

    for i in range(labels.shape[0]):
        if labels[i] in class_list_train:
            idx_train.append(i)
        elif labels[i] in class_list_valid:
            idx_valid.append(i)
        else:
            idx_test.append(i)
    if inductive:
        # subgraph
        gen_subgraph_edge_index, _ = subgraph(idx_train, graph.edge_index)
        # start and end nodes
        n1s=gen_subgraph_edge_index[0]
        n2s=gen_subgraph_edge_index[1]

        #Creating sparse matrix in COO format
        # dimension of the adj matrix changes between inductive and transductive
        adj = sp.coo_matrix((np.ones(len(n1s)), (n1s, n2s)),
                            shape=(num_nodes, num_nodes))
        # Degree of each node
        degree = np.sum(adj, axis=1)
        degree = torch.FloatTensor(degree)

        #Adj matrix
        adj = normalize(adj + sp.eye(adj.shape[0]))
        adj = sparse_mx_to_torch_sparse_tensor(adj)
   
    class_train_dict = defaultdict(list)
    for one in class_list_train:
        for i, label in enumerate(labels.numpy().tolist()):
            if label == one:
                class_train_dict[one].append(i)
                
    class_valid_dict = defaultdict(list)
    for one in class_list_valid:
        for i, label in enumerate(labels.numpy().tolist()):
            if label == one:
                class_valid_dict[one].append(i)

                
                
    class_test_dict = defaultdict(list)
    for one in class_list_test:
        for i, label in enumerate(labels.numpy().tolist()):
            if label == one:
                class_test_dict[one].append(i)

    print(len(idx_train))
    print(len(idx_train) + len(idx_valid))
    print(features.shape[0])



    
    
    return adj, features, labels, idx_train, idx_valid, idx_test, n1s, n2s, class_train_dict, class_test_dict, class_valid_dict


def neighborhoods_(adj, n_hops, use_cuda):
    """Returns the n_hops degree adjacency matrix adj."""
    # adj = torch.tensor(adj, dtype=torch.float)
    # adj=adj.to_dense()
    # print(type(adj))
    if use_cuda:
        adj = adj.cuda()
    # hop_adj = power_adj = adj

    # return (adj@(adj.to_dense())+adj).to_dense().cpu().numpy().astype(int)

    hop_adj = adj + torch.sparse.mm(adj, adj)

    hop_adj = hop_adj.to_dense()
    # hop_adj = (hop_adj > 0).to_dense()

    # for i in range(n_hops - 1):
    # power_adj = power_adj @ adj
    # prev_hop_adj = hop_adj
    # hop_adj = hop_adj + power_adj
    # hop_adj = (hop_adj > 0).float()

    hop_adj = hop_adj.cpu().numpy().astype(int)

    return (hop_adj > 0).astype(int)

    # return hop_adj.cpu().numpy().astype(int)


def neighborhoods(adj, n_hops, use_cuda):
    """Returns the n_hops degree adjacency matrix adj."""
    # adj = torch.tensor(adj, dtype=torch.float)
    # adj=adj.to_dense()
    # print(type(adj))
    if n_hops == 1:
        return adj.cpu().numpy().astype(int)

    if use_cuda:
        adj = adj.cuda()
    # hop_adj = power_adj = adj

    # for i in range(n_hops - 1):
    # power_adj = power_adj @ adj
    hop_adj = adj + adj @ adj
    hop_adj = (hop_adj > 0).float()

    np.save(hop_adj.cpu().numpy().astype(int), './neighborhoods_{}.npy'.format(dataset))

    return hop_adj.cpu().numpy().astype(int)


def InforNCE_Loss(anchor, sample, tau, all_negative=False, temperature_matrix=None):
    def _similarity(h1: torch.Tensor, h2: torch.Tensor):
        h1 = F.normalize(h1)
        h2 = F.normalize(h2)
        return h1 @ h2.t()

    assert anchor.shape[0] == sample.shape[0]

    pos_mask = torch.eye(anchor.shape[0], dtype=torch.float).cuda()
    neg_mask = 1. - pos_mask

    sim = _similarity(anchor, sample / temperature_matrix if temperature_matrix != None else sample) / tau
    exp_sim = torch.exp(sim) * (pos_mask + neg_mask)

    if not all_negative:
        log_prob = sim - torch.log(exp_sim.sum(dim=1, keepdim=True))
    else:
        log_prob = - torch.log(exp_sim.sum(dim=1, keepdim=True))

    loss = log_prob * pos_mask
    loss = loss.sum(dim=1) / pos_mask.sum(dim=1)

    # print(1)
    # return -loss[:10].mean()

    # print(sim)

    return -loss.mean(), sim


class Predictor(nn.Module):
    def __init__(self, nfeat, nhid, nout, dropout=0):
        super(Predictor, self).__init__()
        self.linear1 = Linear(nfeat, nhid)
        self.linear2 = Linear(nhid, nout)

    def forward(self, x):
        return self.linear2(self.linear1(x).relu())


parser = argparse.ArgumentParser()
parser.add_argument('--use_cuda', action='store_true', default=True, help='Disables CUDA training.')
parser.add_argument('--fastmode', action='store_true', default=False,
                    help='Validate during training pass.')
parser.add_argument('--seed', type=int, default=1234, help='Random seed.')
parser.add_argument('--epochs', type=int, default=2000,
                    help='Number of epochs to train.')
parser.add_argument('--test_epochs', type=int, default=2000,
                    help='Number of epochs to train.')
parser.add_argument('--pretrain_lr', type=float, default=0.01,
                    help='Initial learning rate.')
# 权重衰减
parser.add_argument('--weight_decay', type=float, default=5e-4,  # 5e-4
                    help='Weight decay (L2 loss on parameters).')
parser.add_argument('--hidden1', type=int, default=16,
                    help='Number of hidden units.')
parser.add_argument('--hidden2', type=int, default=16,
                    help='Number of hidden units.')
parser.add_argument('--pretrain_dropout', type=float, default=0.5,
                    help='Dropout rate (1 - keep probability).')
parser.add_argument('--dataset', default='dblp',
                    help='Dataset:Amazon_clothing/Amazon_eletronics/dblp')

args = parser.parse_args(args=[])

# args.use_cuda = torch.cuda.is_available()


random.seed(args.seed)
np.random.seed(args.seed)
torch.manual_seed(args.seed)
if args.use_cuda:
    torch.cuda.manual_seed(args.seed)

loss_f = nn.CrossEntropyLoss()
# Load data

Q=10
N = 5
K = 3
avail_train_num_per_class = 0

fine_tune_steps = 20

# 0.05 for Amazon-Computer
# 0.1 for other datasets
fine_tune_lr = 0.1

args.epochs = 500
args.test_epochs = 100

results=defaultdict(dict)

#for dataset in ['dblp','Amazon_eletronics','cora-full']:
#for dataset in ["CoraFull","Coauthor-CS","Amazon-Computer",'ogbn-arxiv']:
#for dataset in ["Cora","CiteSeer",'ogbn-arxiv']:
#for dataset in ['CiteSeer']:
for dataset in ['CoraFull']:
            # for dataset in ['dblp']:
            # for dataset in ['dblp']:
            # for dataset in ['cora-full',]:

    adj_sparse, features, labels, idx_train, idx_val, idx_test, n1s, n2s, class_train_dict, class_test_dict, class_valid_dict = load_data_pretrain(
        dataset,inductive=True)


    # print(adj_sparse[[0,1,2,3]])

    args.hidden1=features.shape[-1]


    adj = adj_sparse.to_dense()
    if dataset!='ogbn-arxiv':
        adj=adj.cuda()
    else:
        args.use_cuda=False
        args.epochs=500


    for N in [2,5]:
        if N==5 and dataset in ["Amazon-Computer","Cora","CiteSeer"]:continue
        for K in [1,3,5]:
            #if N==2 and (K==1 or K==3) and dataset=='ogbn-arxiv': continue

            for repeat in range(5):

                print('don')
                print(dataset)
                print('N={},K={}'.format(N,K))





                model = GCN_dense(nfeat=args.hidden1,
                                  nhid=args.hidden2,
                                  nclass=labels.max().item() + 1,
                                  dropout=args.pretrain_dropout)


                if avail_train_num_per_class!=0:
                    for key in class_train_dict.keys():
                        if len(class_train_dict[key])>avail_train_num_per_class:
                            class_train_dict[key]=np.random.choice(class_train_dict[key],avail_train_num_per_class,replace=False).tolist()
                    for key in class_valid_dict.keys():
                        if len(class_valid_dict[key])>avail_train_num_per_class:
                            class_valid_dict[key]=np.random.choice(class_valid_dict[key],avail_train_num_per_class,replace=False).tolist()



                # generater=nn.Linear(args.hidden1, (args.hidden1+1)*args.hidden2*2+(args.hidden2+1)*args.hidden2*2)

                MLP_alpha=Linear(10, 1)
                MLP_beta=Linear(10,1)

                classifier = Linear(args.hidden2, N)
                predictor = Predictor(args.hidden2, args.hidden2 * 2, args.hidden2)

                optimizer = optim.Adam([{'params': model.parameters()}, {'params': classifier.parameters()}, {'params': MLP_alpha.parameters()}, {'params': MLP_beta.parameters()},
                                        {'params': predictor.parameters()}],
                                       lr=args.pretrain_lr, weight_decay=args.weight_decay)



                cos_similarity = nn.CosineSimilarity(dim=1, eps=1e-6)

                support_labels=torch.zeros(N*K,dtype=torch.long)
                for i in range(N):
                    support_labels[i * K:(i + 1) * K] = i


                if args.use_cuda:
                    model.cuda()
                    features = features.cuda()
                    #
                    # generater=generater.cuda()
                    # adj = adj.cuda()

                    MLP_alpha=MLP_alpha.cuda()
                    MLP_beta=MLP_beta.cuda()
                    adj_sparse = adj_sparse.cuda()
                    labels = labels.cuda()
                    classifier = classifier.cuda()
                    predictor = predictor.cuda()

                    support_labels=support_labels.cuda()


                X_hat=adj.matmul(adj.matmul(features))

                def pre_train(epoch, mode='train'):
                    # classes=np.random.choice(list(range(len(class_train_dict))),N,replace=False)

                    #emb_features = model(features, adj_sparse)
                    #emb_features=features
                    if mode=='train' or mode=='valid':
                        Q=5
                    else:
                        Q=10

                    query_labels=torch.zeros(N*Q,dtype=torch.long)
                    for i in range(N):
                        query_labels[i * Q:(i + 1) * Q] = i
                    if args.use_cuda:
                        query_labels=query_labels.cuda()


                    target_idx = []
                    target_new_idx = []
                    target_graph_adj_and_feat = []
                    support_target_graph_adj_and_feat = []

                    pos_node_idx = []

                    if mode == 'train':
                        class_dict = class_train_dict
                        #for i in class_dict:  
                            #class_dict[i] = class_dict[i][:avail_train_num_per_class]
                    elif mode == 'test':
                        class_dict = class_test_dict
                    elif mode=='valid':
                        class_dict = class_valid_dict

                    classes = np.random.choice(list(class_dict.keys()), N, replace=False).tolist()


                    for i in classes:
                        # sample from one specific class
                        sampled_idx=np.random.choice(class_dict[i], K+Q, replace=False).tolist()

                        pos_node_idx.extend(sampled_idx[:K])
                        target_idx.extend(sampled_idx[K:])

                    node_set_1=np.random.choice(pos_node_idx+target_idx, 10, replace=False).tolist()
                    node_set_2=np.random.choice(pos_node_idx+target_idx, 10, replace=False).tolist()


                    X_hat_1=features[node_set_1]
                    X_hat_2=features[node_set_2]

                    alpha_1=MLP_alpha(X_hat_1.t()).t()
                    alpha_2=MLP_alpha(X_hat_2.t()).t()

                    beta_1=MLP_beta(X_hat_1.t()).t()
                    beta_2=MLP_beta(X_hat_2.t()).t()

                    alpha=(alpha_1+alpha_2)/2
                    beta=(beta_1+beta_2)/2               

                    if mode == 'train':
                        model.train()
                        optimizer.zero_grad()
                    else:
                        model.eval()
                    gc1_w, gc1_b, gc2_w, gc2_b, w, b = model.gc1.weight, model.gc1.bias, model.gc2.weight, model.gc2.bias, classifier.weight, classifier.bias

                    for j in range(fine_tune_steps):

                        emb_features = model(features*(1+alpha*0.01), adj_sparse, gc1_w, gc1_b, gc2_w, gc2_b)
                        ori_emb = emb_features[pos_node_idx]

                        loss_supervised = loss_f(classifier(ori_emb, w, b), support_labels)

                        loss = loss_supervised 

                        grad = torch.autograd.grad(loss, [gc1_w, gc1_b, gc2_w, gc2_b, w, b])
                        gc1_w, gc1_b, gc2_w, gc2_b, w, b = list(
                            map(lambda p: p[1] - fine_tune_lr * p[0], zip(grad, [gc1_w, gc1_b, gc2_w, gc2_b, w, b])))

                        # print(grad)
                        if torch.isnan(grad[0]).sum() > 0:
                            print(grad)
                            print(1 / 0)

                    #query_labels = torch.tensor(list(range(N))).cuda()

                    model.eval()
                    emb_features = model(features*(1+alpha*0.01), adj_sparse, gc1_w, gc1_b, gc2_w, gc2_b)
                    ori_emb = emb_features[target_idx]

                    logits = classifier(ori_emb, w, b)

                    #if np.random.rand()<0.05:
                        #print(alpha)

                    # print(ori_emb)


                    loss = loss_f(logits, query_labels)-0.01*(cos_similarity(alpha_1.mean(0,keepdim=True),alpha_2.mean(0,keepdim=True)).squeeze()+cos_similarity(beta_1.mean(0,keepdim=True),beta_2.mean(0,keepdim=True)).squeeze())

                    if mode == 'train':
                        loss.backward()
                        optimizer.step()

                    if epoch % 499 == 0 and mode == 'train':
                        print('Epoch: {:04d}'.format(epoch + 1),
                              'loss_train: {:.4f}'.format(loss.item()),
                              'acc_train: {:.4f}'.format((torch.argmax(logits, -1) == query_labels).float().mean().item()))
                    return (torch.argmax(logits, -1) == query_labels).float().mean().item()

                # Train model

                t_total = time.time()
                best_acc = 0
                best_valid_acc=0
                count=0
                for epoch in range(args.epochs):
                    acc_train=pre_train(epoch)


                    if  epoch > 0 and epoch % 10 == 0:
                        accs = []

                        for epoch_test in range(20):
                            accs.append(pre_train(epoch_test, mode='valid'))

                        valid_acc=np.array(accs).mean(axis=0)
                        print("Meta-valid_Accuracy: {}".format(valid_acc))

                        if valid_acc>best_valid_acc:
                            best_valid_acc=valid_acc
                            count=0
                            
                            test_accs=[]
                            for epoch_test in range(args.test_epochs):
                                test_accs.append(pre_train(epoch_test, mode='test'))
                        else:
                            count+=1
                            if count>=10:
                                break




                accs=test_accs
                results[dataset]['{}-way {}-shot {}-repeat'.format(N,K,repeat)]=[np.array(accs).mean(axis=0),
                                                                np.std(np.array(accs))]

                json.dump(results[dataset],open('./G-meta-result_{}_{}_avail.json'.format(dataset,avail_train_num_per_class),'w')) 


            accs=[]
            stds=[]
            for repeat in range(5):
                accs.append(results[dataset]['{}-way {}-shot {}-repeat'.format(N,K,repeat)][0])
                stds.append(results[dataset]['{}-way {}-shot {}-repeat'.format(N,K,repeat)][1])

            results[dataset]['{}-way {}-shot'.format(N,K)]=[np.mean(accs),np.mean(stds)]
            results[dataset]['{}-way {}-shot_print'.format(N,K)]='acc: {:.4f}\n std: {:.4f}\n interval: {:.4f}'.format(np.mean(accs),np.mean(stds),np.mean(stds)*0.196 )

            json.dump(results[dataset],open('./G-meta-result_{}_{}_avail.json'.format(dataset,avail_train_num_per_class),'w'))   

            del model

    del adj


