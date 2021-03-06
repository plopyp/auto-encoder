#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#function for training the DBN
import matplotlib.pyplot as plt
import numpy as np
import time

import function as func
import rbm_visualize as rbmv


#RBM
def sample_rbm_forward(visible, c, w):
   return np.where(np.random.rand(w.shape[0],visible.shape[1]) < func.sigmoid(np.tile(c,(1,visible.shape[1]))+w.dot(visible)), 1, -1)


def sample_rbm_backward(hidden, c, w):
    return np.where(np.random.rand(w.shape[1],hidden.shape[1]) < func.sigmoid(np.tile(c,(1,hidden.shape[1]))+np.transpose(w).dot(hidden)), 1, -1)

def sample_grbm_backward(hidden, b, w):
    return np.random.normal(np.tile(b,(1,hidden.shape[1]))+np.transpose(w).dot(hidden), 0.01)#np.where(np.random.rand(w.shape[1],hidden.shape[1]) < sigmoid(np.tile(b,(1,hidden.shape[1]))+np.transpose(w).dot(hidden)), 0, 1) #this is no more sampling!!!!!!!!!!!!!

def backandforw(hidden, b, c, w, k, mode):#propagate backward and forward between 2 layers k times
    for i in range(k):
        if mode==0:
            visible_k=sample_grbm_backward(hidden, b, w)
        if mode==1:
            visible_k=sample_rbm_backward(hidden, b, w)
        hidden=sample_rbm_forward(visible_k, c, w)
    return hidden, visible_k

def spatial_actualise_weight(visible, b, c, w, k, epsilon, alpha, mode, Wt):#proceed to contrastive divergence and update weigts
    hidden=sample_rbm_forward(visible, c, w)
    hidden_c, visible_c=backandforw(hidden, b, c, w, k, mode[0])
    w+=(1/(visible.shape[1]))*epsilon*(hidden.dot(np.transpose(visible))-hidden_c.dot(np.transpose(visible_c)))*Wt
    b+=(1/(visible.shape[1]))*epsilon*(np.sum(visible-visible_c, axis=1)).reshape(visible.shape[0],1)
    c+=(1/(visible.shape[1]))*epsilon*(np.sum(hidden-hidden_c, axis=1)).reshape(w.shape[0],1)
    if mode[1]!=0:#sparsity
        cwv=c+w.dot(visible)
        dsigm=func.dsigmoid(cwv)
        q=((2*mode[1]-1)-(1/visible.shape[1])*(2*np.sum(func.sigmoid(cwv), axis=1)-1)).reshape(w.shape[0],1)
        #q=q*np.abs(np.power(q,2))
        w+=epsilon*alpha*q*(1/visible.shape[1])*(dsigm.dot(np.transpose(visible)))*Wt
        c+=epsilon*alpha*q*(1/visible.shape[1])*(np.sum(dsigm, axis=1).reshape(w.shape[0],1))

def actualise_weight(visible, b, c, w, k, epsilon, alpha, mode):#proceed to contrastive divergence and update weigts
    hidden=sample_rbm_forward(visible, c, w)
    hidden_c, visible_c=backandforw(hidden, b, c, w, k, mode[0])
    w+=(1/(visible.shape[1]))*epsilon*(hidden.dot(np.transpose(visible))-hidden_c.dot(np.transpose(visible_c)))
    b+=(1/(visible.shape[1]))*epsilon*(np.sum(visible-visible_c, axis=1)).reshape(visible.shape[0],1)
    c+=(1/(visible.shape[1]))*epsilon*(np.sum(hidden-hidden_c, axis=1)).reshape(w.shape[0],1)
    if mode[1]!=0:#sparsity
        cwv=c+w.dot(visible)
        dsigm=func.dsigmoid(cwv)
        q=((2*mode[1]-1)-(2*np.mean(func.sigmoid(cwv), axis=1)-1)).reshape(w.shape[0],1)
        w+=epsilon*alpha*q*(1/visible.shape[1])*(dsigm.dot(np.transpose(visible)))
        c+=epsilon*alpha*q*(1/visible.shape[1])*(np.sum(dsigm, axis=1).reshape(w.shape[0],1))
  
def train_rbm(visible, b, c, w, iterr_rbm, mode, epsilon, alpha, x_test, dataset_size, cd, f):
    ind=[]
    e=[]
    E=[]
    fe=[]
    d=0
    g=0
    
    t1=0
    t2=0
    iterr_rbm=iterr_rbm//cd
    for i in range(iterr_rbm):
        visible_batch=visible[:,d:d+32]
        #visible_batch=visible_batch.reshape(visible.shape[0],1)
        g+=1
        if g==32:
            d+=32
            g=0
        if d>dataset_size-34:
            d=0
        actualise_weight(visible_batch, b, c, w, cd, epsilon, alpha, mode)
        if i%(iterr_rbm//20)==0:
            ind.append(i)
            if mode[0]==0:
                tt=time.time()
                e.append(rbmv.energy_grbm(x_test, b, c, w))
                E.append(rbmv.energy_grbm(visible, b, c, w))
                t1+=time.time()-tt
                tt=time.time()
                fe.append(rbmv.pseudo_likelihood_grbm(x_test, b, c, w, f))
                #fE.append(rbmv.pseudo_likelihood_grbm(visible, b, c, w, 3))
                t2+=time.time()-tt
            else:
                tt=time.time()
                e.append(rbmv.energy_rbm(x_test, b, c, w))
                E.append(rbmv.energy_rbm(visible, b, c, w))
                t1+=time.time()-tt
                tt=time.time()
                fe.append(rbmv.pseudo_likelihood_rbm(x_test, b, c, w, f))
                #fE.append(rbmv.pseudo_likelihood_rbm(visible, b, c, w, 3))
                t2+=time.time()-tt   
    plt.hist(np.mean(func.sigmoid(c+w.dot(visible)), axis=1), bins=30)
    plt.title("mean neurons activation")
    plt.legend()
    plt.show() 
    plt.plot(ind, e,label="test set")
    plt.plot(ind, E, label="training set")
    plt.legend(loc='upper right')
    if mode[0] == 1:
        plt.yscale('symlog')
    plt.show()
    plt.plot(ind, fe, label="free energy test set")
    #plt.plot(ind, fE, label="free energy training set")
    plt.legend(loc='lower right')
    plt.show()
    print("free-energy", fe[len(fe)-1])
    print("energy time and pseudo likelihood time ", t1, t2)
    return [ind,fe]

    
def train_spatial_rbm(visible, b, c, w, iterr_rbm, mode, epsilon, alpha, x_test, dataset_size, cd, f, Wt):
    ind=[]
    e=[]
    E=[]
    fe=[]
    er=[]
    d=0
    g=0
    
    t1=0
    t2=0
    iterr_rbm=iterr_rbm//cd
    for i in range(iterr_rbm):
        visible_batch=visible[:,d:d+32]
        #visible_batch=visible_batch.reshape(visible.shape[0],1)
        g+=1
        if g==32:
            d+=32
            g=0
        if d>dataset_size-34:
            d=0
        spatial_actualise_weight(visible_batch, b, c, w, cd, epsilon, alpha, mode, Wt)
        if i%(iterr_rbm//20)==0:
            ind.append(i)
            if mode[0]==0:
                tt=time.time()
                e.append(rbmv.energy_grbm(x_test, b, c, w))
                E.append(rbmv.energy_grbm(visible, b, c, w))
                t1+=time.time()-tt
                tt=time.time()
                fe.append(rbmv.pseudo_likelihood_grbm(x_test, b, c, w, f))
                #fE.append(rbmv.pseudo_likelihood_grbm(visible, b, c, w, 3))
                er.append(rbmv.error(x_test, b, c, w))
                t2+=time.time()-tt
            else:
                tt=time.time()
                e.append(rbmv.energy_rbm(x_test, b, c, w))
                E.append(rbmv.energy_rbm(visible, b, c, w))
                t1+=time.time()-tt
                tt=time.time()
                fe.append(rbmv.pseudo_likelihood_rbm(x_test, b, c, w, f))
                #fE.append(rbmv.pseudo_likelihood_rbm(visible, b, c, w, 3))
                er.append(rbmv.error(x_test, b, c, w))
                t2+=time.time()-tt
    plt.hist(np.mean(func.sigmoid(c+w.dot(visible)), axis=1), bins=30)
    plt.show()
    plt.plot(ind, e,label="test set")
    plt.plot(ind, E, label="training set")
    plt.legend(loc='upper right')
    if mode[0] == 1:
        plt.yscale('symlog')
    plt.show()
    plt.plot(ind, fe, label="free energy test set")
    #plt.plot(ind, fE, label="free energy training set")
    plt.legend(loc='lower right')
    plt.show()
    print("free-energy", fe[len(fe)-1])
    print("energy time and pseudo likelihood time ", t1, t2)
    plt.plot(ind, er)
    plt.show()
    return [ind,fe]



