import PolicyAnalyser, os, requests
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import allfuctions
import pandas as pd


alldatasets = [
    '/var/www/vhost/skillvet.nms.kcl.ac.uk/public/source/Data2019.csv',
    '/var/www/vhost/skillvet.nms.kcl.ac.uk/public/source/Data2020.csv',
    '/var/www/vhost/skillvet.nms.kcl.ac.uk/public/source/Data2021.csv',
]

df2019 = pd.read_csv(alldatasets[0])
df2020 = pd.read_csv(alldatasets[1])
df2021 = pd.read_csv(alldatasets[2])


year = {'2019': df2019, '2020':df2020, '2021':df2021}
realtrace={'B':'Broken', 'P': 'Partial', 'C':'Complete', 'R':'all'}

#getting number of unique skills and developers
headings = ("Markets", "May 2019","July 2020","April 2021")
unique_skills, unique_devs = allfuctions.getNumSkillsDevs(df2019, df2020, df2021)

#Preprocess a Snapshot dataframe for analysis default 2021
df = allfuctions.getallYearSkillPerm(df2021)

#get devs and skills traceability default 2021
trace = 'C'
requestYear = '2021'
yearperm = year[requestYear]
devpermchart = allfuctions.renderChartPermsDev(yearperm, trace)
skillpermchart = allfuctions.renderChartPermsSkill(yearperm, trace)


#get traceability by category default C
catskillchart = allfuctions.renderChartByCat(yearperm, trace)
skillchartTotaltrace, devchartTotaltrace = allfuctions.renderChartTotaltrace(df2021,df2020,df2019)

#UPLOAD_FOLDER = 'uploads'
UPLOAD_FOLDER = '/var/www/vhost/skillvet.nms.kcl.ac.uk/public/uploads'
headers = {'User-Agent': 'Mozilla/8.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpeg','.jpg', '.png', '.gif', '.pdf','.txt','.html','.docx']
app.config['UPLOAD_PATH'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'happy_to_guess_some_random _strings_for_ICO'


olderperm1 = ['list read access', 'list write access']
olderperm2 = ['Full Name','First Name']

path = app.config['UPLOAD_PATH'] + '/' 
filename= 'temp.txt'
data = ''

def get_parameter(filename,permissions_requested, data):
    #adapt older permissions to new ones
    permissions_requested_adapt = ['personal information' if perm in olderperm1 else 'name' if perm in olderperm2 else perm for perm in permissions_requested]

    models = PolicyAnalyser.LoadModels()
    PolicyPath = path + filename
    perm_found = PolicyAnalyser.AnalysePolicy(PolicyPath, models, smartNegation=True, smartNone=True, kwfilter = False, kw_ignore_filter=True, splitintolines = True)

    permissions_found = [p.lower() for p in perm_found[0] if p.lower() != 'none']

    permissions = []
    sentences = []
    to_remove =["{","}","'"]
    for perm in perm_found[1]:
        if "{'None'}" not in perm:
            permission, sentence = perm.split(":",1)
            for charc in to_remove:
                if charc in permission:
                    permission = permission.replace(charc, "")
            permissions.append(permission)
            sentences.append(sentence)
    sentence_length = len (sentences)

    #if we find 'device address' we also find 'device country and postal code', because the latest is a subset
        #of the first.
    if('device address' in permissions_found):
        permissions_found.append('device country and postal code')
    #find the traceability
    typetraceability = None
    if( set(permissions_requested_adapt).issubset(set(permissions_found)) ):
        typetraceability = 'Complete'
    elif( (len(permissions_found) == 0 or (len(permissions_found) == 1 and 'none' in permissions_found))
            and len(permissions_requested_adapt)>0):
        typetraceability = 'Broken'
    else:
        #check if any permission found fits with the permission requested by the skill
        typetraceability = 'Broken'
        for p in permissions_requested_adapt:
            if(p in permissions_found or 'personal information' in permissions_found):
                typetraceability = 'Partial'
    

    #converting the permission to title case for presentation            
    permissions_found = [perm.title() for perm in permissions_found]
    return show_chart(scroll='Result', sentences= sentences, permissions = permissions, sentence_length=sentence_length,
                        typetraceability = typetraceability,
                        permissions_requested = permissions_requested,
                        permissions_found = set(permissions_found),
                        permissions_requested_adapt = set(permissions_requested_adapt),
                        data = data)

@app.errorhandler(413)
def too_large(e):
    return "File is too large. Try a smaller file ", 413

@app.route('/')
def index():
    return show_chart()

def upload():
    data = ''
    filename = 'temp.txt'
    permissions_requested = request.form.getlist('permission')

    #First check for URL selection
    try:
        urllink = request.form['url']
        if urllink!='':
            permissions_requested, html = allfuctions.get_url(urllink)
            data = allfuctions.clean_html_file(html)
    except:
        pass

    #selection is File 
    try:
        uploaded_file = request.files['file']
        #getting filename
        filename = secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            #checking to see if file is allowed
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                return "Invalid file", 400
            #Saving the uploaded file       
            uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
            data = allfuctions.GetData(path + filename,file_ext)
            #Converting PDF to text and save
            if (file_ext != ".txt"):     
                filename = filename.replace(file_ext, '.txt')
                with open(path + filename, 'w') as fil:
                    fil.write(data.encode('ascii', 'ignore').decode('ascii'))
    except:
        pass
    
    #Selection is Text 
    try:
        data = request.form['content']
    except:
        pass
    
    #getting filename
    if data !='':
        with open(path + filename, 'w') as fil:
                fil.write(data.encode('ascii', 'ignore').decode('ascii'))
    
    return (filename,permissions_requested, data)

def show_chart(df=df, 
            catskillchart=catskillchart, 
            skillpermchart = skillpermchart,
            devpermchart=devpermchart, 
            trace = trace, 
            requestYear= requestYear, 
            scroll = '', 
            sentences= '', 
            permissions = '', 
            sentence_length= 0,
            typetraceability = '',
            permissions_requested = '',
            permissions_found = '',
            permissions_requested_adapt = '',
            data = data):
    trace = realtrace[trace]
    return render_template('index.html', headings = headings,
            unique_skills = unique_skills,
            unique_devs = unique_devs, column_names = df.columns.values, 
            row_data=list(df.values.tolist()),
            zip=zip, requestYear = requestYear,
            skillchartTotaltrace=skillchartTotaltrace,
            devchartTotaltrace = devchartTotaltrace, catskillchart=catskillchart,
            devpermchart = devpermchart, skillpermchart = skillpermchart, 
            scroll=scroll, trace=trace, sentences= sentences, 
            permissions = permissions, 
            sentence_length=sentence_length,
            typetraceability = typetraceability,
            permissions_requested = permissions_requested,
            permissions_found = set(permissions_found),
            permissions_requested_adapt = set(permissions_requested_adapt),
            data = data)   


@app.route('/', methods=['GET','POST'])
def display():
    if request.method == 'POST':
        if "permission" in request.form or 'url' in request.form:
            filename,permissions_requested, data = upload()
            return get_parameter(filename,permissions_requested, data)

        elif "radiosbar_year" in request.form:
            requestYear= request.form['radiosbar_year'] #get the year from selection
            yearperm = year[requestYear]
            df = allfuctions.getallYearSkillPerm(yearperm)
            return show_chart(df=df, scroll = 'skillswithpermissionbutton')

        elif "radiosbar_year2" in request.form:
            trace = request.form['radiosbar_trace']
            requestYear= request.form['radiosbar_year2'] #get the year from selection
            yearperm = year[requestYear]
            devpermchart = allfuctions.renderChartPermsDev(yearperm, trace)
            skillpermchart = allfuctions.renderChartPermsSkill(yearperm, trace)
            return show_chart(skillpermchart = skillpermchart, devpermchart=devpermchart, 
                                trace = trace, requestYear= requestYear, scroll = 'skillpermchart')

        elif "radioscat_trace" in request.form:
            trace = request.form['radioscat_trace']
            requestYear= request.form['radioscat_year'] #get the year from selection
            yearperm = year[requestYear]
            catskillchart = allfuctions.renderChartByCat(yearperm, trace)
            return show_chart(catskillchart = catskillchart, scroll='tracebycatfig',
				requestYear= requestYear,trace = trace)
        else:
            return redirect(request.url) 


#if __name__ == "__main__":
#    app.run(host='0.0.0.0', port=3860, debug=True)

