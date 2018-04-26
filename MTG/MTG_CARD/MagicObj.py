import numpy as np
import pandas as pd
import json
import random
import pickle
import datetime
import os
__author__ = "dneems"

class cardGenerator(object):
    """
    Single class that contains pointers to all the data and simple methods for coding features of
    the Card and Classes

    """

    def __init__(self, data_location = './Data'):
        self.dataLocation = data_location
        self.rarities = {'C': 'Common',
                            'U': 'Uncommon',
                            'R': 'Rare',
                            'M': 'Mythic Rare',
                            'S': 'Special',
                            'B': 'Basic Land'}
        self.card_types = {'I': 'Instant',
                              'S': 'Sorcery',
                              'A': 'Artifact',
                              'C': 'Creature',
                              'E': 'Enchantment',
                              'L': 'Land',
                              'P': 'Planeswalker'}
        self.layouts = {'N': 'Normal',
                          'Sp': 'Split',
                          'F': 'Flip',
                          'D': 'Double-Face',
                          'T': 'Token',
                          'Pl': 'Plane',
                          'Sh': 'Scheme',
                          'Ph': 'Phenomenon',
                          'L': 'Leveler',
                          'V': 'Vanguard',
                          'M': 'Meld'}

        self.card_index = pd.read_csv(self.dataLocation + '/CardSets/Card_Index.csv')
        self.card_dict = dict(zip(self.card_index.id, zip(self.card_index.name, self.card_index.setname)))
        self.inMem_sets = {}

    def makeCard(self, card_id=None, card_name=None, card_set=None, validate = True):
        if card_name is not None:
           card_id = self.getID(card_name, card_set)
        [card, set_info] = self.getCard(card_id,validate)
        card['rarity'] = self.code_entry(card.get('rarity'), self.rarities)
        card['types'] = self.code_entry(card.get('types'), self.card_types)
        card['id'] = self.validate_id(card.get('id'),validate)
        card['layout'] = self.code_entry(card.get('layout').capitalize(), self.layouts)
        return Card(card, set_info)

    @staticmethod
    def code_entry(value, coding_dict):

        islist = isinstance(value, list)
        if islist:
            coded_list = []
            for V in value:
                if len(V) <= 2:
                    coded_list.append(V)
                else:
                    coded_list.append({v: k for k, v in coding_dict.iteritems()}.get(V))
        else:
            if len(value) <= 2:
                coded_list = value
            else:
                coded_list = {v: k for k, v in coding_dict.iteritems()}.get(value)

        if coded_list is None or len(coded_list) == 0:
            for k, v in coding_dict.iteritems():
                print k + '-' + v
            raise ValueError(value + ' is not a valid code')
        else:
            return coded_list

    def validate_id(self, card_id,validate):
        if validate:
            if card_id not in self.card_dict.keys():
                raise ValueError(card_id + ' is not a valid SHA1 Card Hash')
        return card_id

    def getID(self,card_name, card_set=None):
        if card_set is None:
            card_set = random.choice(
                self.card_index[self.card_index.name.apply(lambda x: x.lower()) == card_name.lower()].setname.tolist())
        card_id = self.card_index[(self.card_index.name.apply(lambda x: x.lower()) == card_name.lower()) & (self.card_index.setname == card_set)].id.values[0]
        return card_id

    def getCard(self, card_id,validate= True):
        card_id = self.validate_id(card_id,validate)
        [cardname, set_codename] = self.card_dict[card_id]
        if self.inMem_sets.get(set_codename) is None:
            set_json = self.dataLocation + '/CardSets/' + set_codename + '/' + set_codename + '_CardInfo.json'
            with open(set_json, 'r') as filename:
                data = json.load(filename)

            set_info_json = self.dataLocation + '/CardSets/' + set_codename + '/' + set_codename + '_SetInfo.json'
            with open(set_info_json, 'r') as filename:
                set_info = json.load(filename)
            self.inMem_sets[set_codename] = [set_info,data]
        else:
            [set_info, data] = self.inMem_sets[set_codename]

        card = [x for x in data if x['name'] == cardname][0]
        return [card, set_info]

class setGenerator(cardGenerator):
    """
    Single class that contains pointers to all the data and simple methods for coding features of
    the Set Classes

    """

    def __init__(self, data_location = './Data'):
        self.dataLocation = data_location
        self.card_sets = pickle.load(open(self.dataLocation + "/codename_xwalk.pkl", "rb"))
        self.set_codes = self.card_sets.keys()
        self.set_card_lists = dict(cardGenerator(data_location).card_index.groupby('setname')['id'].apply(list))

    def getName(self,code_name):
        if code_name.upper() not in self.set_codes:
            raise ValueError(code_name + ' is not a valid Set Code')
        return self.card_sets[code_name.upper()]

    def getCode(self,set_name):
        if set_name.upper() not in [x.upper() for x in self.card_sets.values()]:
            raise ValueError(set_name + ' is not a valid Set Code')
        return {v.upper(): k for k, v in self.card_sets.iteritems()}.get(set_name.upper())


    def getSetJSON(self, set_code):
        set_info_json = './Data' + '/CardSets/' + set_code.upper() + '/' + set_code.upper() + '_SetInfo.json'
        with open(set_info_json, 'r') as filename:
            set_info = json.load(filename)
        return set_info

    def makeSet(self, set_code):
        if set_code.upper() in [x.upper() for x in self.card_sets.keys()]:
            set_JSON = self.getSetJSON(set_code)
        else:
            set_code = setGenerator().getCode(set_code)
            set_JSON = self.getSetJSON(set_code)

        card_ids = []
        with open(self.dataLocation + '/CardSets/' + set_code + '/' + set_code + '_CardInfo.json', 'r') as filename:
            card_ids = [x.get('id') for x in json.load(filename)]

        return Card_Set(set_JSON=set_JSON,card_ids = card_ids)

    def setNameCodes(self):
        code_name_dict = pickle.load(open(self.dataLocation + "/codename_xwalk.pkl", "rb"))
        release_dict = pickle.load(open(self.dataLocation + "/codname_releaseDates.pkl", "rb"))
        return pd.DataFrame(code_name_dict.items(), columns = ['ThreeLetter','FullName']).merge(pd.DataFrame(release_dict.items(), columns = ['ThreeLetter','Release'])).sort_values('Release')

class Card(cardGenerator):
    """Represents a Magic the gathering card.
        Start with simple an universial properties of every card


     Attributes:
       name: String, Name of the Card
       CMC: Int, converted mana cost, sum of all the mana costs on the card
       rarity: Char, C(common), U(uncommon), R(rare), M(Mythic Rare)
       mana_cost: [Int,String], [Total genertic mana,color symbols]
       set: String, card set
       card_type: String, type line
       rules_text: Rules text
       flavor_text: Flavor Text
       art: Array, RGB of art
     """

    def __init__(self, card, set_info):
        self.id = card.get('id')
        self.multiverse_ID = card.get('multiverseid')
        self.rarity = card.get('rarity')
        self.layout = card.get('layout')
        self.name = card.get('name')
        self.mana_cost = card.get('manaCost')
        self.cmc = card.get('cmc', 0)
        self.colorIdentity = card.get('colorIdentity')
        self.types = card.get('types')
        self.supertypes = card.get('supertypes')
        self.subtypes = card.get('subtypes')
        self.card_set = set_info['code']
        self.rules_text = card.get('text')
        self.flavor_text = card.get('flavor')
        self.artist = card.get('artist')
        self.art_url = card.get('multiverseid')
        self.power = card.get('power')
        self.toughness = card.get('toughness')
        self.printings = card.get('printings')
        self.legalities = card.get('legalities')

    # Properties
    @property
    def printings(self):
        return self._printings

    @property
    def legalities(self):
        return self._legalities

    @property
    def power(self):
        if hasattr(self,'_power') is False:
            return None
        else:
            return self._power

    @property
    def toughness(self):
        if hasattr(self,'_toughness') is False:
            return None
        else:
            return self._toughness
    @property
    def rarity(self):
        return self._rarity

    @property
    def types(self):
        return self._types

    @property
    def supertypes(self):
        return self._supertypes

    @property
    def subtypes(self):
        return self._subtypes

    @property
    def id(self):
        print self._id + ' : Unique SHA1 Hash of card'
        return self._id

    @property
    def layout(self):
        return self._layout

    @property
    def name(self):
        return self._name

    @property
    def mana_cost(self):
        return self._name

    @property
    def cmc(self):
        return self._cmc

    @property
    def card_set(self):
        return self._card_set

    @property
    def rules_text(self):
        return self._rules_text

    @property
    def flavor_text(self):
        return self._flavor_text

    @property
    def card_number(self):
        return self._card_number

    @property
    def artist(self):
        return self._artist

    @property
    def art_url(self):
        return self._art_url

    @property
    def colorIdentity(self):
        return self._colorIdentity


    @rarity.setter
    def rarity(self, value):
        self._rarity = value

    @types.setter
    def types(self, values):
        self._types =values

    @subtypes.setter
    def subtypes(self, values):
        self._subtypes = values

    @supertypes.setter
    def supertypes(self, values):
        self._supertypes = values


    @id.setter
    def id(self, value):
        self._id = value

    @layout.setter
    def layout(self, value):
        self._layout = value.capitalize()

    @name.setter
    def name(self, value):
        self._name = value.title()

    @mana_cost.setter
    def mana_cost(self, value):
        if value is None:
            self._mana_cost = [None, None]
        else:
            self._mana_cost = [value[:value.find('}')] + '}', value[value.find('}') + 1:]]

    @cmc.setter
    def cmc(self, value):
        self._cmc = value

    @card_set.setter
    def card_set(self, value):
        self._card_set = value.title()

    @colorIdentity.setter
    def colorIdentity(self, value):
        self._colorIdentity = value

    @rules_text.setter
    def rules_text(self, value):
        if value is None:
            self._rules_text = ''
        else:
            self._rules_text = value.title()

    @flavor_text.setter
    def flavor_text(self, value):
        if value is not None:
            self._flavor_text = value.title()

    @card_number.setter
    def card_number(self, value):
        self._card_number = int(value)

    @artist.setter
    def artist(self, value):
        self._artist = value

    @art_url.setter
    def art_url(self, value):
        self._art_url  = 'http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid=%s&type=card' % value

    @power.setter
    def power(self, value):
        if value is not None:
            if value == '*':
                value = -10
            self._power = int(value)

    @toughness.setter
    def toughness(self, value):
        if value is not None:
            if value == '*':
                value = -10
            self._toughness = int(value)

    @printings.setter
    def printings(self, value):
            self._printings = value

    @legalities.setter
    def legalities(self, values):
        legal_dict= {}
        for value in values:
            if legal_dict.get(value['legality']) is None:
                legal_dict[value['legality']] = [value['format']]
            else:
                legal_dict[value['legality']].append(value['format'])
        self._legalities = legal_dict

class Card_Set(setGenerator):
    """
    Contains all the metadata around the card set and what cards are in the set
    """
    def __init__(self, set_JSON,card_ids):
            self.set_code = set_JSON.get('code')
            self.set_name = set_JSON.get('name')
            self.mkm_name = set_JSON.get("mkm_name")
            self.border = set_JSON.get("border")
            self.translations = set_JSON.get("translations")
            self.mkm_id = set_JSON.get("mkm_id")
            self.releaseDate = set_JSON.get("releaseDate")
            self.booster_template = set_JSON.get("booster")
            self.set_type = set_JSON.get("type")
            self.set_code = set_JSON.get("block")
            self.magicCardsInfoCode = set_JSON.get("magicCardsInfoCode")
            self.cards = card_ids




    @property
    def set_code(self):
        return self._set_code

    @set_code.setter
    def set_code(self, value):
        self._set_code = value

    @property
    def set_name(self):
        return self._set_name

    @set_name.setter
    def set_name(self, value):
        self._set_name = value

    @property
    def mkm_name(self):
        return self._mkm_name

    @mkm_name.setter
    def mkm_name(self, value):
        self._mkm_name = value

    @property
    def border(self):
        return self._border

    @border.setter
    def border(self, value):
        self._border = value

    @property
    def translations(self):
        return self._translations

    @translations.setter
    def translations(self, value):
        self._translations = value

    @property
    def mkm_id(self):
        return self._mkm_id

    @mkm_id.setter
    def mkm_id(self, value):
        self._mkm_id = value

    @property
    def releaseDate(self):
        return self._releaseDate

    @releaseDate.setter
    def releaseDate(self, value):
        self._releaseDate = datetime.datetime.strptime(value, "%Y-%m-%d")

    @property
    def booster_template(self):
        return self._booster_template

    @booster_template.setter
    def booster_template(self, value):
        self._booster_template = value

    @property
    def set_type(self):
        return self._set_type

    @set_type.setter
    def set_type(self, value):
        self._set_type = value

    @property
    def block(self):
        return self._block

    @block.setter
    def block(self, value):
        self._block = value

    @property
    def magicCardsInfoCode(self):
        return self._magicCardsInfoCode

    @magicCardsInfoCode.setter
    def magicCardsInfoCode(self, value):
        self._magicCardsInfoCode = value

    @property
    def cards(self):
        return self._cards

    @cards.setter
    def cards(self, values):
        card_objs = []
        CG = cardGenerator()
        for value in values:
            card_objs.append(CG.makeCard(value,validate= False))
        self._cards = card_objs


