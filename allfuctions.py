from PIL import Image
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests, docx2txt, pytesseract, PyPDF2
import collections, pygal
import pandas as pd
import numpy as np

ua=UserAgent()
hdr = {'User-Agent': ua.random,
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
      'Accept-Encoding': 'none',
      'Accept-Language': 'en-US,en;q=0.8',
      'Connection': 'keep-alive'}

olderperms = [('Lists Read Access', 'Personal Information'),
                     ('Lists Write Access', 'Personal Information'),
                     ('lists write access (2)', 'Personal Information'),
                     ('First Name', 'Name'),
                     ('Full Name', 'Name'),
                     ('Given Name', 'Name'),
                     ('Device Country and Postcode', 'device country and postal code'),
                     ('phone number','Mobile Number'),
                     ('zip', 'device country and postal code'),
                     ('address','Device Address'),
                     ('location','Location Services'),
                     ('birthday', 'Personal Information'),
                     ('email','Email Address'),
                     ('area code', 'device country and postal code'),
                     ('gender', 'Personal Information'),
                     ('born','Personal Information'),
                     ('zipcode', 'device country and postal code'),
                     ('postal code', 'device country and postal code')
                    ]
olderrems = ['alexa notifications', 'skill personisation', 'reminders', 'timer', 'birthday', 'gender','skill resumption', 'timers']


def clean_html_file(html):
    text = html.find_all(text=True)
    output = ''
    blacklist = ['[document]','noscript','header','html', 
                'meta', 'head', 'input','script','style'
                ]
    for t in text:
        if t.parent.name not in blacklist:
            output += '{} '.format(t.encode('utf-8').strip())
    return output

#getting privacy policy and permission with fake user agent
def get_url(url):
    res = requests.get(url, headers=hdr)
    html_page = res.content
    soup = BeautifulSoup(html_page, 'html.parser')
    #getting the permission
    skill_permissions = [perm.get_text().strip() for perm in soup.findAll("li", attrs={"class": "a2s-permissions-list-item"})]
    # print(skill_permissions)
    #GETting DYNAMIC CONTENT
    link = [a for a in soup.findAll("a", attrs={"rel": "noopener"})]
    privacy_policy_link = (link[0]['href'])
    try:
        res = requests.get(privacy_policy_link, headers=hdr)
        html_page = res.content
        data = BeautifulSoup(html_page, 'html.parser')
    except:
        data = 'Error Page'
    return (skill_permissions, data)

#getting data from  non text files
def GetData(file_path, file_ext):
    image_ext = ['.png','.jpg', '.jpeg','.gif']
    word_doc= ['.doc','.docx']
    data = 'Error'
    if file_ext == '.pdf':
        with open(file_path,'rb') as pdfFileObj:
            pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
            for i in range (0 , pdfReader.numPages):
                pageObj = pdfReader.getPage(i)
                data = data + (pageObj.extractText())#.encode('ascii','ignore'))
            #print('\n\n\n\n\n',data,'\n\n\n\n\n')
            return data
    elif file_ext in image_ext:
        with Image.open(file_path) as img:
            data = pytesseract.image_to_string(img, lang='eng')
            return str(data.encode('ascii', 'ignore'))
    elif file_ext in word_doc:
        data = docx2txt.process(file_path)
        return data
    else:
        with open(file_path, "r") as fp:
            data = fp.read().encode('ascii', 'ignore')
        return data


marketplaces = {'IT': 'Italy', "IN": 'India', "AU":"Australia", "US": "United State", "UK":"United Kingdom", "FR":"France","DE":"Germany","ES":"Spain","MX":"Mexico","CA":"Canada","JP":"Japan"}
def getNumSkillsDevs(df2019, df2020, df2021):
    allmarkets = df2021.market.unique()
    unique_skills = list()
    unique_devs = list()
    for mk in allmarkets:
        mknew = marketplaces[mk]
        skillyear2019 = len(df2019.loc[df2019['market'] == mk])
        skillyear2020 = len(df2020.loc[df2020['market'] == mk])
        skillyear2021 = len(df2021.loc[df2021['market'] == mk])
        skillyear2019, skillyear2020, skillyear2021 = "{:,}".format(skillyear2019), "{:,}".format(skillyear2020), "{:,}".format(skillyear2021)
        unique_skills.append((mknew, skillyear2019,skillyear2020,skillyear2021))

        alldevs2019 = df2019.loc[df2019['market'] == mk].dev.unique()
        alldevs2020 = df2020.loc[df2020['market'] == mk].dev.unique()
        alldevs2021 = df2021.loc[df2021['market'] == mk].dev.unique()

        devyear2019, devyear2020, devyear2021   = len(alldevs2019), len(alldevs2020), len(alldevs2021)
        devyear2019, devyear2020, devyear2021 = "{:,}".format(devyear2019), "{:,}".format(devyear2020), "{:,}".format(devyear2021)
        unique_devs.append((mknew, devyear2019,devyear2020,devyear2021))
    return (unique_skills, unique_devs)


def preprocessSnapshotPerm(df):
    #skills with Permission in english markets per year
    df_selected = df.loc[ (df['market'].isin(['US', 'UK', 'CA', 'AU', 'IN'])) & (df['perm_requested_norm'].notnull()) ]
    df_selected = df_selected.drop_duplicates(subset='id_name_dev', keep="last")
    return df_selected


def getallYearSkillPerm(df):
    df_selected = preprocessSnapshotPerm(df)
    df = df_selected.drop(['market'], axis = 1)

    df.rename(columns={'name':'Skill','acc_linking':'Account Linking',
                    'cat':'Category', 'dev':'Developer', 
                    'market':'Market','perm_requested_original':'Permission',
                    'traceability':'Traceability','year':'Year',
                    'in_skill_purchase':'In Skill Purchase' }, inplace=True)
    df = df.iloc[:,1:].replace(np.nan, 'None', regex=True).reset_index(drop=True)
    df = df.drop(['skill_link','perm_found_norm','perm_requested_norm', 'id_name_dev'], axis=1)
    return df


def traceByPermissionTypeSkill(df):
    df_selected = preprocessSnapshotPerm(df)
    tracebility = ['R','B','P','C']
    finalresults = {}
    for trace in tracebility:
        if trace == 'R':
            df = df_selected
        else:   
            df = df_selected[df_selected['traceability']== trace]
        to_replace = ["[","]", "'"]
        results = []
        formatresult = []
        for index,row in df.iterrows():
            perms = row['perm_requested_norm']
            try:
                perms = perms.split(",")
            except:
                pass
            if len(perms)> 0:
                for perm in perms:
                    for i in to_replace:
                        if i in perm:
                            perm = perm.replace(i , "")
                    for oldperm in olderperms:
                        if perm.lower().strip() == oldperm[0].lower():
                            perm = perm[1].lower()
                    if perm.lower().strip() not in olderrems:
                        if perm.strip().lower() == 'personal information':
                            perm = 'list'
                        results.append(perm.strip().lower())
    
        for result in (collections.Counter(results)).items():
            formatresult.append(result)
        finalresults[trace] = (len(df), formatresult)
    return(finalresults)


def traceByPermissionTypeDev(df):
    df_selected = preprocessSnapshotPerm(df)
    tracebility = ['R','B','P','C']
    finalresult = {}
    for trace in tracebility:
        if trace == 'R':
            df = df_selected
        else:   
            df = df_selected[df_selected['traceability']== trace]
        to_replace = ["[","]", "'"]
        result = []
        developers_across = []
        permissions = ['device country and postal code', 'device address', 'email address','personal information', 'name', 'mobile number', 'amazon pay','location services']
        for aperm in permissions:
            developers = []
            for index,row in df.iterrows():
                perms = row['perm_requested_norm']
                try:
                    perms = perms.split(",")
                except:
                    pass
                if len(perms)> 0:
                    for perm in perms:
                        for i in to_replace:
                            if i in perm:
                                perm = perm.replace(i , "")

                        for olderperm in olderperms:
                            if perm.lower().strip() == olderperm[0].lower():
                                perm = perm[1].lower()
                        if perm.lower().strip() not in olderrems:

                            if row['dev'] not in developers and (perm.strip().lower()) == aperm:
                                developers.append(row['dev'])

                            if row['dev'] not in developers_across:
                                developers_across.append(row['dev'])   
            if aperm == 'personal information':
                aperm = 'list'
            result.append((aperm, len(developers)))
        
        finalresult[trace] = (len(developers_across), result)
    return(finalresult )
    

def renderChartPermsDev(df, trace):
    devresults = traceByPermissionTypeDev(df)
    devresult = devresults[trace]
    TotalDev = devresult[0]
    dev_bar_chart = pygal.Bar(height=500)  # instance of Bar class
    dev_bar_chart.title = 'Traceability by Permission across Developers'  # title of bar chart
    for index,elem in enumerate(devresult[1]):
        dev_bar_chart.add(elem[0],elem[1])
    devchart = dev_bar_chart.render_data_uri()  # render bar chart
    return devchart

def renderChartPermsSkill(df,trace):
    skillresults = traceByPermissionTypeSkill(df)
    skillresult = skillresults[trace]
    TotalDev = skillresult[0]
    skill_bar_chart = pygal.Bar(height=500)  # instance of Bar class
    skill_bar_chart.title = 'Traceability by Permission across Skills'  # title of bar chart
    for index,elem in enumerate(skillresult[1]):
        if elem[0]== '':
            continue
        skill_bar_chart.add(elem[0],elem[1])
    skillchart = skill_bar_chart.render_data_uri()  # render bar chart
    return skillchart

def unpackGroupByResult(data):
    Broken, Partial, Complete =[],[],[]
    finalresult = {}
    for key, value in data.items():
        cat, trace = key
        if trace == 'B':
            Broken.append((cat, value))
        elif trace == 'P':
            Partial.append((cat, value))
        elif trace == 'C':
            Complete.append((cat, value))
    finalresult ['C']= Complete
    finalresult ['P']= Partial
    finalresult ['B']= Broken
    return finalresult

def renderChartTotaltrace(df,df2,df3):
    x_labels = ['2021','2020','2019']
    #checking for skill
    Totaltrace = df.groupby('traceability')['id_name_dev'].nunique()
    Totaltrace2 = df2.groupby('traceability')['id_name_dev'].nunique()
    Totaltrace3 = df3.groupby('traceability')['id_name_dev'].nunique()
    title = 'Traceability by Skills Per Year'
    skillchartTotaltrace = draw(x_labels,title, Totaltrace, Totaltrace2, Totaltrace3)
    
    #check for developers
    Totaltrace = df.groupby('traceability')['dev'].nunique()
    Totaltrace2 = df2.groupby('traceability')['dev'].nunique()
    Totaltrace3 = df3.groupby('traceability')['dev'].nunique()
    title = 'Traceability by Developers Per Year'
    devchartTotaltrace = draw(x_labels,title, Totaltrace, Totaltrace2, Totaltrace3)
    return skillchartTotaltrace, devchartTotaltrace

def draw(x_labels,title, *argv):
    graph = pygal.Bar(height=500)
    graph.title = title
    graph.x_labels = x_labels
    Broken, Partial, Complete =[],[],[]
    for item in argv:
        for key, value in item.iteritems():
            if key == 'B':
                Broken.append(value)
            elif key == 'P':
                Partial.append(value)
            elif key == 'C':
                Complete.append(value)    
    graph.add('Broken', Broken) 
    graph.add('Partial', Partial) 
    graph.add('Complete', Complete)
    return graph.render_data_uri()

#use this to recategorise the skills
def CatMapping(df):
    
    categorylist = {'Business' : ['Wirtschaft & Finanzen','ビジネス・ファイナンス', 'Business & Finance', 'Affaires et finances','Negocios y Finanzas', 'Negocios y finanzas ',
                'Affari e finanza', 'Negocios y finanzas',],
    'car' : ['Vernetztes Auto','コネクテッドカー','Connected Car', 'Auto connessa', 'Coche conectado',],
    'Education' : ['Bildung & Nachschlagewerke','Education & Reference',' Educación y Referencia', 'Educación y referencia', 'Etudes supérieures',
                 'Educación y Referencia', 'Enseignement et éducation', '教育・レファレンス'],
    'Food': ['Essen & Trinken','フード・ドリンク', 'Food & Drink','Cooking & Recipes', 'Delivery & Takeout', 'Restaurant Booking, Info & Reviews',
            'Wine & Beverages', 'Alimentation et gastronomie','Alimentos y Bebidas','Alimentos y bebidas', 
            'Cibo e bevande',], 
    'Games': ['Spiele und Quiz','Spiele & Quiz','Games & Trivia', 'Games','Game Info & Accessories','Knowledge & Trivia', 'Giochi e quiz',
            'Juegos y Curiosidades','Juegos y curiosidades','Jeux et culture générale', 'ゲーム・トリビア', ],
    'Health': ['Gesundheit & Fitness','ヘルス・フィットネス', 'Health & Fitness','Salud y Bienestar', 'Salud y bienestar', 'Fitness & Sports', 
              'Salute e benessere', 'Santé et bien-être','Safety'],
    'Kids':['子ども向け','Kids', 'Bambini e ragazzi', 'Enfants', 'Kinder', 'Niños', 'Infantil',],
    'Lifestyle': ['ライフスタイル' ,'Stili e tendenze' , 'Stili e tendenze ', 'Lifestyle', 'Home Services', 'Astrology','Cooking & Recipes','Event Finders','Fashion & Style','Friends & Family','Health & Fitness',
                 'Pets & Animals','Religion & Spirituality','Self Improvement','Fan Shop',
                 'To-Do Lists & Notes','Wine & Beverages', 'Estilo de Vida', 'Estilo de vida',],
    'Local' : ['area','地域','Local','Event Finders','Food Delivery & Takeout','Movie Showtimes','Public Transportation',
    'Restaurant Booking', 'Info & Reviews','Schools','Taxi & Ridesharing', 'Consultazione e informazione','Informazioni utili sulle città',],
    'Movies' : ['Film & Fernsehen','映画・TV', 'Movies & TV', 'Knowledge & Trivia','Movie & TV Games','Movie Info & Reviews',
    'Movie Showtimes','TV Guides', 'Film e TV', 'Películas y TV', 'Cinéma et télévision'],
    'Music': ['Musik & Audio','音楽・オーディオ', 'Music & Audio','Accessories', 'Knowledge & Trivia', 'Music Games'," Music Info\, Reviews & Recognition Services",
    'Podcasts', 'Streaming Services', 'Música y Audio', 'Música y audio', 'Music Info, Reviews & Recognition Services','Musica e audio'
    'Musique, radio et audio', 'Maison connectée', 'Musica e audio', 'Musique, radio et audio' ],
    'News' :['Nachrichten','ニュース', 'News','Actualités', 'Noticias', 'Notizie',],
    'Novelty': ['Neuheiten & Humor','ノベルティ・ユーモア', 'Curiosidades y Humor', 'Novelty & Humor',
                'Novelty & Humour', 'Curiosidades y humor', 'Fantaisie et humour', 'Umorismo e curiosità',],
    'Productivity': ['Produktivität','仕事効率化','Productivité', 'Productivity','Alarms & Clocks',
                     'Calculators','Calendars & Reminders','Communication','Organizers & Assistants','Self Improvement','To-Do Lists & Notes','Translators',
                    'Productividad',' Productivité', 'Produttività',"Supporters' Gear"],
    'Shopping' : ['Shopping', 'Compras', 'ショッピング', 'Boutique du supporter'],
    'Home': ['Smart Home','Casa intelligente', 'Hogar digital', 'スマートホーム',],
    'Social': ['Soziale Netzwerke', 'ソーシャル', 'Social','Communication', 'Communication',
               'Dating','Friends & Family','Social Networking',],
    'Sports': ['スポーツ', 'Sports','Exercise & Workout','Games', 'Sport', 'Deportes','Score Keeping','Football'],
    'Travel' : ['Reise & Transport','旅行・交通', 'Travel & Transportation','Currency Guides & Converters','Flight Finders','Hotel Finders','Navigation & Trip Planners',
    'Public Transportation','Taxi & Ridesharing','Translators', 'Viaggi e trasporti', 'Viaje y transporte', 
              'Tourisme et voyages', 'Viaje y Transporte', ],
    'Utilities' : ['Tapes, Adhesives & Sealants','Dienstprogramme','ユーティリティ', 'Home Décor','Utilities','Alarms & Clocks','Calculators','Calendars & Reminders','Device Tracking',
    'Translators','Unit Converters','Zip Code Lookup', 'Utility', 'Servicios',],
    'Weather': ['Wetter','天気','Weather', 'Meteorologia', 'Météo', 'Clima',],}
    
    for i, row in df.iterrows():
        try:
            cat = row['cat'].strip()
        except:
            pass
        for category in categorylist:
            if cat in categorylist[category]:
                df.at[i,'cat'] = category
                break
            else:
                continue
    return df

def renderChartByCat(df,trace):
    elem = df.groupby('cat')['traceability'].value_counts()
    finalresult = unpackGroupByResult(elem)
    skill_per_cat = finalresult[trace]
    cat_skill_bar_chart = pygal.Bar(height=500)  # instance of Bar class
    cat_skill_bar_chart.title = 'Traceability by Category across Skills'  # title of bar chart
    [cat_skill_bar_chart.add(x[0], x[1]) for x in skill_per_cat]
    catskillchart = cat_skill_bar_chart.render_data_uri()  # render bar chart
    return catskillchart
