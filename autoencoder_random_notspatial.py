# topographique auto encoder sturcture
#build uniform position, split neurons into layers, connect layers to layers creating topology if needed and then train backprop
import os
import tqdm
import voronoi
import numpy as np
from matplotlib.collections import LineCollection
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, Polygon
from matplotlib.collections import PatchCollection
from matplotlib.animation import FuncAnimation
from random import randint
import copy
from sklearn import preprocessing
import time

def connect(Pl, l, n_input_cells, n_output_cells):
    sigma=200
    d=200
    W=[]
    q=1.4 #control the rate connection to first layer (has to be bigger than 1)
    win=np.floor(np.random.uniform(0,q,(len(Pl[0]),n_input_cells)))#create input connection
    for i in range(n_input_cells):#ensure each entry is connected to at least one neurone
        counter=0
        for j in range(len(Pl[0])):
            if win[j,i]!=0:
                counter+=1
        if counter==0:
            win[randint(0,len(Pl[0])-1),i]=1
    W.append(win)
    for j in range(l-1):
        P1=Pl[j]
        P2=Pl[j+1]
        n1 = len(P1)
        n2 = len(P2)
    
        dP = P1.reshape(1,n1,2) - P2.reshape(n2,1,2)
    
            
    
        # Distances
        
        D = np.hypot(dP[...,0]+d, dP[...,1])
        #D = dP[...,1]
    
        w = np.zeros((n2,n1))
        for i in range(n1):
                for j in range(n2):
                    if (np.random.uniform(0,1) < np.exp(-(D[j,i]**2)/(2*sigma**2))):
                        w[j,i]=1
        W.append(w)
    wout=np.floor(np.random.uniform(0,3,(n_output_cells,len(Pl[l-1]))))
    W.append(wout)
    
    return W

def split(P, l):#l number of layer 
    n=len(P)
    layer=[]
    for j in range(l):
        temp=[]
        c=1
        for i in range(n):
            if((1000/l)*j<P[i,0]<=(1000/l)*(j+1)):
                if(c==0):
                    temp.append(P[i,:])
                else:
                    #layer.append(P[i,:])
                    temp.append(P[i,:])
                    c=0
        temp=np.array(temp)
        layer.append(temp)
    return np.array(layer)


def build(n_cells=1000, n_input_cells = 32, n_output_cells = 32,
          n_input = 3, n_output = 3, sparsity = 0.01, seed=0,l=10):
    """

    Parameters:
    -----------

    n_cells:        Number of cells in the reservoir
    n_input_cells:  Number of cells receiving external input
    n_output_cells: Number of cells sending external output
    n_input:        Number of external input
    n_output:       Number of external output
    sparsity:       Connection rate
    seed:           Seed for the random genrator

    
    """
    
    np.random.seed(seed)
    density    = np.ones((1000,1000))
    n=1000
    for i in range(n):
	    ii=i/(n-1)
	    density[:,i]=np.power(((3.85)*ii*(ii-1)+1)*np.ones((1,n)),0.75) #neurone density
    density_P  = density.cumsum(axis=1)
    density_Q  = density_P.cumsum(axis=1)
    filename = "autoencoder-second-degree.npy"#aba.npy#autoencoder-second-degree.npy

    if not os.path.exists(filename):
        cells_pos = np.zeros((n_cells,2))
        cells_pos[:,0] = np.random.uniform(0, 1000, n_cells)
        cells_pos[:,1] = np.random.uniform(0, 1000, n_cells)
        for i in tqdm.trange(75):
            _, cells_pos = voronoi.centroids(cells_pos, density, density_P, density_Q)
        np.save(filename, cells_pos)

    cells_pos = np.load(filename)
    cells_pos=split(cells_pos,l)
    #X,Y = cells_pos[:,0], cells_pos[:,1]

    
    W=connect(cells_pos, l, n_input_cells, n_output_cells)
    scheme_vis(cells_pos, W)
    return cells_pos/1000, W#, W_in, W_out, bias
    




def sigmoid(x):
    return 1/(1+np.exp(-x))

def dsigmoid(x):
    return sigmoid(x)*(1-sigmoid(x))

def forward(x, w):
    l=len(w)
    X=[]
    for i in range(l):
        X.append(x)
        x=sigmoid(w[i].dot(x))
    return X, x

def backprop(x_in, x_in_t, w, alpha, Spatial): #propagate back, train W one step and resturn actual error
    X, x_out=forward(x_in,w)
    X_t, x_out_t=forward(x_in_t,w)
    l=len(w)-1
    e=[dsigmoid(w[l].dot(X[l]))*(x_out-x_in)]
    for i in range(l-1,-1,-1):
        e.append(dsigmoid(w[i].dot(X[i]))*np.transpose(w[i+1]).dot(e[l-1-i]))
    if Spatial:
        for i in range(l+1):
            for j in range(x_in.shape[1]):
               w[i]-=alpha*(np.outer(e[l-i][:, j], X[i][:, j]))*W[i]
    else:
        for i in range(l+1):
            for j in range(x_in.shape[1]):
               w[i]-=alpha*np.outer(e[l-i][:, j], X[i][:, j])
    return w, (np.sum((x_out-x_in)**2))/(x_in.shape[1]), (np.sum((x_out_t-x_in_t)**2))/(x_in_t.shape[1])

    
def train(x_in, x_in_t, w, iterr, alpha, Spatial):
    error=np.zeros(iterr)
    error_t=np.zeros(iterr)
    for i in range(iterr):
            w, error[i], error_t[i]= backprop(x_in, x_in_t, w, alpha, Spatial)
    plt.loglog(error)
    plt.show()
    return w, error, error_t




def generate_poly(data_size, n, degree):
    data=np.zeros((data_size, n))
    def poly(x, param):
        p=0
        for i in range(len(param)):
            p=p*x+param[i]
        return p
    for i in range(n):
        a=2*np.random.random([degree+1])-1
        data[:,i]=poly(np.linspace(-2, 2, data_size), a)
    return data

def scheme_vis(layer, W):
    for i in layer:
        plt.scatter(i[:,0], i[:,1])
    plt.axis("off")
    plt.axis('equal')
    plt.savefig("fig1.png")
    plt.show()
    
    fig, ax = plt.subplots()
    for i in layer:
        plt.scatter(i[:,0], i[:,1])
    c=['r', 'g', 'b', 'y']
    conteur1=0
    conteur2=0
    for i in range(1, len(W)-1):
        conteur1+=np.sum(W[i])
        conteur2+=(W[i].shape[0])*(W[i].shape[1])
        lines=[]
        for n in range(W[i].shape[0]):
            for k in range(W[i].shape[1]):
                if W[i][n,k]==1:
                    lines.append([layer[i-1][k], layer[i][n]])
        seg=LineCollection(lines, colors=c[i-1])
        ax.add_collection(seg)
    plt.axis("off")
    ax.axis('equal')
    plt.savefig("fig2.png")
    plt.show()
    print(conteur1, conteur2)
    
        


# Build
# ------
#P, W, W_in, W_out, bias = build(1000, 32, 32, n_input=1, n_output=1,sparsity=0.05, seed=0)
 
l=5 
size=10
alpha=0.03#0.03
iterr=10000

P, W = build(50, size, size, l=l, n_input=1, n_output=1,sparsity=0.05, seed=2)
w=copy.deepcopy(W)

for i in range(len(w)):
    print(w[i].shape)
    w[i]=w[i]*(2*np.random.random(w[i].shape)-1)

#x=np.random.random([size])
#data=np.random.random([size, 1])

scaler = preprocessing.MinMaxScaler()
data=generate_poly(size, 50, 4)
scaled_data=scaler.fit_transform(data)
unscaled_data=scaler.inverse_transform(scaled_data)
data_t=generate_poly(size, 50, 4)
scaled_data_t=scaler.transform(data_t)

s1=time.time()
a,b,e=train(scaled_data, scaled_data_t, w, iterr, alpha, True)
s1=time.time()-s1
X, x=forward(scaled_data_t,w)

li=[]
for i in range(len(X)):
    a=np.mean(np.abs(X[i]), axis=1)
    print(a.shape[0], np.mean(a))
    li.append(a.shape[0]*np.mean(a))
a=np.mean(np.abs(x), axis=1)
print(a.shape[0], np.mean(a))
li.append(a.shape[0]*np.mean(a))

fig , ax1= plt.subplots()
plt.figure(figsize=(5,5))
ax1.set_aspect(30)
plt.plot(x[:,3:5], label="reconstructed polynomials") 
plt.plot(scaled_data[:,3:5],  label="test polynomials")
#plt.legend(loc="upper right")
#plt.savefig("fig4.png")
plt.show()

for i in range(len(w)):
    w[i]=(2*np.random.random(w[i].shape)-1)
    
s2=time.time()
c,d,f=train(scaled_data, scaled_data_t, w, iterr, alpha, False)
s2=time.time()-s2


fig = plt.figure()
fig.subplots_adjust(top=0.8)
ax1 = fig.add_subplot(211)
ax1.set_ylabel('Mean Square Error')
ax1.set_xlabel('Iterration')

plt.loglog(b, label="Spatial")
plt.loglog(d, label="not Spatial")
plt.legend()
#plt.savefig("fig3.png")
plt.show()

fig = plt.figure()
fig.subplots_adjust(top=0.8)
ax1 = fig.add_subplot(211)
ax1.set_ylabel('Mean Square Error')
ax1.set_xlabel('Iterration')

plt.loglog(e, label="Spatial")
plt.loglog(f, label="not Spatial")
plt.legend()
#plt.savefig("fig3.png")
plt.show()
X, x=forward(scaled_data_t,w)

lii=[]
for i in range(len(X)):
    a=np.mean(np.abs(X[i]), axis=1)
    print(a.shape[0], np.mean(a))
    lii.append(a.shape[0]*np.mean(a))
a=np.mean(np.abs(x), axis=1)
print(a.shape[0], np.mean(a))
lii.append(a.shape[0]*np.mean(a))

plt.plot(li, label="spatial")
plt.plot(lii, label="non spatial")
plt.legend()
plt.show()

fig , ax1= plt.subplots()
plt.figure(figsize=(5,5))
ax1.set_aspect(30)
plt.plot(x[:,3:5], label="reconstructed polynomials") 
plt.plot(scaled_data[:,3:5],  label="test polynomials")
#plt.legend(loc="upper right")
#plt.savefig("fig4.png")
plt.show()

print(s2, s1)
#for i in range(6):
#    print(w[i]-W[i])
#print(w)

#print(b)
"""
w=copy.deepcopy(W)

a,b=train(x, w, 10000, 3)
print(b)
for i in range(len(a)):
    print(a[i].shape)
"""
"""

#print('{0:1.2e}'.format(b))
li=[0.5]
for i in range(3):
    li.append(li[i]*1.8)
c=[]
for i in li:
    w=copy.deepcopy(W)
    a,b=train(x, w, 10000, i)
    print(b, i)
    c.append(b)
plt.show()
plt.loglog(li, c)
"""
