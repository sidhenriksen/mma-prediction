import google,re,urllib2,lxml


def get_fighter(fighter):
    S = get_url(fighter)
    P = parse_url(S)
    return P

def get_url(fighter):

    site = "www.sherdog.com"
    
    query = '"'+fighter+'"' + 'site:'+site
    k = 5
    mysearch = google.search(query,num=k)

    for k in range(k):
        S = mysearch.next()
        if 'fighter' in S:
            return S        

    return 'NaN'

def parse_sherdog(url):

    if 'sherdog' not in url:
        url = 'http://www.sherdog.com'+url

    try:
        url_generator = urllib2.urlopen(url,timeout=2)
        page = url_generator.readlines()
    except IOError:
        return ['Empty page']


    fight_props = parse_fightrecord(page)
    props = parse_props(page)
    props.update(fight_props)
    ufc,ama = parse_fighthistory(page)

    props['Pro fights'] = ufc
    props['Amateur fights'] = ama

    return props

def parse_fightmetric(url):
    if 'fightmetric' not in url:
        url = 'http://fightmetric.com/'
        
    try:
        url_generator = urllib2.urlopen(url,timeout=2)
        page = url_generator.readlines()
    except IOError:
        return ['Empty page']

    fighter_stats = parse_fighter_stats(page)



def parse_fighter_stats(page):
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

def percent_to_prop(S):
    myreg = S.replace('%','')
    return float(myreg)/100.

def ft_to_cm(S):
    val_str = S.replace('"','').replace("'",'').split()
    feet = float(val_str[0])
    inches = float(val_str[1])
    i2cm = 2.54
    f2cm = 30.48
    cm = feet*f2cm + inches*i2cm
    return cm

def in_to_cm(S):
    i2cm = 2.54
    val_str = S.replace('"','')
    inches = float(val_str)
    cm = inches*i2cm
    return cm
    

def lbs_to_kg(S):
    val_str = S.replace('lbs.','')
    lbs = float(val_str)
    kg_per_lb = 0.454
    kg = lbs*kg_per_lb

    return kg


def parse_fightrecord(page):
    start_win = [i for i,k in enumerate(page) if '<div class="bio_graph">' in k][0]
    start_loss = [i for i,k in enumerate(page) if '<div class="bio_graph loser">' in k][0]
    
    props = {'Wins':1,'Losses':1,'KO/TKO':0,'SUBMISSIONS':0,'DECISIONS':0}
    properties = {}
    for i in range(100):
        j = start_win+i
        for prop in props:
            if prop in page[j]:
                val = strip_html(page[j+props[prop]]).strip()

                if prop in val:
                    val = val.replace(prop,'')

                if prop != 'Wins':
                    properties['WIN '+prop] = float(val.split()[0])
                else:
                    properties[prop] = float(val)

        if len(properties) == 4:
            break
           

    for i in range(100):
        j = start_loss+i
        for prop in props:
            if prop in page[j]:
                val = strip_html(page[j+props[prop]]).strip()

                if prop in val:
                    val = val.replace(prop,'')

                if prop != 'Losses':
                    properties['LOSS '+prop] = float(val.split()[0])
                else:
                    properties[prop] = float(val)

        if len(properties) == 8:
            break
    

    return properties

def parse_fighthistory(page):
    ufc_start = False
    amateur_start = False
    amateur_table_start = None
    ufc_table_start = None
    

    for i,p in enumerate(page):
        if 'Fight History' in p:
            ufc_start = True
            amateur_start = False
        elif 'Amateur Fights' in p:
            ufc_start = False
            amateur_start = True

        if '<table' in p:
            if ufc_start:
                ufc_table_start = i
            elif amateur_start:
                amateur_table_start=i

        if '</table>' in p:
            if ufc_start:
                ufc_table_stop = i
            elif amateur_start:
                amateur_table_stop = i

        if '<div class="module black">' in p:
            break
    
    if ufc_table_start != None:
        ufc_history = page[ufc_table_start:ufc_table_stop+1]
        ufc_hstring_raw = [strip_html(k).strip() for k in ufc_history]
        ufc_hstring = [k for k in ufc_hstring_raw if k != '']
        n_ufc_fights = len(ufc_hstring)/6 -1    
        ufc_fights = [{ufc_hstring[i]:ufc_hstring[i+k*6] for i in range(0,6)} for k in range(n_ufc_fights)]
    else:
        ufc_fights = []
    
    if amateur_table_start != None:
        amateur_history = page[amateur_table_start:amateur_table_stop+1]
        amateur_hstring_raw = [strip_html(k).strip() for k in amateur_history]
        amateur_hstring = [k for k in amateur_hstring_raw if k != '']
        n_ama_fights = len(amateur_hstring)/6 -1
        ama_fights = [{amateur_hstring[i]:amateur_hstring[i+k*6] for i in range(0,6)} for k in range(n_ama_fights)]
    else:
        ama_fights = []
    
        
    return ufc_fights,ama_fights


def strip_html(data):
    p = re.compile(r'<.*?>')
    return p.sub('',data)

def parse_props(page):
    props = {'Weight':2,'Height':2,'Association':1,'AGE':0,\
             'Class':0,'nationality':0,'Wins':1,'Losses':1}

    # 0 = not numeric; 1 = numeric and no units; 2 = numeric and units 
    # (e.g. 70 kg)
    is_numeric = {'Weight':2,'Height':2,'Association':0,'AGE':1,\
                  'Class':0,'nationality':0,'Wins':1,'Losses':1}

    properties = {}
    stop = None
    for i,line in enumerate(page):
        if '<div class="module bio_fighter vcard">' in line:
            start = i-300 # a small number of fighters have their names at diff location
        if '<!-- Fighter Biography -->' in line:
            stop = i-1
    


    page = page[start:stop]

    for i,line in enumerate(page):
        for j,prop in enumerate(props):
            if prop in line:                
                raw_val=page[i+props[prop]]
                val = strip_html(raw_val).strip()

                if prop in val:
                    val = val.replace(prop+': ','')

                if is_numeric[prop]==2:
                    if len(val) == 0:
                        var = None
                    else:
                        val = float(val.split()[0])


                    
                if is_numeric[prop]==1:
                    try:
                        val = float(val)
                    except ValueError:
                        val = None



                properties[prop] = val
    

    # And then just add some properties

    name = parse_spanclass(page,'fn')
    nickname= parse_spanclass(page,'nickname')

    if len(nickname)==0:
        nickname=['None']
        
    properties.update({'Name':name[0],'Nickname':nickname[0]})
    return properties


def parse_spanclass(P,prop):
    spanstr = r'<span class="'+prop+'">'
    
    S = []    
    for p in P:
        match = re.search(spanstr,p)


        if match:            
            end_idx = match.end()
            start_idx=end_idx
            mystr = ''
            for k in range(100):
                idx1 = start_idx+k
                idx2 = start_idx+k+7
                
                p_now = p[idx1:idx2].strip()

                if p_now == '</span>':
                    break

                mystr = mystr+p[start_idx+k]

            S.append(strip_html(mystr))
            
    return S
