import urllib2,google,re,os,random,sqlite3
import fightmetric as fm
import numpy as np


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

    conn = sqlite3.connect(dbfile,timeout=10)
    cur = conn.cursor()

    cur.executescript('''
    DROP TABLE IF EXISTS Fighters;
    DROP TABLE IF EXISTS Fights;
    DROP TABLE IF EXISTS FighterURLs;

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
    strdef	REAL,
    wins	INTEGER,
    losses	INTEGER,
    cumtime	REAL
    );

    CREATE TABLE FighterURLs (
    id		INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    url		TEXT UNIQUE, 
    fighter_id  INTEGER UNIQUE,
    processed   INTEGER
    );

    CREATE TABLE Fights (
    id		INTEGER NOT NULL PRIMARY KEY UNIQUE,
    fighter1 	TEXT,
    fighter2 	TEXT,
    event	TEXT,
    method	TEXT,
    pass1	REAL,
    pass2 	REAL,
    round 	INTEGER,
    str1 	REAL,
    str2	REAL,
    sub1	REAL,
    sub2	REAL,
    td1 	REAL,
    td2		REAL,
    time	REAL,
    winner 	TEXT
    )
    ''')

    conn.commit()

    conn.close()
    
def crawl(initFighter='Mark Hunt',dbfile='fighterdb.sqlite',K=2):
    '''
     Basic Fightmetric crawler; will get URLs for all fighter profiles on Fightmetric
    
    Parameters
    ----------
    initFighter : str (optional)
        Name of the fighter to start the crawl. The URL will be fetched from Google.
    	Default is either a random fighter from existing data, or Mark Hunt if no
    	data exists.
    dbfile : str (optional)
	Name of the database file
    K : int (optional)
    	Degrees of separation to include. Default is K=2, meaning that the crawler
    	will parse initFighter (1), and the fighters on initFighter's page (2).

    Returns
    -------
    fighters : dict
    	Each entry corresponds to a fighter (with the fighter's name as key).
    	The dict contains fighter stats and all the fighter's fights

    '''

    if dbfile not in os.listdir('./'):
        print "Database not found; initialising new database."
        init_db()
        


    # init sqlite stuff
    conn = sqlite3.connect(dbfile,timeout=10)
    
    cur = conn.cursor()

    # Create the base of the tree
    initFighterURL = fm.get_url(initFighter)[11:]

    write_page_to_database(initFighterURL,cur)

    conn.commit()

    fighterURLs = get_url_list(cur)
            
    for k in range(K):

        for fighterURL in fighterURLs:

            pauseInterval = np.random.rand() + 0.5

            # pause for some random time interval
            os.system('sleep %.2f'%pauseInterval) 


            print 'Running fighter: %s'%fighterURL
            
            write_page_to_database(fighterURL,cur)

            conn.commit()

        fighterURLs = get_url_list(cur)

        
            
    return fighterURLs

    
def get_url_list(cur):
    '''
    Returns a list of all URLs which have been added to the database,
    but which still haven't been processed.
    
    Parameters
    ----------
    cur : a sqlite db cursor
    
    Returns
    -------
    fighterURLs : a list of URLs to Fightermetric web pages.
    

    '''
    
    cur.execute(''' SELECT url from FighterURLs WHERE processed = 0 ''')
    
    fighterURLs = [k[0] for k in cur.fetchall()]
    
    return fighterURLs

def add_to_url_list(fighterURLs,processed,cur):
    ''' Adds an entry into the FighterURLs database which lets us know
    whether or not this person's page has been processed.

    
    Parameters
    ----------
    fighterURLs : list of strings
    	a list of URLs for new fighters

    processed : int
    	0 or 1 denoting whether this page has been processed

    cur : sqlite3 cursor
    	% Cursor pointing to the database

    Returns
    -------
    Nothing.
    

    '''
    if processed:
        sqlExpression = '''INSERT OR REPLACE INTO FighterURLs (url,processed)
    		VALUES ( ?, ? )'''
    else:
        sqlExpression = '''INSERT OR IGNORE INTO FighterURLs (url,processed)
    		VALUES ( ?, ? )'''

    # convert to list if (presumably) a string is given
    if type(fighterURLs) == str : fighterURLs = set([fighterURLs])

    for fighterURL in fighterURLs:
        cur.execute(sqlExpression, (fighterURL, processed))





def write_fights_to_database(fights,cur):
    
    for fight in fights:
        sortedFighters = sorted(fight['Fighter'])
        
        bothFighters = sortedFighters[0]+sortedFighters[1]

        fightId = hash(bothFighters+fight['Event'][0])
    

        if fight['outcome'] == 'win':
            winner = fight['Fighter'][0]
        elif fight['outcome'] == 'loss':
            winner = fight['Fighter'][1]
        else:
            winner = 'Draw'

        # Do a quick check
        cur.execute('SELECT fighter1,fighter2 FROM Fights WHERE id == ?',(fightId,))
        matches = cur.fetchall()
        for match in matches:
            if ( sorted(match) != sorted(fight['Fighter']) ):
                 raise AssertionError('Error: Fighters and fight id should match. Probably'+\
                    ' means overlapping ids.')
                 

        cur.execute(\
            '''INSERT OR IGNORE INTO Fights (id, fighter1, fighter2,
            event, method, pass1, pass2, round, str1, str2, sub1, sub2,
    	    td1, td2, time, winner) VALUES ( ?, ?, ?, ?, ?, ?, 
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )''',\
            (fightId,fight['Fighter'][0], fight['Fighter'][1],\
             fight['Event'][0], fight['Method'],\
             fight['Pass'][0], fight['Pass'][1], fight['Round'],\
             fight['Str'][0], fight['Str'][1], fight['Sub'][0],\
             fight['Sub'][1], fight['Td'][0], fight['Td'][1],\
             fight['Time'], winner) )


def write_fighter_to_database(stats,urls,cur):
    key2Sql = {key:strip_key(key) for key in stats.keys()}
    
    fighterURL = stats['url']
    
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

    cur.execute(''' SELECT id FROM Fighters WHERE name = ? ''', (stats['Name'],))
        
    fighter_id = cur.fetchone()[0]
    
    cur.execute('''INSERT OR IGNORE INTO FighterURLs (url,fighter_id)
    		    VALUES ( ?, ? )''', (fighterURL, fighter_id))

    add_to_url_list(urls,0,cur)
    
    add_to_url_list([fighterURL],1,cur)

    
            
def write_page_to_database(fighterURL,cur):

    fighterPage = fm.get_page(fighterURL)

    if fighterPage == ['Empty page']: return None

    stats,urls = fm.parse_page(fighterPage)
    
    fights = stats.pop('Fights')

    stats['url'] = fighterURL

    stats['wins'] = compute_wins(fights)
    
    stats['losses'] = compute_losses(fights)

    stats['cumtime'] = compute_cumtime(fights)

    write_fighter_to_database(stats,urls,cur)

    write_fights_to_database(fights,cur)
    
    
def compute_wins(fights):
    y = np.sum([fight['outcome']=='win' for fight in fights])
    return y

def compute_losses(fights):
    y = np.sum([fight['outcome']=='loss' for fight in fights])
    return y

def compute_cumtime(fights):
    y = np.sum([fight['Time'] for fight in fights])
    return y



def strip_key(mykey):

    newkey = mykey.replace('.','').replace(' ','').lower()

    return newkey




if __name__ == "__main__":
    initFighters = ['Demetrious Johnson',\
		     'TJ Dillashaw',\
		     'Jose Aldo','Conor McGregor',\
                     'Rafael dos Anjos',\
                     'Donald Cerrone',\
                     'Robert Whittaker','Anderson Silva',\
                     'Jon Jones','Alexander Gustafsson',\
                     'Mark Hunt','Stipe Miocic']

    
    for fighter in initFighters:
        print 'Crawling using %s as root'%fighter
        crawl(initFighter=fighter,K=4)
