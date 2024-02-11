from flask import Flask, render_template, request, redirect, url_for
from math import radians, sin, cos, sqrt, atan2, ceil
from flask_sqlalchemy import SQLAlchemy
import requests
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap
import os


# Flaskアプリケーションの設定
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)

# データベースのモデルを定義
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), unique=True, nullable=False)
    password = db.Column(db.String(12), nullable=False)
    point = db.Column(db.Integer, default=100)
    bookmarks = db.relationship('Bookmark', backref='user', lazy=True)

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shop_id = db.Column(db.String(30), nullable=False)

# ユーザー情報を取得するための関数
@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(int(user_id))

# 距離を計算する関数
def haversine(lat1, lon1, lat2, lon2):
    # 地球の半径（単位: km）
    R = 6371.0

    # 度数からラジアンに変換
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # ヒュベニの公式
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance

# ホーム画面
@app.route('/', methods=['POST','GET'])
def index():
    if request.method == "POST":
        if "1" in request.form:
            return render_template('out.html')
        elif "2" in request.form:
            return render_template('inout.html')
        elif "3" in request.form:
            print("未対応")
            return redirect("/")
        elif "4" in request.form:
            return render_template('test.html')
    else:
        return render_template('index.html')

# テスト画面
@app.route('/test', methods=['POST','GET'])
def test():
    print("----------------------------------------------")
    if request.method == "POST":
        if "1" in request.form:
            # "現在地から" ボタンが押された場合の処理
            return render_template('out.html')
        elif "2" in request.form:
            # "住所から" ボタンが押された場合の処理
            return render_template('inout.html')
        elif "3" in request.form:
            # "キーワードから" ボタンが押された場合の処理
            print("未対応")
            return redirect("/")
    else:
        return render_template('test.html')
    
# 新規登録画面
@app.route('/signup', methods=['POST','GET'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        user=User(username=username,password=generate_password_hash(password, method='pbkdf2:sha256', salt_length=10000),point=100000)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    else:
        return render_template("signup.html")

# ログイン画面
@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username):
            user=User.query.filter_by(username=username).first()
        else:
            redirect("login.thml")
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect('/')
    else:
        return render_template("login.html")

# ログアウト画面
@app.route('/logout')
@login_required #アクセス制御
def logout():
    logout_user()
    return redirect('/login')

# #検索方法を選択
# @app.route('/chose', methods=['POST'])
# def chose():
#     if request.method == "POST":
#         if request.form.get("out"):
#             return render_template("out.html")
#         if request.form.get("inout"):
#             return render_template("inout.html")
#     else:
#         return redirect("/")

# 住所から検索
@app.route('/chose/inout', methods=['POST','GET'])
def choseinout():
    if request.method == "POST":
        address = request.form.get('address')
        if address:
            api_endpoint = 'https://nominatim.openstreetmap.org/search'
            params = {
                'format': 'json',
                'q': address
            }
            response = requests.get(api_endpoint, params=params)
            data = response.json()

            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
        if request.form.get('enter'):
                distance=request.form.get('distance')
        else:
            for key in request.form.items():
                    distance=key
        print("------------------------------")
        print("検索設定")
        return redirect(url_for("search", page=1, lat=lat, lon=lon, distance=distance))
    else:
        return render_template("inout.html")

# 現在地から検索
@app.route('/chose/out', methods=['POST', 'GET'])
def result():
    if request.method == "POST":
        error = request.form.get("error_message")
        if error:
            return redirect(url_for("showerror", text=error))
        else:
            lat = request.form.get("latitude")
            lon = request.form.get("longitude")

        if request.form.get('enter'):
            distance = request.form.get('distance')
        else:
            for key in request.form.items():
                distance=key
        print("------------------------------")
        print("検索設定")
        return redirect(url_for("search", page=1, lat=lat, lon=lon, distance=distance))

    else:
        return render_template("out.html")

# 検索結果一覧
@app.route('/search/<int:page>', methods=['POST', 'GET'])
def search(page):
    print("------------------------------")
    print("検索開始")
    # ホットペッパーAPIのエンドポイントとAPIキーを設定
    API_ENDPOINT = "https://webservice.recruit.co.jp/hotpepper/gourmet/v1/"
    API_KEY = "982df35e8e7d6344" 
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    distance = request.args.get('distance')
    
    print("Page:", page)
    print("Lat:", lat)
    print("Lon:", lon)
    print("Distance:", distance)

    # latとlonが指定されていない場合はエラーメッセージを表示
    if not (lat and lon):
        return "Error: latとlonは両方指定してください."

    # ページングのための設定
    items_per_page = 15  # 1ページあたりのアイテム数
    start_index=(page-1)*items_per_page
    params = {
        'key': API_KEY,
        'lat': lat,
        'lng': lon,
        'range': distance,
        'format': 'json',
        'count': items_per_page,
        'start': start_index+1,
        'order': 4,  
    }

    response = requests.get(API_ENDPOINT, params=params)
    datum = response.json()

    # APIの応答から有効なデータが含まれているか確認
    if 'results' not in datum or 'shop' not in datum['results']:
        return "エラー: 結果が見つかりませんでした。"

    shops = datum['results']['shop']

    # デバッグエリア
    print(datum['results']['results_available'])
    print(datum['results']['results_returned'])
    for i in shops:
        print(i['name'],i['id'])

    user_lat = float(lat)
    user_lon = float(lon)

    # 距離計算
    current_page_shops = []
    for shop in shops:
        shop_lat = float(shop['lat'])
        shop_lon = float(shop['lng'])
        distance_2 = haversine(user_lat, user_lon, shop_lat, shop_lon)
        shop['distance'] = round(distance_2, 2)
        current_page_shops.append(shop)

    # APIの応答から結果の数を取得
    total_items = datum['results']['results_available']
    total_pages = ceil(total_items / items_per_page)

    current_time = datetime.now().time()
    return render_template('result.html', shops=current_page_shops, current_time=current_time, total_pages=total_pages, current_page=page, lat=lat, lon=lon, distance=distance)

# お店の詳細情報
@app.route('/shopinfo/<id>', methods=['POST', 'GET'])
def shopinfo(id):
    print("------------------------------------")
    print("shopinfo")
    # ホットペッパーAPIのエンドポイントとAPIキーを設定
    API_ENDPOINT = "https://webservice.recruit.co.jp/hotpepper/gourmet/v1/"
    API_KEY = "982df35e8e7d6344" 
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    params={
        'key': API_KEY,
        'id':id,
        'format': 'json'
    }

    response = requests.get(API_ENDPOINT, params=params)
    datum = response.json()

    shops = datum['results']['shop']

    # デバッグエリア
    for i in shops:
        print(i['name'],i['id'])

    user_lat = float(lat)
    user_lon = float(lon)

    # 距離計算
    current_page_shops = []
    
    for shop in shops:
        shop_lat = float(shop['lat'])
        shop_lon = float(shop['lng'])
        distance_2 = haversine(user_lat, user_lon, shop_lat, shop_lon)
        shop['distance'] = round(distance_2, 2)
        current_page_shops.append(shop)
    shop={}
    for i in current_page_shops:
        print(i['distance'])
        shop=i



    current_time = datetime.now().time()
    return render_template('shop.html', shop=shop, current_time=current_time)

# ブックマーク機能
@app.route('/bookmark/<id>', methods=['POST', 'GET'])
def bookmark(id):
    if request.method == "POST":
        if not current_user.is_authenticated:
            return redirect('/login')
        else:
            user_id = current_user.id
            bookmark = Bookmark(user_id=user_id, shop_id=id)
            db.session.add(bookmark)
            db.session.commit()
            return redirect(url_for("shopinfo", id=id, lat=lat, lon=lon))
    elif request.method == "GET":
        if not current_user.is_authenticated:
            return redirect('/login')
        else:
            user_id = current_user.id
            bookmark = Bookmark(user_id=user_id, shop_id=id)
            db.session.add(bookmark)
            db.session.commit()
            referer = request.headers.get("Referer")
            if referer.endswith("shop.html"):
                return redirect(url_for("shopinfo", id=id, lat=lat, lon=lon))
            elif referer.endswith("resalt.html"):
                return redirect(url_for("result"))
            else:
                # Add a variable to indicate the source
                source = "unknown"
                return redirect(url_for("shopinfo", id=id, lat=lat, lon=lon, source=source))
    

@app.route('/error/<text>', methods=['POST', 'GET'])
def showerror(text):
    return f"{text}"
