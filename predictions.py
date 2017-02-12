import fmprocess,classifier
import numpy as np

def ufc208_predictions(X=None,y=None):

    fighters = fmprocess.get_fighters()
    
    if X is None or y is None:
        X,y = fmprocess.build_features(fighters)

    myClassifier = classifier.build_classifier(X,y)

    currentFights = [('Holly Holm','Germaine de Randamie'),\
              ('Anderson Silva', 'Derek Brunson'),\
              ('Jacare Souza','Tim Boetsch'),\
              ('Glover Teixeira','Jared Cannonier'),\
              ('Dustin Poirier','Jim Miller'),\
              ('Randy Brown','Belal Muhammad'),\
              ('Wilson Reis','Ulka Sasaki'),\
              ('Nik Lentz','Islam Makhachev'),\
              ('Ian McCall','Jarred Brooks'),\
              ('Phillipe Nover','Rick Glenn'),\
              ('Ryan LaFlare','Roan Carneiro')]

    fighters = fmprocess.get_fighters()

    winners = []
    
    for fight in currentFights:
        if (fight[0] not in fighters) or (fight[1] not in fighters):
            print '%s vs %s skipped as one or both fighters not in database.'%fight
            print ' '
            continue

        print '%s vs %s'%fight
        winner=classifier.predict_fight(myClassifier,fight[0],fight[1])
        print ' '

        winners.append(winner)

    return winners

        

def dummy_analysis():

    fighters = fmprocess.get_fighters()

    allOutcomes = []


    for fighterName in fighters.keys():
        fights = fmprocess.get_fights(fighterName)
        outcome = [fight['fighter1']==fight['winner'] for fight in fights]
        allOutcomes.extend(outcome)


    return allOutcomes
