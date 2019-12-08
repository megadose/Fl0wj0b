# coding: utf-8
from bs4 import BeautifulSoup
import csv,argparse,json,requests,tabulate
from lxml import html
parser = argparse.ArgumentParser()
parser.add_argument('-q', '--qui',help = '"Nom prenom"', required = True)
parser.add_argument('-o', '--ou',required = True)
parser.add_argument('-e', '--export',help = "exporter les resultats en .csv")

args = parser.parse_args()


def add_if_not_none(the_dict, key, item):
    if item is not None:
        the_dict[key] = item.string.strip()

def doublon(dictdata,dictdata2):
    #compare les résultats avec  2 dictionnaire
    dict_datafinal = []
    for i in dictdata2:
        dict_datafinal.append(dict(Nom=i["Nom"], Adresse=i['Adresse'],CodePostal=i['CodePostal'], Ville=i['Ville'], Telephone=i['Telephone']))
    if dictdata is not None:
        for i in dictdata:
            if i['Telephone'] != "":
                tel = i['Telephone']
                check = tel in str(dict_datafinal) in str(dict_datafinal)
            else:
                dict_datafinal.append(dict(Nom=i["Nom"], Adresse=i['Adresse'],CodePostal=i['CodePostal'], Ville=i['Ville'], Telephone=i['Telephone']))
            if(check==False):
                dict_datafinal.append(dict(Nom=i["Nom"], Adresse=i['Adresse'],CodePostal=i['CodePostal'], Ville=i['Ville'], Telephone=i['Telephone']))
    else :
        pass

    return(dict_datafinal)

def export_csv(list,csv_file,csv_columns):
    #Export en csv
    try:
        with open(csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for data in dict_data_final:
                writer.writerow(data)
    except IOError:
        print("I/O error")

def annuaire118712(qui, ou):
    # recherche sur l'annuaire d'Orange
    res = []
    req = requests.get('https://annuaire.118712.fr/', params={"s": qui+' '+ou})
    h = BeautifulSoup(req.text, 'lxml')
    for p in h.find_all(itemtype="http://schema.org/Person"):
        nom = p.find(itemprop="name").a.string.strip()
        cp = p.find(itemprop="postalCode").string.strip()
        ville = p.find(itemprop="addressLocality").string.strip()
        tel = p.find(itemprop="telephone").string.strip()
        result = dict(Nom=nom, CodePostal=cp, Ville=ville, Telephone=tel.replace(" ",""))
        adresse = p.find(itemprop="streetAddress")
        if adresse is not None:
            result['Adresse'] = adresse.string.strip()
        else:
            result['Adresse'] = ''

        lat = p.find(itemprop="latitude")
        if lat is not None:
            result['lat'] = lat.string.strip()
        lon = p.find(itemprop="longitude")
        if lon is not None:
            result['lon'] = lon.string.strip()
        categories = p.find(class_="categories")
        if categories is not None:
            result['categories'] = categories.string.strip()
        res.append(result)

    for p in h.find_all(itemtype="http://schema.org/LocalBusiness"):
        nom = p.find(itemprop="name").a.string.strip()
        cp = p.find(itemprop="postalCode").string.strip()
        ville = p.find(itemprop="addressLocality").string.strip()
        tel = p.find(itemprop="telephone").string.strip()
        result = dict(Nom=nom, CodePostal=cp, Ville=ville, Telephone=tel.replace(" ",""))
        adresse = p.find(itemprop="streetAddress")
        if adresse is not None:
            result['Adresse'] = adresse.string.strip()
        else:
            result['Adresse'] = ''

        lat = p.find(itemprop="latitude")
        if lat is not None:
            result['lat'] = lat.string.strip()
        lon = p.find(itemprop="longitude")
        if lon is not None:
            result['lon'] = lon.string.strip()
        categories = p.find(class_="categories")
        if categories is not None:
            result['categories'] = categories.string.strip()
        res.append(result)

    return(res)

def page_blanche(qui, ou):
    # recherche sur page blanche
    res = []
    headers = {
    'User-Agent': 'Mozilla/5.0 (fens NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3831.0 Safari/537.36 Edg/77.0.200.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://www.pagesjaunes.fr',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Referer': 'https://www.pagesjaunes.fr/pagesblanches',
    'Upgrade-Insecure-Requests': '1',
    'TE': 'Trailers',
    }

    req = requests.post('https://www.pagesjaunes.fr/pagesblanches/recherche',
                       params={'quoiqui': qui,'ou':ou,'proximite':"0"},headers=headers)
    tree = html.fromstring(req.text)
    articles = tree.xpath("//article[contains(@id, 'bi-bloc-')]")
    for article in articles:
        name = article.xpath(".//a[@class='denomination-links pj-lb pj-link']/text()")
        phone = article.xpath(".//strong[@class='num']/@title")
        adresse_complet = article.xpath(".//a[@class='adresse pj-lb pj-link']/text()")
        if(len(adresse_complet)!=0):
            cp = adresse_complet[0].split(",")[1].split("\n")[0]
            ville = adresse_complet[0].split(",")[1].split("\n")[1]
            adresse = adresse_complet[0].split(",")[0]
        else:
            cp = ""
            ville = ""
            adresse = "Cet abonné ne désire pas publier son adresse."
        result = dict(Nom=name[0].replace("\n",""))
        result['Adresse'] = adresse.replace("\n","")
        result['CodePostal'] = cp
        result['Ville'] = ville
        result['Telephone'] = ' / '.join(phone).replace(" ","")
        res.append(result)
    return(res)

def annu118000(qui, ou):
    # recherche sur l'annuaire 118000
    res = []
    # recherche particuliers
    req = requests.get('https://www.118000.fr/search',
                       params={"who": qui, "label": ou})
    h = BeautifulSoup(req.text, 'lxml')
    for p in h.find_all(class_="card"):
        b = p.find(class_="iconheart")
        if b['data-info'] is not None:
            j = json.loads(b['data-info'])
            if j['tel'] != j['mainLine']:
                tel = str(j['tel'])+"/"+str(j['mainLine'])
            else:
                tel = j['mainLine']
            res.append(dict(Nom=p.h2.a.string, Adresse=j['address'],
                            CodePostal=j['cp'], Ville=j['city'], Telephone=tel))

    return(res)

dict_data = annuaire118712(args.qui, args.ou)
#print(dict_data)
dict_data2 = page_blanche(args.qui, args.ou)
#print(dict_data2)
dict_data3 = annu118000(args.qui, args.ou)
#print(dict_data3)
dict_data_final = doublon(dict_data2,dict_data)
dict_data_final = doublon(dict_data3,dict_data_final)
#print(dict_data_final)
if(len(dict_data_final)>=1):
    header = dict_data_final[0].keys()
    rows =  [x.values() for x in dict_data_final]

    print(tabulate.tabulate(rows, header))

    if(args.export!=None):
        csv_columns = ['Nom','Adresse','CodePostal','Ville','Telephone']
        export_csv(dict_data_final,args.export,csv_columns)
