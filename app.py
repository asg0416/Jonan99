from flask import Flask, render_template, jsonify, request
import requests

app = Flask(__name__)

@app.route('/')
def home():
   return render_template('index.html')


@app.route('/post_home')
def post_home():
    water = requests.get('http://openapi.seoul.go.kr:8088/546c635a6e61736733394979736142/json/WPOSInformationTime/1/5/')
    water_response = water.json()
    water_temp = water_response['WPOSInformationTime']['row'][0]['W_TEMP']

    weather = requests.get('http://api.openweathermap.org/data/2.5/weather?lat=37.56826&lon=126.977829&APPID=8bab5afa1c8be369722bbca48120e0bc')
    weather_response = weather.json()
    weather_temp = weather_response['main']['temp'] - 273.15
    return render_template('post_home.html', water_temp=water_temp, weather_temp=weather_temp)


@app.route('/login')
def login():
   return render_template('login.html')

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


app.run('0.0.0.0',port=5000,debug=True)