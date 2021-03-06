g# MNIST DBN. Can change Spatial from True to False if you want to train Spatial or all to all network. Can load already train example and save your own example if needed.
import numpy as np
import matplotlib.pyplot as plt
import copy
from sklearn import preprocessing
np.set_printoptions(threshold=np.inf)
import tensorflow as tf
import time
import pickle

import topology as top
import function as func
import analyzeTools as at
import rbm_train as rbmt
import rbm_visualize as rbmv

#The parameter width can be changed in topology.py in connect_3d_sharp

#global variable
size=784
n_cell=1600
dataset_size=10000
dataset_size_t=300
t=4
sigma=16
ims=28
d=27
height=7
epsilon=[0]*4#rbm rate
fe=[]
ttt=[]
Spatial=True

    
class store(object): 
    def __init__(self, build_height=0, build_d=0, build_sigma=0, W=0, Wt=0, P=0, index_list=0, Spatial=0, epsilon=0, alpha=0, mode=0, iterr_rbm=0, w=0, b=0, c=0, fe=0, ttt=0):
        self.build_height = build_height#build length
        self.build_d = build_d#connection length
        self.build_sigma = build_sigma#connection width
        self.W = W#complete connection matrix
        self.Wt = Wt#layered connection matrix
        self.P = P#position array
        self.index_list = index_list#list of index of layers suposed to be 5
        
        self.Spatial = Spatial#==True if spatial connection
        self.epsilon = epsilon#list of all learning rate (supposed to be 4)
        self.alpha = alpha#list of sparsity learning rate
        self.mode = mode#list of list(first element 0/1->gaussianRbm/rbm, second element, if mode[i][1]==0 no sparsity, otherwise mode[i][1] is the target sparsity)
        self.iterr_rbm = iterr_rbm#list of iterration for rbm training
        
        self.w = w#learned weight
        self.b = b#learned backward bias
        self.c = c#learned forward bias
        
        self.fe = fe#training free energy
        self.ttt = ttt

 



P, W,in_index =top.build_3d(height, d, sigma)
#Wt=top.abstract_layer(in_index, W, t)#_local_backward_restriction
Wt, index_list=top.abstract_layer_local_backward_restriction(in_index, W, t, 1)#385)
at.visualize_abstract_3d(P, W, index_list, t)
at.degree_distribution(Wt)
#at.connection_forward_0(Wt)
#at.connection_backward_rate(Wt)
#at.connection_forward_rate(Wt)
#at.analyze_topology_back(Wt,4)
#Wt=top.abstract_layer_restriction(Wt, 10, 0.93)
#at.connection_backward_rate(Wt)
#at.analyze_topology_back(Wt,4)
#for i in range(t-1,0,-1):
    #at.analyze_topology(Wt, i)
#for i in range(t-1,0,-1):
    #at.analyze_topology_froward(Wt,i)
#for i in range(t-1,0,-1):
#    at.analyze_topology_back(Wt,i)
#at.connection_backward_rate(Wt)
    
w=[]                                                                           #initialise weight and bias
b=[]#backward bias
c=[]#forward bias
for i in range(len(Wt)):
    wc=copy.deepcopy(Wt[i])
    #wc=np.ones(wc.shape)
    wc=wc*np.random.normal(0, 0.01, wc.shape)
    w.append(wc)
    b.append(np.zeros((wc.shape[1],1)))
    c.append(np.zeros((wc.shape[0],1)))
b[0]=np.random.randn(Wt[0].shape[1],1)


mnist = tf.keras.datasets.mnist                                                #data set loading and scalling
(x_train, y_train),(x_test, y_test) = mnist.load_data()
x_train=x_train[0:dataset_size,:,:]
x_test=x_test[0:dataset_size_t,:,:]

x_train=np.asarray(x_train).reshape(dataset_size,-1)
x_test=np.asarray(x_test).reshape(dataset_size_t,-1)
scaler = preprocessing.StandardScaler().fit(x_train)
x_train = np.transpose(scaler.transform(x_train))
scaler1 = preprocessing.StandardScaler().fit(np.transpose(x_test))
x_test=np.transpose(scaler.transform(x_test))


#at.visualize_3d(P, W, in_index, t)
answer = input("Do you want to train y/n?")
if answer == "y":
    if Spatial:
        epsilon=[0.01, 0.05, 0.01, 0.07] #RBMs learning rate
        alpha=[0.01, 0.01, 0.1, 0.05]      #Sparsity learning rate ponderation
        mode=[[0, 0], [1, 0], [1, 0], [1, 0]] #mode[i][0] 0 for grbm 1 for rbm   mode[i][1] 0 if no sparsity if !=0 mode[i][1]=target sparsity
        iterr_rbm=[3000, 1000, 3000, 1000]
            
        b[0]=np.random.randn(Wt[0].shape[1],1)
        c[0]=np.zeros(c[0].shape)    
        w[0]=copy.deepcopy(Wt[0])
        w[0]=w[0]*np.random.normal(0, 0.01, w[0].shape)

        #layer 1
        seconds = time.time()
        fe.append(rbmt.train_spatial_rbm(x_train, b[0], c[0], w[0], iterr_rbm[0], mode[0], epsilon[0], alpha[0], x_test, dataset_size, 1, 50, Wt[0]))
        ttt.append(time.time()-seconds)
        print("time",time.time()-seconds)
        print("error", rbmv.error(x_test,b[0],c[0],w[0]))
        for i in range(0,w[0].shape[0]-1,w[0].shape[0]//5):
            plt.imshow(w[0][i,:].reshape(ims,ims))
            plt.colorbar()
            plt.show()
        rbmv.gibbs_sampling(x_test[:,0:1], b[0],c[0],w[0], 2, scaler, mode[0])
        rbmv.gibbs_sampling(x_test[:,1:2], b[0],c[0],w[0], 2, scaler, mode[0])
        rbmv.gibbs_sampling(x_test[:,20:21], b[0],c[0],w[0], 2, scaler, mode[0])
    
        x_test_1=rbmt.sample_rbm_forward(x_test, c[0], w[0])
        n=20
        pi=0
        p=200#x_test_4.shape[0]
        x=np.zeros((10*n, p))
        for j in range(10):                                                         #affiche l'encodage
            q=0
            i=0
            while (q<n and i<300):
                if y_test[i]==j:
                    x[q+n*j, 0:p]=0.5*(x_test_1[pi:pi+p, i]+1)
                    q+=1
                i+=1
        fig, ax = plt.subplots(figsize=(90, 10))
        ax.imshow(x)
        plt.show()
    
        
        b[1]=np.zeros(b[1].shape)
        c[1]=np.zeros(c[1].shape)    
        w[1]=copy.deepcopy(Wt[1])
        w[1]=w[1]*np.random.normal(0, 0.01, w[1].shape)
        
        #layer 2
        x_train_1=rbmt.sample_rbm_forward(x_train, c[0], w[0])
        x_test_1=rbmt.sample_rbm_forward(x_test, c[0], w[0])
        seconds = time.time()
        fe.append(rbmt.train_spatial_rbm(x_train_1, b[1],c[1],w[1], iterr_rbm[1], mode[1], epsilon[1], alpha[1], x_test_1, dataset_size, 1, 50, Wt[1]))
        ttt.append(time.time()-seconds)
        print("layer 2")
        print("error", rbmv.error(x_test_1,b[1],c[1],w[1]))
        print("time",time.time()-seconds)
        rbmv.gibbs_deep_sampling(x_test[:,1:2], b, c, w, 1, scaler)
    
        x_test_2=rbmt.sample_rbm_forward(x_test_1, c[1], w[1])
        n=20
        pi=0
        p=200#x_test_4.shape[0]
        x=np.zeros((10*n, p))
        for j in range(10):                                                         #affiche l'encodage
            q=0
            i=0
            while (q<n and i<300):
                if y_test[i]==j:
                    x[q+n*j, 0:p]=0.5*(x_test_2[pi:pi+p, i]+1)
                    q+=1
                i+=1
        fig, ax = plt.subplots(figsize=(90, 10))
        ax.imshow(x)
        plt.show()
    


        b[2]=np.zeros(b[2].shape)
        c[2]=np.zeros(c[2].shape)
        w[2]=copy.deepcopy(Wt[2])
        w[2]=w[2]*np.random.normal(0, 0.01, w[2].shape) 
        #layer 3
        x_train_2=rbmt.sample_rbm_forward(x_train_1, c[1], w[1])
        x_test_2=rbmt.sample_rbm_forward(x_test_1, c[1], w[1])
        seconds = time.time()
        fe.append(rbmt.train_spatial_rbm(x_train_2, b[2],c[2],w[2], iterr_rbm[2], mode[2], epsilon[2], alpha[2], x_test_2, dataset_size, 1, 50, Wt[2]))
        ttt.append(time.time()-seconds)
        print("layer 3")
        print("error", rbmv.error(x_test_2,b[2],c[2],w[2]))
        print("time",time.time()-seconds)
        rbmv.gibbs_deep_sampling(x_test[:,1:2], b, c, w, 2, scaler)
    
        x_test_3=rbmt.sample_rbm_forward(x_test_2, c[2], w[2])
        n=20
        pi=0
        p=min(200, x_test_3.shape[0])#x_test_4.shape[0]
        x=np.zeros((10*n, p))
        for j in range(10):                                                         #affiche l'encodage
            q=0
            i=0
            while (q<n and i<300):
                if y_test[i]==j:
                    x[q+n*j, 0:p]=0.5*(x_test_3[pi:pi+p, i]+1)
                    q+=1
                i+=1
        fig, ax = plt.subplots(figsize=(90, 10))
        ax.imshow(x)
        plt.show()

    else:
        epsilon=[0.001, 0.001, 0.001, 0.001]#RBMs learning rate
        alpha=[5, 0.5, 0.05, 8]#Sparsity learning rate ponderation
        mode=[[0, 0.1], [1, 0.1], [1, 0.1], [1, 0]]#[[0, 0.1], [1, 0.1], [1, 0.1], [1, 0.2]]
        iterr_rbm=[6000, 2000, 2000, 10]#mode[i][0] 0 for grbm 1 for rbm   mode[i][1] 0 if no sparsity if !=0 mode[i][1]=target sparsity
        
        b[0]=np.random.randn(Wt[0].shape[1],1)
        c[0]=np.zeros(c[0].shape)
        w[0]=np.ones(w[0].shape)*np.random.normal(0, 0.01, w[0].shape)
        
        seconds = time.time()
        fe.append(rbmt.train_rbm(x_train, b[0], c[0], w[0], iterr_rbm[0], mode[0], epsilon[0], alpha[0], x_test, dataset_size, 1, 50))
        ttt.append(time.time()-seconds)
        for i in range(w[0].shape[0]-10, w[0].shape[0]-5):
            plt.imshow(w[0][i,:].reshape(ims,ims))
            plt.colorbar()
            plt.show()
        print("error", rbmv.error(x_test,b[0],c[0],w[0]))
        print("time",time.time()-seconds)
        rbmv.gibbs_sampling(x_test[:,0:1], b[0],c[0],w[0], 2, scaler, mode[0])#resconstruction fro the first lqyer
        rbmv.gibbs_sampling(x_test[:,1:2], b[0],c[0],w[0], 2, scaler, mode[0])
        rbmv.gibbs_sampling(x_test[:,20:21], b[0],c[0],w[0], 2, scaler, mode[0])
     
        

    
        #layer 2
    
        b[1]=np.zeros(b[1].shape)
        c[1]=np.zeros(c[1].shape)
        w[1]=np.ones(w[1].shape)*np.random.normal(0, 0.01, w[1].shape)
    
        x_train_1=rbmt.sample_rbm_forward(x_train, c[0], w[0])
        x_test_1=rbmt.sample_rbm_forward(x_test, c[0], w[0])
        seconds = time.time()
        fe.append(rbmt.train_rbm(x_train_1, b[1],c[1],w[1], iterr_rbm[1], mode[1], epsilon[1], alpha[1], x_test_1, dataset_size, 1, 50))
        ttt.append(time.time()-seconds)
        print("time",time.time()-seconds)
    
     
        print("layer 2")
        print("error", rbmv.error(x_test_1,b[1],c[1],w[1]))
    
        rbmv.gibbs_deep_sampling(x_test[:,1:2], b, c, w, 1, scaler)
    
        b[2]=np.zeros(b[2].shape)
        c[2]=np.zeros(c[2].shape)
        w[2]=np.ones(w[2].shape)*np.random.normal(0, 0.01, w[2].shape)
    
     
        #layer 3
        x_train_2=rbmt.sample_rbm_forward(x_train_1, c[1], w[1])
        x_test_2=rbmt.sample_rbm_forward(x_test_1, c[1], w[1])
        seconds = time.time()
        fe.append(rbmt.train_rbm(x_train_2, b[2],c[2],w[2], iterr_rbm[2], mode[2], epsilon[2], alpha[2], x_test_2, dataset_size, 1, 200))
        ttt.append(time.time()-seconds)
        print("layer 3")
        print("error", rbmv.error(x_test_2,b[2],c[2],w[2]))
        print("time",time.time()-seconds)
        rbmv.gibbs_deep_sampling(x_test[:,1:2], b, c, w, 2, scaler)
    
        x_test_3=rbmt.sample_rbm_forward(x_test_2, c[2], w[2])
        n=10
        pi=0
        p=min(200,x_test_1.shape[0])#x_test_4.shape[0]
        
        x=np.zeros((10*n, p))
        for j in range(10):                                                         #affiche l'encodage
            q=0
            i=0
            while (q<n and i<300):
                if y_test[i]==j:
                    x[q+n*j, 0:p]=0.5*(x_test_1[pi:pi+p, i]+1)
                    q+=1
                i+=1
        fig, ax = plt.subplots(figsize=(90, 10))
        ax.imshow(x)
        plt.show()
        
        p=min(200,x_test_2.shape[0])
        x=np.zeros((10*n, p))
        for j in range(10):                                                         #affiche l'encodage
            q=0
            i=0
            while (q<n and i<300):
                if y_test[i]==j:
                    x[q+n*j, 0:p]=0.5*(x_test_2[pi:pi+p, i]+1)
                    q+=1
                i+=1
        fig, ax = plt.subplots(figsize=(90, 10))
        ax.imshow(x)
        plt.show()
        
        p=min(200,x_test_3.shape[0])
        x=np.zeros((10*n, p))
        for j in range(10):                                                         #affiche l'encodage
            q=0
            i=0
            while (q<n and i<300):
                if y_test[i]==j:
                    x[q+n*j, 0:p]=0.5*(x_test_3[pi:pi+p, i]+1)
                    q+=1
                i+=1
        fig, ax = plt.subplots(figsize=(90, 10))
        ax.imshow(x)
        plt.show()
        
    
        
        for i in range(3):
            plt.hist(w[i])
            plt.show()
            
        
    answer = input("Do you want to save it y/n?")
    if answer == "y":
        memory = store(height, d, sigma, W, Wt, P, index_list, Spatial, epsilon, alpha, mode, iterr_rbm, w, b, c, fe, ttt)
        with open('no_restriction_spatial_dbn_width0.1.pkl', 'wb') as output:
            pickle.dump(memory, output, pickle.HIGHEST_PROTOCOL)
    elif answer == "n":
        print("ok")
    else:
        print("Please enter y or n.")
    
    
elif answer == "n":
    print("ok")
else:
    print("Please enter y or n.")
    
    
strl=['no_restriction_sparse_dbn_non_spatial.pkl', 'no_restriction_spatial_dbn_width0.05.pkl']#['sparse_dbn_non_spatial.pkl', 'no_restriction_sparse_dbn_non_spatial.pkl', 'no_restriction_sparse_spatial_dbn.pkl', 'no_restriction_spatial_dbn.pkl']
answer = input("Do you want to load y/n?")
if answer == "y":#load already trained network parameter and plot reconstruction.
    fig = plt.figure()
    for i in range(10):
            if i<5:fig.add_subplot(6,5,1+i)
            else:fig.add_subplot(6,5,11+i)
            plt.axis('off')
            plt.imshow(np.transpose(scaler.inverse_transform(np.transpose(x_test[:,i]))).reshape(ims,ims), vmin=-100, vmax= 400)
    k=0
    for st in strl:
        print(st)
        with open(st, 'rb') as data:
            memory = pickle.load(data)
            w=memory.w 
            b=memory.b 
            c=memory.c 
            print("epsilon", memory.epsilon)
            print("alpha", memory.alpha)
            print("mode", memory.mode)
        
        for i in range(10):
            n=2
            h=rbmt.sample_rbm_forward(x_test[:,i:i+1], c[0], w[0])
            for j in range(n):
                h=rbmt.sample_rbm_forward(h, c[j+1], w[j+1])
            for j in range(n):
                h=rbmt.sample_rbm_backward(h, b[n-j], w[n-j])
            h=rbmt.sample_grbm_backward(h, b[0], w[0])
            if i<5:fig.add_subplot(6,5,6+i+k)
            else:fig.add_subplot(6,5,16+i+k)
            plt.axis('off')
            plt.imshow(np.transpose(scaler.inverse_transform(np.transpose(h))).reshape(ims,ims), vmin=-100, vmax= 400)
        """   
        for i in range(10):
            n=2
            h=rbmt.sample_rbm_forward(x_test[:,i:i+1], c[0], w[0])
            for j in range(n):
                h=rbmt.sample_rbm_forward(h, c[j+1], w[j+1])
            for j in range(n):
                h=rbmt.sample_rbm_backward(h, b[n-j], w[n-j])
            h=rbmt.sample_grbm_backward(h, b[0], w[0])
            if i<5:fig.add_subplot(6,5,6+i+k)
            else:fig.add_subplot(6,5,16+i+k)
            plt.axis('off')
            if k==0:
                n=2
                h=rbmt.sample_rbm_forward(x_test, c[0], w[0])
                for j in range(n):
                    h=rbmt.sample_rbm_forward(h, c[j+1], w[j+1])
                for j in range(n):
                    h=rbmt.sample_rbm_backward(h, b[n-j], w[n-j])
                h=rbmt.sample_grbm_backward(h, b[0], w[0])
                plt.imshow(scaler1.inverse_transform(h)[:,i:i+1].reshape(ims,ims), vmin=-100, vmax= 400)
            else:plt.imshow(np.transpose(scaler.inverse_transform(np.transpose(h))).reshape(ims,ims), vmin=-100, vmax= 400)
        """
        k+=5
                
        
        x_test_1=rbmt.sample_rbm_forward(x_test, c[0], w[0])
        x_test_2=rbmt.sample_rbm_forward(x_test_1, c[1], w[1])
        x_test_3=rbmt.sample_rbm_forward(x_test_2, c[2], w[2])
        
        """
        n=10
        pi=0
        p=min(200,x_test_1.shape[0])#x_test_4.shape[0]
        
        x=np.zeros((10*n, p))
        for j in range(10):                                                         #affiche l'encodage
            q=0
            i=0
            while (q<n and i<300):
                if y_test[i]==j:
                    x[q+n*j, 0:p]=0.5*(x_test_1[pi:pi+p, i]+1)
                    q+=1
                i+=1
        fig, ax = plt.subplots(figsize=(90, 10))
        ax.imshow(x)
        plt.show()
        
        p=min(200,x_test_2.shape[0])
        x=np.zeros((10*n, p))
        for j in range(10):                                                         #affiche l'encodage
            q=0
            i=0
            while (q<n and i<300):
                if y_test[i]==j:
                    x[q+n*j, 0:p]=0.5*(x_test_2[pi:pi+p, i]+1)
                    q+=1
                i+=1
        fig, ax = plt.subplots(figsize=(90, 10))
        ax.imshow(x)
        plt.show()
        
        p=min(200,x_test_3.shape[0])
        x=np.zeros((10*n, p))
        for j in range(10):                                                         #affiche l'encodage
            q=0
            i=0
            while (q<n and i<300):
                if y_test[i]==j:
                    x[q+n*j, 0:p]=0.5*(x_test_3[pi:pi+p, i]+1)
                    q+=1
                i+=1
        fig, ax = plt.subplots(figsize=(90, 10))
        ax.imshow(x)
        plt.show()
        
        for i in range(3):
            plt.plot(memory.fe[i][0], memory.fe[i][1], label="layer "+str(i+1))
        plt.legend()
        plt.show()
        
        plt.hist(np.mean((x_test_1+1)/2, axis=1), bins=30)
        plt.show() 
        plt.hist(np.mean((x_test_2+1)/2, axis=1), bins=30)
        plt.show()     
        plt.hist(np.mean((x_test_3+1)/2, axis=1), bins=30)
        plt.show()         
        """
        
    #plt.savefig("mnistDbn.pdf")
    print("first line, test samples, second line all to all reconstructions, third line spatoal reconstruction")
    plt.show()
    
    lab=["0.1","0.05", "0.01"]
    ssparse=[]
    for st in ['no_restriction_spatial_dbn_width0.1.pkl', 'no_restriction_spatial_dbn_width0.05.pkl', 'no_restriction_spatial_dbn_width0.01.pkl']:
        print(st)
        with open(st, 'rb') as data:
            memory = pickle.load(data)
            w=memory.w 
            b=memory.b 
            c=memory.c
        x_test_1=rbmt.sample_rbm_forward(x_test, c[0], w[0])
        x_test_2=rbmt.sample_rbm_forward(x_test_1, c[1], w[1])
        x_test_3=rbmt.sample_rbm_forward(x_test_2, c[2], w[2])
        
        sparse=[]
        xx=[x_test, x_test_1, x_test_2, x_test_3]
        for i in range(3):
            sparse.append(w[i].shape[1]*(np.mean(xx[i])+1)/2)
        sparse.append(w[2].shape[0]*(np.mean(xx[3])+1)/2)
        ssparse.append(sparse)
    for i in range(3):
        plt.plot([1,2,3,4], ssparse[i], label=lab[i])
    plt.legend()
    plt.show()
        

elif answer == "n":
    print("ok")
else:
    print("Please enter y or n.")
    