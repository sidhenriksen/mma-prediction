
import fmprocess
import sklearn.linear_model as sklin
import numpy as np
import matplotlib.pyplot as plt
import sklearn.ensemble as sken
import sklearn.linear_model as sklin

def build_classifier(X=None,y=None):
    fighters = fmprocess.get_fighters()

    if X is None or y is None: # only call this if it's not fed as input
        X,y = fmprocess.build_features(fighters)

    myClassifier = sken.RandomForestClassifier()
#    myClassifier = sklin.LogisticRegression()
    myClassifier.meanNorm = X.mean(0)
    myClassifier.sdNorm = X.std(0)
    myClassifier.normalise = lambda x:(x-myClassifier.meanNorm)/myClassifier.sdNorm
    
    X = myClassifier.normalise(X)
    
    myClassifier.fit(X,y)

    return myClassifier

def predict_fight(myClassifier,fighter1Name,fighter2Name,predict_proba=True):
    fighters = fmprocess.get_fighters()
    fighter1 = fighters[fighter1Name]
    fighter2 = fighters[fighter2Name]

    x = fmprocess.build_matchup(fighter1,fighter2)

    x = myClassifier.normalise(x)

    if predict_proba:
        p = myClassifier.predict_proba(x)[0]

        if p[0] > 0.5:
            realP = p[0]
            winner = fighter1Name
        else:
            realP = p[1]
            winner = fighter2Name

        print '%.2f%% chance of %s winning.'%(realP*100,winner)
            
    p = int(myClassifier.predict(x))

    winner = (fighter1Name,fighter2Name)[p]
        
    print '%s wins.'%winner



    return winner


if __name__ == "__main__":

    fighters = fmprocess.get_fighters()

    print 'Building features (this takes a while)'
#    X,y = fmprocess.build_features(fighters)
    
    p = 0.75

    nTrain = int(len(X)*p)

    randIndex = np.arange(len(X))
    np.random.shuffle(randIndex)

    trainIndex = randIndex[:nTrain]
    
    testIndex = randIndex[nTrain:]
    
    XTrain = X.iloc[trainIndex,:]
    XTest = X.iloc[testIndex,:]
    yTrain = y[trainIndex]
    yTest = y[testIndex]

    myClassifier = sklin.LogisticRegression()

    myClassifier.fit(XTrain,yTrain)

    yhatTrain = myClassifier.predict(XTrain)
    yhatTest = myClassifier.predict(XTest)

    print '--- Logistic regression ---'
    print 'Proportion correct on training data: %.2f'%np.mean(yhatTrain==yTrain)
    print 'Proportion correct on CV data: %.2f'%np.mean(yhatTest==yTest)

    randomForest = sken.RandomForestClassifier()
    randomForest.fit(XTrain,yTrain)

    yhatTrainRF = randomForest.predict(XTrain)
    yhatTestRF = randomForest.predict(XTest)

    print '--- Random Forest ---'
    print 'Proportion correct on training data: %.2f'%np.mean(yhatTrainRF==yTrain)
    print 'Proportion correct on CV data: %.2f'%np.mean(yhatTestRF==yTest)

    

    theta = 0.1
    unsortedCoefs = myClassifier.coef_[0]
    idx = np.argsort(unsortedCoefs)[np.abs(unsortedCoefs)>theta]
    coefs = unsortedCoefs[idx]/np.max(unsortedCoefs)

    coefsRF = randomForest.feature_importances_[idx]
    coefsRF /= np.max(coefsRF)
    
    columnNames = X.columns[idx]

    x = np.arange(0,len(idx)*4,4)

    fig,ax = plt.subplots(1)
    ax.bar(x,coefs,color=[0.8,0.1,0.1],tick_label=columnNames)
    ax.bar(x+1,coefsRF,color=[0.1,0.1,0.8])
    ax.legend(['Logistic regression','Random Forest'],loc='lower right')
    ax.plot(x,x*0,'-',c='k',lw=2)

    ax.set_ylabel('Normalised feature importance',size=14)

    plt.show(block=False)

