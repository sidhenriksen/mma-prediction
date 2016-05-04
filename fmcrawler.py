import urllib2,google,re,os,random
import fightmetric as fm
import numpy as np
import pickle


def crawl(init_fighter=None,K=2):
    '''
     Basic Fightmetric crawler; will get URLs for all fighter profiles on Fightmetric
    
    Parameters
    ----------
    init_fighter : str (optional)
        Name of the fighter to start the crawl. The URL will be fetched from Google.
    	Default is either a random fighter from existing data, or Mark Hunt if no
    	data exists.
    K : int (optional)
    	Degrees of separation to include. Default is K=2, meaning that the crawler
    	will parse init_fighter (1), and the fighters on init_fighter's page (2).

    Returns
    -------
    fighters : dict
    	Each entry corresponds to a fighter (with the fighter's name as key).
    	The dict contains fighter stats and all the fighter's fights

    '''
    # Usage:


    url_file = 'url_list.txt'
    fighter_file = 'fighters.pickle'
    dir = os.listdir('./')

    # Read list of parsed URLs if it exists, otherwise init to empty list
    if url_file in dir:
        with open(url_file,'r') as f:
            url_list_raw = f.readlines()
            url_list = [k.replace('\n','') for k in url_list_raw]
    else:
        url_list = []
    
    # Load fighter data if it exists, otherwise init to empty dict
    if fighter_file in dir:
        with open(fighter_file,'r') as ff:
            fighter_data = pickle.load(ff)
            if init_fighter == None:
                init_fighter=random.sample(fighter_data.keys(),1)[0]
    else:
        if init_fighter==None:
            init_fighter='Mark Hunt'

        fighter_data = {}

    # Create the base of the tree
    fighter_url = fm.get_url(init_fighter)
    fighter_page = fm.get_page(fighter_url)
    init_urls = fm.get_fighter_urls(fighter_page)
    fighters = {fighter_url:init_urls}

    for k in range(K): 
        print "Degree %i of %i"%(k+1,K)
        for fighter in fighters:
            new_fighters = {}
            print 'Running fighter: %s'%fighter
            if fighter not in url_list:
                current_fighters = fighters[fighter]
                print 'Found %i links.'%len(current_fighters)

                ctr=0
                for cf in current_fighters:
                    if cf not in url_list:
                        ctr +=1

                        current_page = fm.get_page(cf)
                        if current_page[0] == 'Empty page':
                            print 'Empty page returned. Skipping.'
                            continue

                        cf_data,new_fighters = fm.parse_page(current_page)

                        cf_data['url'] = cf

                        fighter_data[cf_data['Name']] = cf_data
                        

                        new_fighters[cf]=new_fighters

                        url_list.append(fighter)

                
                if ctr > 0:
                    print 'Found %i new fighters. Saving data.'%ctr
                    with open(url_file,'w') as f:
                        f.writelines([fighter+'\n' for fighter in url_list])

                    with open(fighter_file,'w') as ff:
                        pickle.dump(fighter_data,ff)

                else:
                    print 'No new fighters.'

        fighters.update(new_fighters)


    return fighters

    
