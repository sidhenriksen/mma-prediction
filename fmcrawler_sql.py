import urllib2,google,re,os,random,sqlite3
import fightmetric as fm
import numpy as np
import pickle # remove this


def init_db(dbfile='fighterdb.sqlite'):
    '''
    Function to initialise the database. This should be called the first
    time you run the crawler, or whenever you want to create a fresh database.

    Parameters
    ----------
    dbfile : string (optional)
    	Name of the database file.

    Returns
    -------
    Nothing.
    '''

    conn = sqlite3.connect(dbfile)
    cur = conn.cursor()

    cur.executescript('''
    DROP TABLE IF EXISTS Fighters;
    DROP TABLE IF EXISTS Fights;

    CREATE TABLE Fighters (
    id		INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name	TEXT UNIQUE,
    url         TEXT UNIQUE,  
    weight	REAL,
    height	REAL,
    slpm        REAL,
    stance	TEXT,
    sapm 	REAL,
    dob		TEXT,
    subavg	REAL,
    reach	REAL,
    tdacc	REAL,
    tddef	REAL,
    tdavg	REAL,
    stracc	REAL,
    strdef	REAL
    );

    CREATE TABLE Fights (
    id		INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    fighter1_id INTEGER,
    fighter2_id INTEGER,
    url         TEXT UNIQUE
    )
    ''')

    conn.commit()
    
def crawl(init_fighter='Mark Hunt',dbfile='fighterdb.sqlite',K=2):
    '''
     Basic Fightmetric crawler; will get URLs for all fighter profiles on Fightmetric
    
    Parameters
    ----------
    init_fighter : str (optional)
        Name of the fighter to start the crawl. The URL will be fetched from Google.
    	Default is either a random fighter from existing data, or Mark Hunt if no
    	data exists.
    dbfile : str (optional)
	Name of the database file
    K : int (optional)
    	Degrees of separation to include. Default is K=2, meaning that the crawler
    	will parse init_fighter (1), and the fighters on init_fighter's page (2).

    Returns
    -------
    fighters : dict
    	Each entry corresponds to a fighter (with the fighter's name as key).
    	The dict contains fighter stats and all the fighter's fights

    '''

    if dbfile not in os.listdir('./'):
        print "Database not found; initialising new database."
        init_db()
        
    skipExistingFighters = False
    
    conn = sqlite3.connect(dbfile)
    
    cur = conn.cursor()

    url_file = 'url_list.txt'
    
    dir = os.listdir('./')

    # Read list of parsed URLs if it exists, otherwise init to empty list
    if url_file in dir:
        with open(url_file,'r') as f:
            url_list_raw = f.readlines()

            url_list = [k.replace('\n','') for k in url_list_raw]        

            if skipExistingFighters:
                
                cur.execute('SELECT url FROM Fighters')
                existing_urls_tuple = cur.fetchall()
                existing_urls = [k[0] for k in existing_urls_tuple]
                
                url_list = list(set(url_list).union(set(existing_urls)))
            
    else:
        url_list = []

    # Create the base of the tree
    fighter_url = fm.get_url(init_fighter)
    
    fighter_page = fm.get_page(fighter_url)

    init_urls = page_to_sql(fighter_page,fighter_url,cur)
    
    fighter_urls = {fighter_url:init_urls}

    
    for k in range(K):
        print "Degree %i of %i"%(k+1,K)
        for fighter_url in fighter_urls:
            new_fighter_urls = {}

            print 'Running fighter: %s'%fighter_url
            if fighter_url not in url_list:
                current_fighter_urls = fighter_urls[fighter_url]
                print 'Found %i links.'%len(current_fighter_urls)

                ctr=0
                for cf_url in current_fighter_urls:
                    if cf_url not in url_list:
                        ctr +=1
                        
                        pauseInterval = np.random.rand()*0.9 + 0.1
                        
                        os.system('sleep %'%pauseInterval)
                        
                        current_page = fm.get_page(cf_url)
                        
                        if current_page[0] == 'Empty page':
                            print 'Empty page returned. Skipping.'
                            continue

                        cf_opponent_urls = page_to_sql(current_page,cf_url,cur)
                        
                        new_fighter_urls[cf_url]=cf_opponent_urls

                        url_list.append(cf_url)


                
                if ctr > 0:
                    print 'Found %i new fighters. Saving data.'%ctr
                    with open(url_file,'w') as f:
                        f.writelines([myurl+'\n' for myurl in url_list])

                    conn.commit()

                else:
                    print 'No new fighters.'


        fighter_urls.update(new_fighter_urls)


    return fighter_urls

    


def page_to_sql(fighter_page,fighter_url,cur):

    stats,urls = fm.parse_page(fighter_page)

    stats['url'] = fighter_url

    key2Sql = {key:strip_key(key) for key in stats.keys()}

    _ = key2Sql.pop('Fights')
    
    sqlExpression = 'INSERT OR REPLACE INTO Fighters ( '
    for i,k in enumerate(key2Sql):
        if i == (len(key2Sql)-1):
            delim = ''
        else:
            delim = ', '
            
        sqlExpression += key2Sql[k]+delim

    sqlExpression += ') VALUES ( ' + '?, '*(len(key2Sql)-1) + '? )'

    dataTuple = tuple([stats[key] for key in key2Sql])

    cur.execute(sqlExpression,dataTuple)

    return urls
    

def strip_key(mykey):

    newkey = mykey.replace('.','').replace(' ','').lower()

    return newkey




if __name__ == "__main__":
    K = 6
    init_fighters = ['Demetrious Johnson',\
		     'TJ Dillashaw',\
		     'Jose Aldo','Conor McGregor',\
                     'Rafael dos Anjos',\
                     'Donald Cerrone',\
                     'Robert Whittaker','Anderson Silva',\
                     'Jon Jones','Alexander Gustafsson',\
                     'Mark Hunt','Stipe Miocic']

    for fighter in init_fighters:
        print 'Crawling using %s as root'%fighter
        crawl(init_fighter=fighter,K=6)
