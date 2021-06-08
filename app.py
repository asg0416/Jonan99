from flask import Flask, render_template, jsonify, request, url_for, redirect
from datetime import datetime, timedelta
import requests
import jwt
import hashlib
from pymongo import MongoClient

app = Flask(__name__)

from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.dbjonan99

@app.route('/')
def home(SECRET_KEY=None):
    # token_receive = request.cookies.get('mytoken')
    # try:
    #     payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    #
    #     return render_template('index.html')
    # except jwt.ExpiredSignatureError:
    #     return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    # except jwt.exceptions.DecodeError:
    #     return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))
    return render_template('index.html')




@app.route('/post_home')
def post_home():
    water = requests.get('http://openapi.seoul.go.kr:8088/546c635a6e61736733394979736142/json/WPOSInformationTime/1/5/')
    water_response = water.json()
    water_temp = water_response['WPOSInformationTime']['row'][0]['W_TEMP']

    weather = requests.get(
        'http://api.openweathermap.org/data/2.5/weather?lat=37.56826&lon=126.977829&APPID=8bab5afa1c8be369722bbca48120e0bc')
    weather_response = weather.json()
    weather_temp = weather_response['main']['temp'] - 273.15

    return render_template('post_home.html', water_temp=water_temp, weather_temp=weather_temp)


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


@app.route('/sign_in', methods=['POST'])
def sign_in(SECRET_KEY=None):
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:  #result 찾음
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    # result 못찾음
    else:
        return jsonify({'result': 'fail', 'msg': '가입하지 않은 아이디이거나, 잘못된 비밀번호입니다.'})



@app.route('/sign_up')
def sign_up():
   return render_template('sign_up.html')


@app.route('/content')
def content():
   return render_template('content.html')


# logout api 필요
@app.route('/api/logout', methods=['POST'])
def logout():
    id_receive = request.form['id_give']
    # db.mystar.delete_one({'name': name_receive})

    return jsonify({'msg': '로그아웃 되었습니다.'})


# post 삭제 api 필요
@app.route('/api/delete', methods=['POST'])
def delete_star():
    name_receive = request.form['name_give']
    # db.mystar.delete_one({'name': name_receive})

    return jsonify({'msg': '삭제완료'})

@app.route('/api/content', methods=['GET'])
def show_post():
    contents = list(db.jonan.find({}, {'_id': False}))
    return jsonify({'all_content': contents})

@app.route('/api/content', methods=['POST'])
def post_content():
    title_receive = request.form['title_give']
    comment_receive = request.form['comment_give']
    nickname_receive = request.form['nickname_give']

    doc = {
        'title': title_receive,
        'comment': comment_receive,
        'nickname': nickname_receive
    }

    db.jonan.insert_one(doc)

    return jsonify({'msg': '글 작성 완료'})

@app.route('/api/content', methods=['GET'])
def show_content():
    contents = list(db.diary.find({}, {'_id': False}))
    return jsonify({'all_content': contents})


app.run('0.0.0.0',port=5000,debug=True)