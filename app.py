from urllib import response
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pandas as pd
from scipy import sparse
import json


app = Flask(__name__)


@app.route('/api', methods=['POST'])
def function():

    if(request.method == 'POST'):
        request_data = request.data
        request_data = json.loads(request_data)
        jtopy = json.dumps(request_data)
        dict_json = json.loads(jtopy)
        print(dict_json["idUser"])

        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)

        db = firestore.client()

        test = []

        docsUsersRating = db.collection('ratings').where(
            'idUser', '==', dict_json['idUser']).get()

        for doc in docsUsersRating:
            dict_User = doc.to_dict()
            test.append((dict_User['idMenu'], dict_User['rating']))

        docsAllRating = db.collection('ratings').get()

        docsMenu = db.collection('menu-rating').get()

        idMenu = []
        namaMenu = []
        kategori = []
        idMenuRating = []
        idUser = []
        rating = []
        timeStamp = []

        for doc in docsAllRating:
            dict_Rating = doc.to_dict()
            idMenuRating.append(dict_Rating['idMenu'])
            idUser.append(dict_Rating['idUser'])
            rating.append(dict_Rating['rating'])
            timeStamp.append(dict_Rating['timestamp'])

        for doc in docsMenu:
            dict_Menu = doc.to_dict()
            idMenu.append(dict_Menu['idMenu'])
            namaMenu.append(dict_Menu['namaMenu'])
            kategori.append(dict_Menu['kategori'])

        d_Rating = ({'idUser': idUser, 'idMenu': idMenuRating,
                    'rating': rating, 'timeStamp': timeStamp})

        d_Menu = ({'idMenu': idMenu, 'namaMenu': namaMenu,
                   'kategori': kategori})

        df_rating = pd.DataFrame(d_Rating)

        df_menu = pd.DataFrame(d_Menu)

        print(test)

        ratings = pd.merge(df_menu, df_rating).drop(
            ['kategori', 'timeStamp'], axis=1)
        # print(ratings.shape)
        ratings.head()

        # with pd.option_context('display.max_rows', None,
        #                        'display.max_columns', None,
        #                        'display.precision', 3,
        #                        ):
        #     print(ratings)

        userRatings = ratings.pivot_table(index=['idUser'], columns=[
            'idMenu'], values='rating')
        userRatings.head()
        print("Before: ", userRatings.shape)
        userRatings = userRatings.fillna(0, axis=1)
        userRatings.fillna(0, inplace=True)
        print("After: ", userRatings.shape)
        # with pd.option_context('display.max_rows', None,
        #                        'display.max_columns', None,
        #                        'display.precision', 3,
        #                        ):
        #     print('=============================')
        #     print(userRatings)

        # dataUji = [('Kentang Goreng', 5), ('Tumis Kangkung', 3),
        #            ('Sop', 5), ('Batagor', 1), ('Ayam Penyet', 2)]

        corrMatrix = userRatings.corr(method='pearson')
        corrMatrix.head(100)
        # with pd.option_context('display.max_rows', None,
        #                        'display.max_columns', None,
        #                        'display.precision', 3,
        #                        ):
        #     print('============== Perason Korelasi ===============')
        #     print(corrMatrix)

        def get_similar(menu_name, rating):
            similar_ratings = corrMatrix[menu_name]*(rating-2.5)
            similar_ratings = similar_ratings.sort_values(ascending=False)
            print(type(similar_ratings))
            return similar_ratings

        similar_menu = pd.DataFrame()
        for menu, rating in test:
            similar_menu = similar_menu.append(
                get_similar(menu, rating), ignore_index=True)

        similar_menu.head(10)

        rekom = similar_menu.sum().sort_values(ascending=False).head(20)

        print(rekom)
        rekomendasi = {}
        data = []

        for value in rekom.keys():
            data.append(value)

        rekomendasi['idUser'] = dict_json['idUser']
        rekomendasi["rekomendasi"] = data

        # kirim data rekomendasi ke firebase
        docsRekom = db.collection(
            'recommendations').document(dict_json['idUser'])
        docsRekom.set(rekomendasi)

    return ""


if __name__ == "__main__":
    app.run(host="10.140.139.112", port=8000, debug=True)
