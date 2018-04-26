from flask import Flask, render_template, url_for
import sys
import requests
import time
sys.path.append('../MTG')
import MTG_CARD.MagicObj as MO
app = Flask(__name__)



@app.route('/')
def hello_world():
    CG = MO.cardGenerator(data_location='../MTG/Data')
    card = CG.makeCard(card_name='Giant Growth')
    img_data = requests.get(card.art_url).content
    with open('static/img/card_image.jpg', 'wb') as handler:
        handler.write(img_data)
    return render_template('example.html',
                           card_name=card.name,
                           card_set=card.card_set,
                           card_id=card.id,
                           dummy_var=int(time.time()))
@app.route('/SetList')
def ListSets():
    SG = MO.setGenerator(data_location='../MTG/Data')
    set_code_df = SG.setNameCodes()
    dict_list = []
    for row in set_code_df.sort_values('Release', ascending= False).iterrows():
        temp_dict = {}
        temp_dict['ThreeLetter'] = row[1].ThreeLetter
        temp_dict['FullName'] = row[1].FullName
        dict_list.append(temp_dict)

    return render_template('SetList.html',
                           setCode_Pairs = dict_list)


if __name__ == '__main__':
    app.run(debug = True)
