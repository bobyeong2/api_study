from flask import Flask, jsonify,request
from flask.json import JSONEncoder

app = Flask(__name__)

app.users = {}
# 새로 가입한 사용자를 저장할 dict를 user변수에 할당
# key는 사용자 아이디가 될 것임 / value는 dict에 저장된 사용자 정보임

app.id_count = 1
# 회원가입하는 사용자의 id값을 저장할 변수
# 아래에서 확인할 수 있듯이 가입 인원이 추가될 때마다 +1


app.tweets = []
# 사용자들의 트윗들을 저장할 리스트, KEY는 사용자 아이디, value는 사용자의 트윗을 담음.

@app.route('/ping', methods=['GET'])
def index():

    return 'api project pong'


@app.route("/sign-up", methods=['POST'])
# 엔드포인트를 정의 / 고유 주소는 "/sign-up" / HTTP메소드는 POST로 한다

def sign_up():
    new_user = request.json
    # request는 엔드포인트에 전송된 HTTP요청 정보를 저장(*JSON)
    # .json은 위의 JSON 데이터를 python dict로 변환
    # 이걸로 new_user는 python dict자료가 된 거임
    
    new_user["id"] = app.id_count
    # new_user는 dict이고 dict이름["키 값"] = value 값임
    # new_user의 id라는 key에 app.id_count라는 value를 매치
    
    app.users[app.id_count] = new_user
    # app.users도 위에서 dict로 열어놨음
    # app.id_count에 해당하는 키값에 new_user라는 value를 매치
    
    app.id_count = app.id_count + 1
    
    return jsonify(new_user)
    # new_user를 python dict자료형으로 변환하여 return

@app.route('/tweet',methods=['POST'])
def tweet():
    payload = request.json
    user_id = int(payload['id'])
    tweet = payload['tweet']

    if user_id not in app.users :
        return '사용자가 존재하지 않습니다.',400

    if len(tweet) >300 :

        return '300자를 초과하였습니다.',400
    
    user_id = int(payload['id'])

    app.tweets.append({

        'user_id':user_id,'tweet':tweet
    })
    return '',200

@app.route('/follow',methods=['POST'])
def follow():

    payload = request.json
    user_id = int(payload['id'])
    user_id_to_follow = int(payload['follow'])

    if user_id not in app.users or user_id_to_follow not in app.users:
        return '사용자가 존재하지 않습니다.',400

    user = app.users[user_id]
    user.setdefault('follow',set()).add(user_id_to_follow)

    return jsonify(user)


class CustomJsonEncoder(JSONEncoder):

    def default(self,obj):
        if isinstance(obj,set):
            return list(obj)

        return JSONEncoder.default(self,obj)

app.json_encoder = CustomJsonEncoder

@app.route('/unfollow',methods=['POST'])
def unfollow():

    payload = request.json
    user_id = int(payload['id'])
    user_id_to_follow = int(payload['unfollow'])

    if user_id not in app.users or user_id_to_follow not in app.users:
        return '사용자가 존재하지 않습니다.',400

    user = app.users[user_id]
    user.setdefault('unfollow',set()).discard(user_id_to_follow)
    return jsonify(user)

@app.route('/timeline/<int:user_id>', methods=['GET'])
def timeline(user_id):
    if user_id not in app.users:
        return '유저가 존재 하지 않습니다', 400

    follow_list = app.users[user_id].get('follow', set())
    follow_list.add(user_id)
    timeline = [tweet for tweet in app.tweets if tweet['user_id'] in follow_list]

    return jsonify({
        'user_id'  : user_id,
        'timeline' : timeline
    })
