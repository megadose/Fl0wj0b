#!/usr/bin/python3
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
        result = dict(Nom=nom, cp=cp, ville=ville, tel=tel)
        adresse = p.find(itemprop="streetAddress")
        if adresse is not None:
            result['adresse'] = adresse.string.strip()
        else:
            result['adresse'] = ''
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
        result = dict(Nom=nom)
        add_if_not_none(result, 'Adresse', p.find(itemprop="streetAddress"))
        add_if_not_none(result, 'CodePostal', p.find(itemprop="postalCode"))
        add_if_not_none(result, 'Ville', p.find(itemprop="addressLocality"))
        add_if_not_none(result, 'Telephone', p.find(itemprop="telephone"))
        if 'tel' not in result:
            tel = p.find(class_="hidden-phone")
            if tel is not None:
                result['tel'] = tel['data-wording']
        add_if_not_none(result, 'categories', p.find(class_="categories"))
        res.append(result)
    return(res)


def page_blanche(qui, ou):
    # recherche sur page blanche
    res = []
    headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3831.0 Safari/537.36 Edg/77.0.200.1'    }
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
        result['Ville'] = ville
        result['CodePostal'] = cp
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
            res.append(dict(Nom=p.h2.a.string, Adresse=j['address'],
                            CodePostal=j['cp'], Ville=j['city'], Telephone=j['tel']))
    return(res)



def doublon(dictdata,dictdata2):
    #compare les résultats avec  2 dictionnaire
    dict_datafinal = []
    dict_datafinal +=dictdata2
    for i in dictdata:
        try:
            tel = i['Telephone'].replace(" ","")
            check = tel in str(dict_datafinal) in str(dict_datafinal)
            if(check==False):
                dict_datafinal.append(i)
        except:
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


dict_data = annuaire118712(args.qui, args.ou)
dict_data2 = page_blanche(args.qui, args.ou)
dict_data3 = annu118000(args.qui, args.ou)
dict_data_final = doublon(dict_data,dict_data2)
dict_data_final = doublon(dict_data3,dict_data_final)

header = dict_data_final[0].keys()
rows =  [x.values() for x in dict_data_final]

print(tabulate.tabulate(rows, header))

if(args.export!=None):
    csv_columns = ['Nom','CodePostal','Ville','Telephone','Adresse']
    export_csv(dict_data_final,args.export,csv_columns)
