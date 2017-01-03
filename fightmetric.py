import urllib2,re,google
from fetch import strip_html


def get_url(name):
    '''
    Searches Google for a specified name and searches fightmetric.com
    for the fighter profile.

    Parameters
    ----------
    name : str
    	Name of fighter

    Returns
    -------
    S : str
    	URL for the fighter's Fightmetric profile

    '''

    site = "http://fightmetric.com"
    
    query = '"'+name+'"' + ' site:'+site
    k = 5
    mysearch = google.search(query,num=k+1)

    for k in range(k):

        S = mysearch.next()

        if 'fighter-details' in S:
            return S        

    return 'NaN'

    
def get_page(url):
    if 'fightmetric' not in url:
        url = 'http://fightmetric.com/'+url

    if 'http://' not in url:
        url = 'http://'+url

    n_attempts = 3

    page = ['Empty page']
    
    for k in range(n_attempts):
        try:
            url_generator = urllib2.urlopen(url,timeout=2)
            page = url_generator.readlines()
            break
        except IOError:
            if k == n_attempts: return ['Empty page']


    return page


def parse_page(page):
    '''
    Parses a Fighter's profile page, obtains stats and a list of fights

    Parameters
    ----------
    page : list
    	Fighter profile page obtained by calling get_page.

    Returns
    -------
    fighter_stats : dict
    	Contains all stats for the fighter, including list of fights.
    
    urls : list
    	List of all the URLs on the fighter's profile.

    '''

    fighter_stats = parse_stats(page)
    fights = parse_fights(page)

    fighter_stats['Fights'] = fights
    try:
        if len(fights) == 0:        
            name = 'Unknown fighter'
        else:
            name = fights[0]['Fighter'][0]
            
    except IndexError:
        import pdb; pdb.set_trace()
        
    fighter_stats['Name'] = name

    urls = get_fighter_urls(page)

    return fighter_stats,urls



def parse_stats(page):
    '''
    Parse the stats on a fighter's Fightmetric page
    
    Parameters
    ----------
    page : list
    	A fighter's Fightmetric profile page (provided by get_page)

    Returns
    -------
    fighter_stats : dict
    	dict of statistics for fighter (see Fightmetric.com for explanation)

    '''
    metrics = ['Height', 'Weight','Reach', 'STANCE', 'DOB','SLpM',\
               'Str. Acc.','SApM','Str. Def','TD Avg.','TD Acc.',\
               'TD Def.', 'Sub. Avg.']

    fighter_stats = {}
    for metric in metrics:
        if metric == 'DOB' or metric == 'SLpM':
            k =3
        else:
            k =2

        raw_val = [page[i+k] for i,p in enumerate(page) if metric+':' in p][0]
        
        val_str = raw_val.strip()

        if '%' in val_str:
            val = percent_to_prop(val_str)
        
        elif metric == 'Height':
            val = ft_to_cm(val_str)

        elif metric == 'Weight':
            val = lbs_to_kg(val_str)
            
        elif metric == 'Reach':
            val = in_to_cm(val_str)


            
        elif metric != 'DOB' and metric != 'STANCE':
            val = float(val_str)

        else:
             val = val_str   

        fighter_stats[metric] = val
        
    return fighter_stats

def parse_fights(page):
    '''
    Parse the fights on a fighter's Fightmetric page
    
    Parameters
    ----------
    page : list
    	A fighter's Fightmetric profile page (provided by get_page)

    Returns
    -------
    fights : list
    	Contains all the fights listed on the fighter's profile page

    '''    
    ctr = 0
    fights = []
    open_td = False # this is if the table row has opened
    open_outcome = False # this is if the fight outcome has been mentioned

    open_th = False    
    
    columns = []
    current_col = 'None'
    for p in page:
        
        
        if '<th' in p:
            open_th = True
            current_th = ''
        if '</th' in p and open_th:
            # then the row is complete and we can parse
            open_th = False
            current_col = strip_html(current_th).strip()
            columns.append(current_col)

        if open_th:
            current_th += ' ' + p
            

        if 'win<i' in p:
            current_fight = {'outcome':'win'}
            open_outcome = True

        if 'loss<i' in p:
            current_fight = {'outcome':'loss'}
            open_outcome = True

        if '<td' in p and open_outcome:
            ctr += 1
            current_td = ''
            open_td = True

            
        if '</td' in p and open_outcome and open_td:            
            # then the row is complete and we can start parsing
            open_td = False

            current_col = columns[ctr]
            current_val = strip_html(current_td).strip()
            current_val = current_val.replace('\n','')

            if current_col not in ['Method','Round','Time']:                
                mid_idx = int(len(current_val)/2.)
                prop1 = current_val[0:mid_idx].replace(' ','')
                prop2 = current_val[mid_idx:].replace(' ','')                
                if current_col not in ['W/L','Fighter','Event']:
                    prop1 = float(prop1)
                    prop2 = float(prop2)

                props = [prop1,prop2]
                current_val = props
            else:
                current_val = current_val.replace(' ','')

                if current_col == 'Time':
                    current_val = mins_to_sec(current_val)
                    
                if current_col == 'Round':
                    current_val = float(current_val)
                        
            current_fight[current_col] = current_val
            

        if open_td and open_outcome:
            current_td += ' ' + p

            
        # this signals the end of the current row
        if '</tr>' in p and ctr == len(columns)-1:
            for i,name_cat in enumerate(current_fight['Fighter']):
                myre = re.findall('[a-zA-Z][A-Z0-9]',name_cat)
        
                name = name_cat.replace(myre[0],myre[0][0]+' '+myre[0][1])
                current_fight['Fighter'][i] = name

            fights.append(current_fight)
            open_outcome = False
            ctr = 0
                
    return fights

def get_fighter_urls(page):
    '''
    Returns all fighter URLs on a fighter's profile page

    Parameters
    ----------
    page : list
    	A fighter's profile page

    Returns
    -------
    url_list : set
	Set of fighter URLs contained on the profile page

    '''
    # This gets the html from a page whose link is given in S and 
    # fetches all the /fighter/FirstName-LastName-ID phrases on that page

    url_list_all = [find_url(k) for k in page]
    url_list_clean = [k for k in url_list_all if k != []]
    url_list = set([link for flist in url_list_all for link in flist])

    return url_list

def find_url(S):
    '''
    Finds the fightmetric.com URLs in a string
    
    Parameters
    ----------
    S : string
    	
    urls_fx : list
    	list of URLs contained in S   
    '''
    urlregex='fightmetric.com/fighter-details/.*"'    
    urls = re.findall(urlregex,S)
    urls_fx = [k[0:-1] for k in urls]

    return urls_fx


######################################
### These are conversion functions ###
######################################
def mins_to_sec(S):
    S2 = S.replace(':',' ').split()
    mins = float(S2[0])
    secs = float(S2[1])
    
    total_secs = mins*60 + secs
    return total_secs

def percent_to_prop(S):
    myreg = S.replace('%','')
    return float(myreg)/100.

def ft_to_cm(S):
    val_str = S.replace('"','').replace("'",'').split()
    if '--' in val_str:
        return 0
        
    feet = float(val_str[0])
    inches = float(val_str[1])
    i2cm = 2.54
    f2cm = 30.48
    cm = feet*f2cm + inches*i2cm
    return cm

def in_to_cm(S):
    i2cm = 2.54
    val_str = S.replace('"','')
    if val_str == '--':
        return 0
    inches = float(val_str)
    cm = inches*i2cm
    return cm
    

def lbs_to_kg(S):
    val_str = S.replace('lbs.','')
    if val_str == '--':
        return 0
    lbs = float(val_str)
    kg_per_lb = 0.454
    kg = lbs*kg_per_lb

    return kg
