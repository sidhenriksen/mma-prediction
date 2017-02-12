import pandas as pd
import numpy as np
import networkx as nx
import pickle,copy,random,fmcrawler_sql,sqlite3


from scipy.sparse import csc_matrix

def page_rank(G, s = .85, maxerr = .001):
    """
    Computes the pagerank for each of the n states.
    Used in webpage ranking and text summarization using unweighted
    or weighted transitions respectively.
    Args
    ----------
    G: matrix representing state transitions
       Gij can be a boolean or non negative real number representing the
       transition weight from state i to j.
    Kwargs
    ----------
    s: probability of following a transition. 1-s probability of teleporting
       to another state. Defaults to 0.85
    maxerr: if the sum of pageranks between iterations is bellow this we will
            have converged. Defaults to 0.001
    
    Attribution note: Not written by sh
    """
    n = G.shape[0]

    # transform G into markov matrix M
    M = csc_matrix(G,dtype=np.float)
    rsums = np.array(M.sum(1))[:,0]
    ri, ci = M.nonzero()
    M.data /= rsums[ri]

    # bool array of sink states
    sink = rsums==0

    # Compute pagerank r until we converge
    ro, r = np.zeros(n), np.ones(n)
    while np.sum(np.abs(r-ro)) > maxerr:
        ro = r.copy()
        # calculate each pagerank at a time
        for i in xrange(0,n):
            # inlinks of state i
            Ii = np.array(M[:,i].todense())[:,0]
            # account for sink states
            Si = sink / float(n)
            # account for teleportation to state i
            Ti = np.ones(n) / float(n)

            r[i] = ro.dot( Ii*s + Si*s + Ti*(1-s) )

    # return normalized pagerank
    return r/sum(r)


def create_fight_matrix(fights):
    '''
    Creates a fight adjacency matrix, where each row/column corresponds 
    to a fighter. The winner is always the column fighter, such that
    entry fight_matrix[i,j]=1 means that fighter j won over fighter i.
    
    Parameters
    ----------
    fights : dict
	     Scraped fights dict through using fmcrawler. This will be
	     saved in fighters.pickle.
    
    Returns
    -------
    fight_matrix : pd.DataFrame
    	     NxN matrix where N is the number of fighters. 
    '''

    fighters = []
    for fight in fights:
        fighters.extend(fight['Fighters'])
    

    fighters = np.unique(fighters)

    # init matrix as DataFrame
    fight_matrix = pd.DataFrame(np.zeros([len(fighters),len(fighters)]),index=fighters,columns=fighters)

    # iterate over all fights and fill in appropriate entry
    for fight in fights:
        fighter1=fight['Fighters'][0]
        fighter2=fight['Fighters'][1]
        
        if fight['Result'] == fighter1:
            col=fighter1
            row=fighter2
        elif fight['Result'] == fighter2:            
            col=fighter2
            row=fighter1

        fight_matrix.loc[row,col] = 1.0

    return fight_matrix

def create_fight_graph(fights):
    '''
    Creates a NetworkX fight graph, where each node is a fighter and
    each directed edge corresponds to a result. A node pointing
    from node i to node j means that fighter j won over fighter i.
    
    Parameters
    ----------
    fights : dict OR pd.DataFrame
	     Scraped fights dict through using fmcrawler. This will be
	     saved in fighters.pickle.
    	     OR
	     fight_matrix returned from calling create_fight_matrix.
    
    Returns
    -------
    G : nx.DiGraph
             NetworkX graph with N nodes, and K edges, corresponding
    	     to the number of fighters and fighths, respectively.
    '''

    # This lets you pass either a fights list or a fight_matrix
    if type(fights) == list:
        fight_matrix = create_fight_matrix(fights)
    elif type(fights) == pd.core.frame.DataFrame:
        fight_matrix = fights
    
    # init graph and add nodes
    G = nx.DiGraph()
    nodes = fight_matrix.columns
    G.add_nodes_from(nodes)    

    i,j = np.where(fight_matrix==1.0) # find indices for edges

    edges = [(nodes[i[k]],nodes[j[k]]) for k in range(len(i))] #add edges
    G.add_edges_from(edges)

    return G


def prune_graph(G,base_node,K):
    '''
    Takes an existing fight graph and a base node and prunes all nodes 
    which are either not connected to the base node or whose shortest
    path to the base_node is longer than K.
    
    Parameters
    ----------
    G : nx.DiGraph
	    Fight graph, e.g. created using create_fight_graph. 
    base_node : str, int
    	    Name of the base node in the network.
    K : int
            Integer value specifying the shortest path threshold.

    Returns
    -------
    G : nx.DiGraph
            Pruned network graph    	
    '''

    G = G.copy()
    if G.is_directed():
        G_un = G.to_undirected()
    else:
        G_un = G

    for node in G_un.nodes():
        if nx.has_path(G,base_node,node):
            L = nx.shortest_path_length(G,base_node,node)
        else:
            L = np.inf

        if L > K:
            G.remove_node(node)
    
    return G

def compute_graph_metrics(G,base_node):
    A = nx.adjacency_matrix(G)
    PR = page_rank(A)

    return PR
    

def get_fights(fighter,dbfile='fighterdb.sqlite'):
    '''
    Takes a fighters dict, processes the fights and returns a list of
    fights

    Parameters
    ----------
    fighter : str
    	      Name of the fighter
    	       
	      

    Returns
    -------
    fights : list
    	     A list of all the fights from fighters   
    '''

    # this lets us optionally pass a cursor instead of the database file name
    if type(dbfile)==str:
        conn = sqlite3.connect(dbfile)
        cur = conn.cursor()
    else:
        cur = dbfile

    data = sql_to_list('Fights',cur)

    # So we need to check whether we have repetitions in the Fights and Fighters,
    # and also work out the best way to structure this data.
    
    fights = [fight for fight in data if fighter in [fight['fighter1'],fight['fighter2']]]

    return fights

def build_features(fighters):

    fighterNames = fighters.keys()
    fights = []
    for name in fighterNames:
        
        currentFights = get_fights(name)
        
        fights.extend(currentFights)

    X = []

    y = []

    for fight in fights:
        f1Name = fight['fighter1']
        f2Name = fight['fighter2']

        if (f1Name not in fighters.keys()) or (f2Name not in fighters.keys()):
            continue
        
        currentFeatureVector = build_matchup(fighters[f1Name],\
                                             fighters[f2Name])

        X.append(currentFeatureVector)

        y.append(np.double(fight['winner'] == f2Name))
        

    X = pd.concat(X)
    
    y = np.array(y)

    
    # if we're missing date of birth for one fighter, set their date of births to be the same    
    missingF1DobIdx = np.isnan(X.f1_dob)
    missingF2DobIdx = np.isnan(X.f2_dob)
    missingBothDobIdx = missingF1DobIdx & missingF2DobIdx
    X.loc[missingF1DobIdx,'f1_dob'] = X.loc[missingF1DobIdx,'f2_dob'].values
    X.loc[missingF2DobIdx,'f2_dob'] = X.loc[missingF2DobIdx,'f1_dob'].values
    X.loc[missingBothDobIdx,'f1_dob'] = 1988
    X.loc[missingBothDobIdx,'f2_dob'] = 1988
        
    return X,y
        
    

def build_matchup(fighter1,fighter2):
    ''' 
    Builds a single feature vector for a fight between two fighters.
    Note that this only considers fighter stats at the present moment
    in time (except age... maybe)

    Parameters
    ----------
    fighter1 : dict
    	       fighter dictionary containing stats on the first fighter
    fighter2 : dict
    	       fighter dictionary containing stats on the second fighter

    Returns
    -------
    X : pd.DataFrame
    	A single-row data frame corresponding to our feature vector   
    '''

    feature_list = ['height','reach','sapm','slpm','stance','stracc',\
                    'strdef','subavg','tdacc','tdavg','tddef',\
                    'weight','dob','wins','losses','cumtime']

    tagged_features = ['f1_'+f for f in feature_list]+['f2_'+f for f in feature_list]
    X = pd.DataFrame(columns=tagged_features,dtype=float)

    for feature in feature_list:
        f1='f1_'+feature
        f2='f2_'+feature
        
        cf1=fighter1[feature]
        cf2=fighter2[feature]
            
        if feature == 'dob':
            if cf1=='--':
                cf1=np.nan
            else:
                cf1=2017-float(cf1[-4:])

            if cf2=='--':
                cf2=np.nan
            else:
                cf2=float(cf2[-4:])

        if feature == 'stance':
            if cf1 == 'Orthodox':
                cf1=0.0
            else:
                cf1=1.0
                
            if cf2 == 'Orthodox':
                cf2=0.0
            else:
                cf2=1.0

        X.loc[0,f1]=float(cf1)
        X.loc[0,f2]=float(cf2)



    return X



def sql_to_list(tableName,cur):

    pragmaExpr = 'PRAGMA table_info( %s )'%tableName
    
    cur.execute(pragmaExpr)

    columnData = cur.fetchall()

    columnNames = [t[1] for t in columnData]

    selectExpr = 'SELECT * FROM %s'%tableName
    cur.execute(selectExpr)

    tableData = cur.fetchall()

    dataList = []
    
    for entry in tableData:
        currentFight = {name:entry[i] for i,name in enumerate(columnNames)}
                
        dataList.append(currentFight)

    return dataList

def get_fighters(dbfile='fighterdb.sqlite'):

    conn = sqlite3.connect(dbfile)

    cur = conn.cursor()

    dataList = sql_to_list('Fighters',cur)

    dataDict = {}

    for entry in dataList:
        
        name = entry.pop('name')
        _ = entry.pop('id')

        dataDict[name] = entry

    conn.close()
    return dataDict




