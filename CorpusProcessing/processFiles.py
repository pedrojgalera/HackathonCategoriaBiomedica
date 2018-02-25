import csv
import os
from pyquery import PyQuery as pq
import inspect
import json
#import ipdb

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

defaultPath = currentdir + "/SciELO_corpus/"
#print(defaultPath)
defaultPathDublin = defaultPath + "dublin_core/"
#print(defaultPathDublin)
defaultPathFullTexts = defaultPath + "full_texts/"
#print(defaultPathFullTexts)
defaultPathFullTxt = defaultPathFullTexts + "clean_raw_text/"
#print(defaultPathFullTxt)
defaultPathFullXml = defaultPathFullTexts + "clean_xml_text/"
#print(defaultPathFullXml)
#

fieldsMap = []
with open("fieldsMap.json") as json_data:
    fieldsMap = json.load(json_data)
    #print(fieldsMap)

selectedFields = []
with open("selectedFields.json") as json_data:
    selectedFields = json.load(json_data)
    print(selectedFields)

def get_paper_set (id):
    return id[1:10]

def list_files(path,rec, f):
    filesList = []
    for file in os.listdir(path):
        filepath = os.path.join(path,file)
        if os.path.isdir(filepath):
            if rec:
                filesList.extend(list_files(path=filepath,rec=rec,f=f))
        else:
            if len(file)>4 and file[-4:] in ['.xml','.txt']:
                filesList.append(f(filepath))
    return filesList

def list_files_full (path,rec=True):
    return list_files(path,rec,f=(lambda x: x))

def list_files_name (path,rec=True):
    return list_files(path,rec,f=(lambda fn: os.path.basename(fn)))

def list_files_id (path,rec=True):
    return list_files(path,rec,f=(lambda fn: os.path.basename(fn).split(".")[0]))

#filesListId = list_files_id(path=defaultPathDublin)

filesListId = []
regenerate = False
if os.path.exists('filesListId.json') and not regenerate:
    print("Loading ids from file...")
    with open("filesListId.json") as json_data:
        filesListId = json.load(json_data)
else:
    print("Generating file with ids...")
    filesListId = list_files_id(path=defaultPathDublin)
    with open('filesListId.json', 'w') as outfile:
        json.dump(filesListId, outfile)

#filesListName = list_files_name(path=defaultPathDublin)
#filesListPath = list_files_full(path=defaultPathDublin)

#
defaultId = "S0211-57352000000400001"

def wrapExt(id=defaultId,ext='.xml'):
    return (id+ext)

defaultFileXml = wrapExt(defaultId,".xml")
defaultFileTxt = wrapExt(defaultId,".txt")


def getFullPath(filename=defaultFileXml,defaultpath=defaultPathDublin):
    return "{}{}/{}".format(
        defaultpath,
        get_paper_set(filename),
        filename
    )

def getDublinPath(id=defaultId):
    return getFullPath(wrapExt(id,'.xml'),defaultPathDublin)

def getFullPathTxt(id=defaultId):
    return getFullPath(wrapExt(id,'.txt'),defaultPathFullTxt)

def getFullPathXml(id=defaultId):
    return getFullPath(wrapExt(id,'.xml'),defaultPathFullXml)

defaultFilePathDublin = getDublinPath()
defaultFilePathFullTxt = getFullPathTxt()
defaultFilePathFullXml = getFullPathXml()
#print(defaultFilePathDublin)
#print(defaultFilePathFullTxt)
#print(defaultFilePathFullXml)

#filesList = list_files(path=defaultPath)
#filesList = list_files(path=defaultPathDublin,rec=True)

def getUrlDublin(id=defaultId):
    return "http://scielo.isciii.es/oai/scielo-oai.php?verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:scielo:" + id

def getUrlFullText(id=defaultId):
    return "http://scielo.isciii.es/scielo.php?script=sci_arttext&pid=" + id

def getUrlFullXml(id="S0213-12852003000100001",lang="es"):
    pref = "http://scielo.isciii.es/scieloOrg/php/articleXML.php?pid={}&lang={}"
    return pref.format(id,lang)

'''
Example for publication with ID 'S0213-12852003000100001':
- Dublin Core metadata: http://scielo.isciii.es/oai/scielo-oai.php?verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:scielo:S0213-12852003000100001
- Publication website: http://scielo.isciii.es/scielo.php?script=sci_arttext&pid=S0213-12852003000100001
- Publication in XML format including full text: http://scielo.isciii.es/scieloOrg/php/articleXML.php?pid=S0213-12852003000100001&lang=es
'''

def file_to_string(filepath=defaultFilePathDublin, rep=True, f=(lambda x: x)):
    with open(filepath, 'r') as myfile:
        raw = myfile.read()
        replaced = raw.replace('\n', '').replace("<dc:","<dc-").replace("</dc:","</dc-").replace("xml:lang","xml-lang").replace("<![CDATA[","").replace("]]>","").replace("P3.S","P3-S").replace("P1.S","P1-S") if rep else raw
    return f(replaced)

#print(file_to_string())

from polyglot.text import Text,Word

def processChunk(chunk,text):
    textChunk = " ".join(text.words[chunk.start:chunk.end])
    return textChunk

def save_papers_parlance(fileList=filesListId,targetpath='papers.pl'):
    with open(targetpath, 'w') as textfile:
        for fileid in fileList:
            filepath = getFullPathTxt(fileid)
            data = file_to_string(filepath)
            textfile.write("{}\n".format(data))

# Saving fulls texts to use in parlance sensor
# save_papers_parlance()
# Save first ten
# save_papers_parlance(filesListId[0:10])

def wrap_field(key,val):
    return "\n\t{}: <<{}>>".format(fieldsMap.get(key),val)

def wrap_fields(pairs,selectedKeys):
    formatString = "{{"
    formatParams = []
    selectedPairs = filter(lambda pair: pair[0] in selectedKeys,pairs)
    for el in selectedPairs:
        formatString += "{}"
        formatParams.append(wrap_field(*el))
    formatString += "\n}}\n"
    return formatString.format(*formatParams)

#selectedKeys=['newId','title', 'keyword', 'tesauro', 'locs', 'orgs', 'content', 'date']):

# ["content", "locs", "orgs", "set", "id", "keyword"]

def find_some(words, texts):
    found = False
    for word in words:
        for text in texts:
            if text.find(word)!=-1:
                found=True
                break
        if found:
            break
    return found

def save_conceptual_scheme(fileList=filesListId,targetpath='papers.corpus',selectedKeys=selectedFields, ner=False, textLimit=-1):
    with open(targetpath, 'w') as targetfile:
        for fileid in fileList:
            pairs = []
            locs=set()
            orgs=set()
            pers=set()
            pairs.append(("id",fileid))
            metadatafilepath = getDublinPath(fileid)
            fulltextfilepath = getFullPathTxt(fileid)
            fulltextxmlfilepath = getFullPathXml(fileid)
            #paperset = fileid[1:10]
            data = file_to_string(metadatafilepath,f=(lambda d: d.encode("utf-8")))
            dataxml = file_to_string(fulltextxmlfilepath,f=(lambda d: d.encode("utf-8")))
            #print(data)
            data2 = data.lower()
            pq1 = pq(data)
            pq2 = pq(data2)
            #import ipdb; ipdb.set_trace()
            pqxml = pq(dataxml)
            #dataxml2 = dataxml.lower()
            #pqxml2 = pq(dataxml2)
            firstpar = pqxml("#P1-S1").text()
            thirdpar = pqxml("#P3-S1").text()
            #print(firstpar)
            '''
            if firstpar.startswith("EDITORIAL") or firstpar.startswith("NECROLÓGICA") or thirdpar is None or thirdpar == '':
                content = pqxml("#P1-S1").text()+"\n"+pqxml("#P1-S2").text()
            else:
                content = pqxml("#P3-S1").text()+"\n"+pqxml("#P3-S2").text()
            #pairs.append(("content",content[0:200]+"... (para más información, consulte la url proporcionada)"))
            pairs.append(("content",content))
            '''
            titleElems = pq1('dc-title')
            title=''
            for i in titleElems:
                title = i.text
                break
            if title=='':
                title = firstpar.split(" ")[0]#"EDITORIAL"
            if len(title)>0:
                pairs.append(("title",title))
            descriptionElems = pq1('dc-description')
            description=''
            for i in descriptionElems:
                description = i.text
                break
            if len(description)>0:
                pairs.append(("description",description))

            urlmetadata = getUrlDublin(fileid)
            urltext = getUrlFullText(fileid)
            urltextxml = getUrlFullXml(fileid)
            date = pq1("dc-date").text()
            if len(date)>2:
                pairs.append(("date",date))
            setspec = pq2("setspec").text()
            pairs.append(("set",setspec))
            subjectElems = pq1('dc-subject')

            subjectText=''
            for i in subjectElems:
                subjectText += (i.text+",,,")
            subjects = subjectText[0:-3].split(',,,')
            subjectsCad = str(subjects)[1:-1]
            if len(subjectsCad)>2:
                #print(len(subjectsCad))
                #print(subjectsCad)
                pairs.append(("keyword",subjectsCad))

            creatorElems = pq1('dc-creator')
            creators = creatorElems.text().split(' ')
            if len(creators)>0:
                pairs.append(("creators",str(creators)[1:-1]))

            publisher = pq1('dc-publisher').text()
            pairs.append(("publisher",publisher))

            source = pq1('dc-source').text()
            pairs.append(("source",source))

            #import ipdb; ipdb.set_trace()
            fulltext=file_to_string(fulltextfilepath,rep=False)

            if textLimit!=-1:
                s = len(fulltext)
                lim = min(s,textLimit)
                pairs.append(("content",fulltext[0:lim]+"... (para más información, consulte la url proporcionada)"))
            else:
                pairs.append(("content",fulltext))
            if ner:
                #print(fulltext)

                text = Text(fulltext, hint_language_code='es')
                try:
                    if text is not None:
                        if isinstance(text.entities, list):
                            for ent in text.entities:
                                if ent.tag == 'I-LOC':
                                        locs.add(processChunk(ent,text))
                                if ent.tag == 'I-ORG':
                                        orgs.add(processChunk(ent,text))
                                if ent.tag == 'I-PER':
                                        pers.add(processChunk(ent,text))
                    pairs.append(("locs",str(locs)[1:-1]))
                    pairs.append(("orgs",str(orgs)[1:-1]))
                    pairs.append(("pers",str(pers)[1:-1]))
                except ValueError:
                    error = False
                    pass
            pairs.append(("urlmetadata",urlmetadata))
            pairs.append(("urltext",urltext))
            pairs.append(("urltextxml",urltextxml))
            if find_some(["odont","estomat","dentist"],[title,subjectsCad,source,publisher,fulltext]):
                targetfile.write(wrap_fields(pairs,selectedKeys))

#save_conceptual_scheme(filesListId)
save_conceptual_scheme(filesListId, targetpath='papersCutPart.corpus', textLimit=200)

#print("Files in corpus SciELO: {}".format(str(len(filesList))))

'''
filesNo = 1
filesNumber = min(filesNo,len(filesList))
selectedFiles = filesList[0:filesNumber]
selectedFields = ['newId','title', 'keyword', 'tesauro', 'locs', 'orgs', 'content', 'date']
save_conceptual_scheme(fileList=selectedFiles,targetpath='news.corpus',selectedKeys=selectedFields)
save_news_csv(fileList=selectedFiles,targetpath='news.csv',selectedKeys=selectedFields)
save_news_parlance(fileList=selectedFiles,targetpath='news.pl')
'''
