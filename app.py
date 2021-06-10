import requests
from flask import Flask, render_template, jsonify, request, session, redirect, url_for

app = Flask(__name__)

from pymongo import MongoClient

client = MongoClient('localhost', 27017)
# client = MongoClient('mongodb://13.124.117.232', 27017, username="test", password="test")
db = client.JONANTEST

# JWT 토큰을 만들 때 필요한 비밀문자열입니다. 아무거나 입력해도 괜찮습니다.
# 이 문자열은 서버만 알고있기 때문에, 내 서버에서만 토큰을 인코딩(=만들기)/디코딩(=풀기) 할 수 있습니다.
SECRET_KEY = 'SPARTA'

# JWT 패키지를 사용합니다. (설치해야할 패키지 이름: PyJWT)
import jwt

# 토큰에 만료시간을 줘야하기 때문에, datetime 모듈도 사용합니다.
import datetime

# 회원가입 시엔, 비밀번호를 암호화하여 DB에 저장해두는 게 좋습니다.
# 그렇지 않으면, 개발자(=나)가 회원들의 비밀번호를 볼 수 있으니까요.^^;
import hashlib


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/post_home')
def post_home():
    # 로그인 성공시
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})

        # api 이용한 수온, 날씨
        water = requests.get(
            'http://openapi.seoul.go.kr:8088/546c635a6e61736733394979736142/json/WPOSInformationTime/1/5/')
        water_response = water.json()
        water_temp = water_response['WPOSInformationTime']['row'][0]['W_TEMP']

        weather = requests.get(
            'http://api.openweathermap.org/data/2.5/weather?lat=37.56826&lon=126.977829&APPID=8bab5afa1c8be369722bbca48120e0bc')
        weather_response = weather.json()
        weather_temp = weather_response['main']['temp'] - 273.15
        return render_template('post_home.html', nickname=user_info["nick"], water_temp=water_temp,
                               weather_temp=weather_temp, user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


@app.route('/sign_up')
def sign_up():
    return render_template('sign_up.html')


@app.route('/content')
def content():
    return render_template('content.html')


# # logout api 필요
# @app.route('/api/logout', methods=['POST'])
# def logout():
#     id_receive = request.form['id_give']
#     # db.mystar.delete_one({'name': name_receive})
#
#     return jsonify({'msg': '로그아웃 되었습니다.'})


# post 삭제 api 필요
@app.route('/api/delete', methods=['POST'])
def delete_post():
    postid_receive = request.form['postid_give']
    db.posting.remove({'post_id': postid_receive})

    return jsonify({'result': 'success', 'msg': '삭제완료'})


#################################
##  로그인을 위한 API            ##
#################################

# [회원가입 API]
# id, pw, nickname을 받아서, mongoDB에 저장합니다.
# 저장하기 전에, pw를 sha256 방법(=단방향 암호화. 풀어볼 수 없음)으로 암호화해서 저장합니다.
@app.route('/api/sign_up', methods=['POST'])
def api_sign_up():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    nickname_receive = request.form['nickname_give']
    id_count_receive = request.form['id_count']
    result = db.user.find_one({'id': id_receive})

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    if id_count_receive != 'true':
        return jsonify({'result': 'fail', 'msg': '아이디 중복확인을 해주세요.'})

    elif result is not None:
        return jsonify({'result': 'fail', 'msg': '아이디를 확인해주세요.'})
    else:
        db.user.insert_one({'id': id_receive, 'pw': pw_hash, 'nick': nickname_receive})
        return jsonify({'result': 'success', 'msg': '회원가입이 완료되었습니다.'})


@app.route('/api/id_overlap', methods=['POST'])
def id_overlap():
    id_receive = request.form['id_give']
    result = db.user.find_one({'id': id_receive})

    if id_receive == '':
        return jsonify({'result': 'fail', 'msg': '아이디를 입력해주세요'})
    elif result is not None:
        return jsonify({'result': 'fail', 'msg': '존재하는 아이디 입니다.'})
    else:
        return jsonify({'result': 'success', 'msg': '회원가입이 가능한 아이디입니다.'})


@app.route('/api/content', methods=['GET'])
def show_post():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        contents = list(db.posting.find({}).sort("date", -1).limit(20))
        for content in contents:
            db.posting.update_one({'_id': content["_id"]}, {'$set': {'post_id': str(content["_id"])}})
            content["_id"] = str(content["_id"])
            content["count_cheer"] = db.cheer.count_documents({"post_id": content["_id"], "type": "cheer"})
            content["cheer_by_me"] = bool(db.cheer.find_one({"post_id": content["_id"], "type": "cheer", "id": payload['id']}))
            content["my_post"] = bool(db.posting.find_one({"post_id": content["_id"], "id": payload['id']}))

        return jsonify({"result": "success", 'all_content': contents})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/api/content', methods=['POST'])
def post_content():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({'id': payload['id']})
        title_receive = request.form['title_give']
        comment_receive = request.form['comment_give']
        nickname_receive = request.form['nickname_give']
        date_receive = request.form["date_give"]

        doc = {
            'id': user_info['id'],
            'nick': user_info['nick'],
            'title': title_receive,
            'comment': comment_receive,
            'nickname': nickname_receive,
            'date': date_receive,
        }

        db.posting.insert_one(doc)

        return jsonify({'result': 'success', 'msg': '포스팅 완료'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


# [로그인 API]
# id, pw를 받아서 맞춰보고, 토큰을 만들어 발급합니다.
@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    # 회원가입 때와 같은 방법으로 pw를 암호화합니다.
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    # id, 암호화된pw을 가지고 해당 유저를 찾습니다.
    result = db.user.find_one({'id': id_receive, 'pw': pw_hash})

    # 찾으면 JWT 토큰을 만들어 발급합니다.
    if result is not None:
        # JWT 토큰에는, payload와 시크릿키가 필요합니다.
        # 시크릿키가 있어야 토큰을 디코딩(=풀기) 해서 payload 값을 볼 수 있습니다.
        # 아래에선 id와 exp를 담았습니다. 즉, JWT 토큰을 풀면 유저ID 값을 알 수 있습니다.
        # exp에는 만료시간을 넣어줍니다. 만료시간이 지나면, 시크릿키로 토큰을 풀 때 만료되었다고 에러가 납니다.
        payload = {
            'id': id_receive,
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        # token을 줍니다.
        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


# [유저 정보 확인 API]
# 로그인된 유저만 call 할 수 있는 API입니다.
# 유효한 토큰을 줘야 올바른 결과를 얻어갈 수 있습니다.
# (그렇지 않으면 남의 장바구니라든가, 정보를 누구나 볼 수 있겠죠?)
@app.route('/api/nick', methods=['GET'])
def api_valid():
    token_receive = request.cookies.get('mytoken')

    # try / catch 문?
    # try 아래를 실행했다가, 에러가 있으면 except 구분으로 가란 얘기입니다.

    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        print(payload)

        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        # 여기에선 그 예로 닉네임을 보내주겠습니다.
        userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})
        return jsonify({'result': 'success', 'nickname': userinfo['nick']})

    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})


@app.route('/update_cheerup', methods=['POST'])
def update_cheerup():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload["id"]})
        post_id_receive = request.form["post_id_give"]
        type_receive = request.form["type_give"]
        action_receive = request.form["action_give"]

        doc = {
            "post_id": post_id_receive,
            "id": user_info["id"],
            "type": type_receive
        }

        if action_receive == "cheerup":
            db.cheer.insert_one(doc)
        else:
            db.cheer.delete_one(doc)
        count = db.cheer.count_documents({"post_id": post_id_receive, "type": type_receive})
        return jsonify({"result": "success", 'msg': 'updated', "count": count})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
