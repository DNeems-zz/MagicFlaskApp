import urllib, json, pickle, os
import pandas as pd
from bs4 import BeautifulSoup
import urllib2
from datetime import datetime
__author__ = "dneems"
deafault_card_set_url = 'https://mtgjson.com/json/'
default_dataLocation = './Data'
def update_SetList(url=deafault_card_set_url, data_location=default_dataLocation):
    response = urllib.urlopen(url + 'SetCodes.json')
    setlist = json.loads(response.read())
    code_name_dict = {}
    mtg_json_code = {}
    set_release_dates = {}
    for indvset in setlist:
        print indvset
        response = urllib.urlopen(url + indvset + '-x.json')
        data = json.loads(response.read())
        code_name_dict[data['code'].upper()] = data['name'].title()
        mtg_json_code[data['code'].upper()] = indvset
        set_release_dates[data['code'].upper()] = datetime.strptime(data['releaseDate'], '%Y-%m-%d').date()
    pickle.dump(code_name_dict, open(data_location + "/codename_xwalk.pkl", "wb"))
    pickle.dump(mtg_json_code, open(data_location + "/codeurl_xwalk.pkl", "wb"))
    pickle.dump(set_release_dates, open(data_location + "/codname_releaseDates.pkl", "wb"))


def refresh_set(setname='all', url=deafault_card_set_url, data_location=default_dataLocation + '/CardSets'):
    code_name_dict = pickle.load(open(default_dataLocation + "/codename_xwalk.pkl", "rb"))
    mtg_json_dict = pickle.load(open(default_dataLocation + "/codeurl_xwalk.pkl", "rb"))

    if setname == 'all':
        update_SetList()
        for codename in code_name_dict.keys():
            response = urllib.urlopen(url + mtg_json_dict[codename] + '-x.json')
            data = json.loads(response.read())
            cards = data.pop('cards')
            directory = data_location + '/' + codename.upper() + '/'
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(directory + codename.upper() + '_SetInfo.json', 'w') as outfile:
                json.dump(data, outfile)
            with open(directory + codename.upper() + '_CardInfo.json', 'w') as outfile:
                json.dump(cards, outfile)
    else:
            _, codename = validate_set(setname)
            response = urllib.urlopen(url + mtg_json_dict[codename] + '-x.json')
            data = json.loads(response.read())
            cards = data.pop('cards')
            directory = data_location + '/' + codename.upper() + '/'
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(directory + codename.upper() + '_SetInfo.json', 'w') as outfile:
                json.dump(data, outfile)
            with open(directory + codename.upper() + '_CardInfo.json', 'w') as outfile:
                json.dump(cards, outfile)


def index_set(setname = 'all',data_location=default_dataLocation + '/CardSets'):
    if setname == 'all':
        setnames = os.listdir(data_location)
        df_card = pd.DataFrame(columns=['name', 'id', 'setname'])
        for setname in setnames:
            if setname.upper() != 'CARD_INDEX.CSV':
                _, codename = validate_set(setname)
                with open(data_location + '/' + codename.upper() + '/' + codename.upper() + '_CardInfo.json', 'r') as cardfile:
                    cards_json = json.load(cardfile)
                    card_index = []
                    for card in cards_json:
                        card_index.append([card['name'], card['id'],codename])
                partial_df_card = pd.DataFrame(card_index)
                partial_df_card.columns = ['name', 'id', 'setname']
                df_card = df_card.append(partial_df_card)

    else:
        _, codename = validate_set(setname)
        with open(data_location + '/' + codename.upper() + '/' + codename.upper() + '_CardInfo.json', 'r') as cardfile:
            cards_json = json.load(cardfile)
            card_index = []
            for card in cards_json:
                card_index.append([card['name'], card['id'], codename])
        df_card = pd.DataFrame(card_index)
        df_card.columns = ['name', 'id', 'setname']
    df_card.to_csv(data_location+'/Card_Index.csv', header=True, index=False, encoding='utf-8')
    return df_card


def validate_set(input_set, data_location=default_dataLocation + '/CardSets'):
    code_name_dict = pickle.load(open(default_dataLocation + "/codename_xwalk.pkl", "rb"))

    codename = {v: k for k, v in code_name_dict.iteritems()}.get(input_set.title())
    setname = code_name_dict.get(input_set.upper())
    if codename is None:
        codename = input_set

    if setname is None:
        setname = input_set

    print setname
    if codename is None:
        raise ValueError(setname + ' is not a valid Set Name')
    elif setname is None:
        raise ValueError(codename + ' is not a valid Set Code')
    elif not os.path.isdir(data_location + '/' + codename.upper()):
        os.makedirs(data_location + '/' + codename.upper() + '/')
    else:
        return setname, codename


def extractKeywords(table_url='http://mtg.gamepedia.com/Flying',keyword_groups = ['Keyword abilities','Keyword actions','Ability words']):
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = urllib2.Request(table_url,headers=hdr)
    page = urllib2.urlopen(req)
    soup = BeautifulSoup(page)
    table = soup.find("table", { "class" : "nowraplinks" })
    nested_rows = table.find_all('tr',recursive = False)
    special_words = {}
    for row in nested_rows:
        if row.a is not None:
            if row.a.text in keyword_groups:
                special_words[row.a.text] = [x.text for x in row.findAll('li')]
    return special_words

