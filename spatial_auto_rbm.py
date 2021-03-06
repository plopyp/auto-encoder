# topographique auto encoder sturcture
import os
import tqdm
import voronoi
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import copy
from sklearn import preprocessing
np.set_printoptions(threshold=np.inf)


#sigmoid is in 0 1
#grbm sampling is noise free

#graph
def connect(P, n_input_cells, n_output_cells, d, sigma):

    

    n = len(P)
    dP = P.reshape(1,n,2) - P.reshape(n,1,2)
    # Shifted Distances 
    D = np.hypot(dP[...,0]+d, dP[...,1])
    W = np.zeros((n,n))
    for i in range(n):
        for j in range(n):
            if (np.random.uniform(0,1) < np.exp(-(D[j,i]**2)/(2*sigma**2))) & (P[i,0]<P[j,0]):
                W[j,i]=1  
    return W


def build(n_cells, n_input_cells = 32, n_output_cells = 32, sparsity = 0.01, seed=0):
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
    
    #np.random.seed(seed)
    density    = np.ones((1000,1000))
    n=1000
    for i in range(n):
	    ii=i/(n-1)
	    density[:,i]=np.power((0.9*ii*(ii-2)+1)*np.ones((1,n)),4) #neurone density
    density_P  = density.cumsum(axis=1)
    density_Q  = density_P.cumsum(axis=1)
    filename = "deep_rbm.npy"#"CVT-%d-seed-%d.npy" % (n_cells,seed)

    if not os.path.exists(filename):
        cells_pos = np.zeros((n_cells,2))
        cells_pos[:,0] = np.random.uniform(0, 1000, n_cells)
        cells_pos[:,1] = np.random.uniform(0, 1000, n_cells)
        for i in tqdm.trange(75):
            _, cells_pos = voronoi.centroids(cells_pos, density, density_P, density_Q)
        np.save(filename, cells_pos)

    cells_pos = np.load(filename)
    cells_in  = np.argpartition(cells_pos, +n_input_cells, 0)[:+n_input_cells]
    cells_out = np.argpartition(cells_pos, -n_output_cells, 0)[-n_output_cells:]
    
    W=connect(cells_pos, n_input_cells, n_output_cells, d, sigma)


    return cells_pos/1000, W, cells_in[:,0], cells_out[:,0]#, W_in, W_out, bias
    
"""
#backprop
def sigmoid(x):
    return 2/(1+np.exp(-x))-1
"""
def sigmoid(x):
    return 1/(1+np.exp(-x))


def dsigmoid(x):
    f=sigmoid(x)
    return -(f+1)*(f-1)/2

def forward(x, w, t):
    X=[]
    for i in range(t):
        X.append(x)
        x=sigmoid(w.dot(x))
    return X, x

def backward(x_in, w, t, in_index, out_index, alpha):
    X, x_out=forward(x_in, w, t)
    x_in_reshape=np.zeros(x_in.shape)
    x_in_reshape[out_index]=x_in[in_index]

    mask = np.ones(len(x_out), dtype=bool)
    mask[out_index] = False
    x_out_reshape=x_out
    x_out_reshape[mask]=0

    e=[dsigmoid(w.dot(X[t-1]))*(x_out_reshape-x_in_reshape)]
    for i in range(t-2,-1,-1):
        e.append(dsigmoid(w.dot(X[i]))*np.transpose(w).dot(e[t-2-i]))
    for i in range(t):
        for j in range(x_in.shape[1]):
            w-=alpha*np.outer(e[t-1-i][:,j], X[i][:,j])*W  
    return  w, (np.sum(np.abs((x_out_reshape-x_in_reshape))))/(in_index.shape[0]*x_in.shape[1])

def err(x_in, w, t):
    X, x_out=forward(x_in, w, t)
    x_in_reshape=np.zeros(x_in.shape)
    x_in_reshape[out_index]=x_in[in_index]

    mask = np.ones(len(x_out), dtype=bool)
    mask[out_index] = False
    x_out_reshape=x_out
    x_out_reshape[mask]=0
    return (np.sum(np.abs(x_out_reshape-x_in_reshape)))/(in_index.shape[0]*x_in.shape[1]), np.max(x_out_reshape-x_in_reshape)

    
    
def train(x_in, w, t, in_index, out_index, iterr, alpha):
    error=np.zeros(iterr)
    c=0
    for i in range(iterr):
        #x_batch=x_in[:,c:c+32]
        #c+=32
        #if c>dataset_size-34:
        #    c=0
        alpha*=(5)**(1/(-iterr))
        w,  error[i] = backward(x_in, w, t, in_index, out_index, alpha)
        """
        if a==100:
            X, x=forward(x_in, w, t)
            plt.plot(np.linspace(-1, 1, size),scaled_data)
            plt.plot(np.linspace(-1, 1, size),x[out_index])
            plt.show()
            a=0
        a+=1
        """
    plt.semilogy(error)
    return w, error[iterr-1]

#RBM
def abstract_layer(in_index, W, t):#unfold the total connection matrix into layer by layer connection matrix
    index=in_index
    Wt=[]
    for i in range(t-1):
        x=np.zeros(W.shape[0])
        for i in index:x[i]=1
        x=W.dot(x)
        x=(x > 0).astype(int)
        index_new=np.asarray([idx for idx, v in enumerate(x) if v])
        Wt.append(W[index_new[:, None], index])
        index=index_new
    return Wt

def sample_rbm_forward(visible, c, w, delta):
    return np.where(np.random.rand(w.shape[0],visible.shape[1]) < sigmoid(np.tile(c,(1,visible.shape[1]))+w.dot(visible)*(delta**(-2))), 1, 0)

def sample_grbm(hidden, b, w, delta):
    return np.random.normal(np.tile(b,(1,hidden.shape[1]))+np.transpose(w).dot(hidden),1) 

def actualise_weight(visible, b, c, w, delta, i):
    hidden=sample_rbm_forward(visible, c, w, delta)
    visible_c=sample_grbm(hidden, b, w, delta)
    hidden_c=sample_rbm_forward(visible_c, c, w, delta)
    if i%100==0:print("v", (np.tile(b,(1,hidden.shape[1]))+np.transpose(w).dot(hidden))[1,0])
    w+=(1/(visible.shape[1]))*epsilon_w*((delta)**(-2))*(hidden.dot(np.transpose(visible))-hidden_c.dot(np.transpose(visible_c)))
    b+=(1/(visible.shape[1]))*epsilon_b*((delta)**(-2))*(np.sum(visible-visible_c, axis=1)).reshape(visible.shape[0],1)
    c+=(1/(visible.shape[1]))*epsilon_c*(np.sum(hidden-hidden_c, axis=1)).reshape(w.shape[0],1)
    e=0
    for i in range(visible.shape[1]):
        e-=(hidden[:,i]).dot(w.dot(visible[:,i]/delta))
    e+=np.sum((delta**(-2))*np.sum(visible-b, axis=1)**2)-np.sum(c*hidden)
    return e/(visible.shape[1]), np.sum(np.sum(np.abs(visible-visible_c)))/(visible.shape[0]*visible.shape[1])
  
def train_rbm(visible, b, c, w, delta, iterr_rbm):
    e=[]
    E=[]
    print("v", visible[1,0])
    for i in range(iterr_rbm):
        a, b = actualise_weight(visible, b, c, w, delta, i+1)
        e.append(a)
        E.append(b)
    print("v", visible[1,0])
    plt.plot(e)
    plt.yscale('symlog')
    plt.show()
    plt.plot(E)
    plt.yscale('symlog')
    plt.show()
    print(b)
    
def gibbs_sampling(visible, b, c, w, n):
    a=visible
    plt.plot(visible)
    plt.show()
    for i in range(n):
        hidden=sample_rbm_forward(a, c, w, delta)
        visible=sample_grbm(hidden, b, w, delta)
    plt.plot(visible)
    plt.show()

    
#other tools
def visualize(in_index, t):
    index=in_index
    l=[]
    for i in range(t):
        l.append(len(index))
        plt.scatter(P[:,0],P[:,1], s=10)
        plt.scatter(P[index][:,0],P[index][:,1], s=10)
        axes = plt.gca()
        axes.set_xlim([0,1])
        plt.show()
        x=np.zeros(W.shape[0])
        for i in index:x[i]=1
        x=W.dot(x)
        x=(x > 0).astype(int)
        index=[idx for idx, v in enumerate(x) if v]
    print(l)
 

def generate_poly(data_size, n, degree):
    data=np.zeros((data_size, n))
    def poly(x, param):
        p=0
        for i in range(len(param)):
            p=p*x+param[i]
        return p
    for i in range(n):
        a=2*np.random.random([degree+1])-1
        data[:,i]=poly(np.linspace(-1, 1, data_size), a)
    return data


#global variable
size=100
n_cell=150
dataset_size=300
dataset_size_t=400
t=5
sigma=50
d=200
alpha=0.001#backprop rate
error=[]
delta=1#0.05
epsilon_w=0.0000001#rbm rate
epsilon_b=epsilon_w
epsilon_c=epsilon_w
iterr_rbm=1000

P, W, in_index, out_index = build(n_cell, size, size,sparsity=0.05, seed=1)
Wt=abstract_layer(in_index, W, t)
visualize(in_index, t)
wc=copy.deepcopy(Wt[0])
wc*=np.random.normal(0, 0.1, wc.shape)
wc=np.ones((20,100))# llooooooooooooooooooooooookkkkk there there is no spatialised connection scheme
wc*=np.random.normal(0, 0.1, wc.shape)
print(wc.shape)
c=0.0*np.random.randn(wc.shape[0],1)
b=0.0*np.random.randn(wc.shape[1],1)

scaler = preprocessing.MinMaxScaler(feature_range=(-1, 1))
data=generate_poly(size, dataset_size, 2)
data_t=generate_poly(size, dataset_size_t, 5)
scaled_data=preprocessing.scale(data, axis=1)#scaler.fit_transform(data)
scaled_data_t=scaler.fit_transform(data_t)



train_rbm(scaled_data, b, c, wc, delta, iterr_rbm)
for i in range(4):
    plt.plot(wc[i,:])
    plt.show()

"""    

    
x=np.zeros((n_cell,dataset_size))
x[in_index]=scaled_data
x_t=np.zeros((n_cell,dataset_size_t))
x_t[in_index]=scaled_data_t
    
wc,e=train(x, wc, t, in_index, out_index, 1000, alpha)


plt.show()
X, x=forward(x, wc, t)
plt.plot(np.linspace(-1, 1, size),scaled_data)
plt.plot(np.linspace(-1, 1, size),x[out_index])
plt.show()

X, x=forward(x_t[:,0:4], wc, t)


for i in range(3):
    plt.plot(np.linspace(-1, 1, size),scaled_data_t[:,i])
    plt.plot(np.linspace(-1, 1, size),x[:,i][out_index])
    plt.show()




print(e)
print(err(x_t, wc, t)) 
"""