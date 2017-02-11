
import fmprocess
import sklearn.linear_model as sklin
import numpy as np
import matplotlib.pyplot as plt
import sklearn.ensemble as sken

def buildClassifier():
    fighters = fmprocess.get_fighters()

    #X,y = fmprocess.build_features(fighters)

    X = (X-X.mean(0))/X.std(0) # normalise data

    myClassifier = sken.RandomForestClassifier()
    
    myClassifier.fit(X,y)

    return myClassifier

def predictFight(myClassifier,fighter1Name,fighter2Name):
    fighters = fmprocess.get_fighters()
    fighter1 = fighters[fighter1Name]
    fighter2 = fighters[fighter2Name]

    x = fmprocess.build_matchup(fighter1,fighter2)
    
    p = myClassifier.predict_proba(x)[0][0]

    if p < 0.5:
        flipP = 1-p
        winner = fighter1Name
    else:
        flipP = p
        winner = fighter2Name

    print '%.3f chance that %s wins'%(flipP,winner)
    


if __name__ == "__main__":

    fighters = fmprocess.get_fighters()

    #X,y = fmprocess.build_features(fighters)

    X = (X-X.mean(0))/X.std(0) # normalise data
    
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

