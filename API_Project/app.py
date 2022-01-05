from datetime import timedelta
from flask import Flask, jsonify, request, current_app
from flask.json import JSONEncoder
from sqlalchemy import create_engine, text
import bcrypt
import jwt
# 22:58
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj): #default method를 over write 함.
        if isinstance(obj, set): #set타입이라면 list로 변환한다.
            return list(obj)
        return JSONEncoder.default(self, obj)
#app.json_encoder = CustomJSONEncoder

def create_app(test_config = None): #flask가 자동으로 이 함수를 인식함. 또한 test_config라는 인자를 받아 유닛테스트때 사용.
    app = Flask(__name__)
    app.json_encoder = CustomJSONEncoder
    if test_config is None:
        app.config.from_pyfile("config.py") #unittest 하는 경우가 아니라면 config.py를 읽는다.
    else:
        app.config.update(test_config)
    
    database = create_engine(app.config['DB_URL'], encoding = 'utf-8', max_overflow = 0) #sqlAlchemy사용하는 부분임.
    app.database = database #생성한 Engine 객체를 플라스크 객체에 저장함. 이로써 현재 .py파일에서 데이터 베이스 접근이 가능함.

    return app

app = create_app() 

@app.route("/ping", methods = ['GET'])
def ping():
    return "pong"

# 회원 가입 데코레이터 부분 ------------------------------------
@app.route("/sign-up", methods=['POST']) #포스트 임을 주의
def sign_up():
    new_user        = request.json  # request는 endpoint에 전송된 해당 HTTP요청을 통해 전송된 json데이터를 파이썬 딕셔너리로 변환해준다.
    new_user['password'] = bcrypt.hashpw(
        new_user['password'].encode('utf-8'),bcrypt.gensalt()
            )
    new_user_id = app.database.execute(text("""
    INSERT INTO users(
        name,
        email,
        profile,
        hashed_password
    ) VALUES(
        :name,
        :email,
        :profile,
        :password
    ) 
     """), new_user).lastrowid

    row = current_app.database.execute(text("""
        SELECT 
            id,
            name,
            email,
            profile
        FROM users
        WHERE id = :user_id
    """),{
        'user_id': new_user_id
    }).fetchone()
    
    created_user = {
        'id'      : row['id'], 
        'name'    : row['name'],
        'email'   : row['email'],
        'profile' : row['profile']
    } if row else None
 
    return jsonify(created_user) # dictionary를 json으로 변환해줌.

 
 
@app.route('/tweet',methods=["POST"])
def tweet():
    user_tweet  = request.json
    tweet       = user_tweet['tweet']
    
    if len(tweet) > 300 :
        return '300자를 초과하였습니다.', 400
    
    app.database.execute(text("""
    
        INSERT INTO tweets(
            user_id, tweet
            ) values(
                
                :id,
                :tweet
            )
    """), user_tweet)

    return '',200

@app.route('/timeline/<int:user_id>',methods=["GET"])
def timeline(user_id):
    rows = app.database.execute(text("""
    
        SELECT t.user_id, t.tweet
            FROM tweets t
            LEFT JOIN users_follow_list ufl ON ufl.user_Id = :user_id
            WHERE t.user_id = :user_id
            OR t.user_id = ufl.follow_user_id
    
    """), {'user_id':user_id}).fetchall()


    timeline = [{

        'user_id':row['user_id'],
        'tweet':row['tweet'],


    } for row in rows]

    return jsonify({
        
        'user_id':user_id,
        'timeline':timeline
        })

def insert_unfollow(user_unfollow):
    return current_app.database.execute(text("""
        DELETE FROM users_follow_list
        WHERE user_id = :id
        AND follow_user_id = :unfollow
    """), user_unfollow).rowcount

@app.route('/unfollow', methods=['POST'])
def unfollow():
    payload = request.json
    insert_unfollow(payload)

    return '', 200


@app.route('/login')
def login():
    credential = request.json
    email = credential['email']
    password = credential['password']

    row = database.execute(text("""
        SELECT id,hashed_password
        FROM users
        WHERE eamil :eamil
    """),{'email':email}).fetchall()

    if row and bcrypt.checkpw(password.encode('utf8'), row['hashed_password'].encode('utf8')):
        user_id = row['id']
        payload = {

            'user_id' : user_id,
            'exp' : datetime.utcnow() + timedelta(seconds= 60 * 60 * 24)

        }
        token = jwt.encode(payload, app.config['JWT_SECRET_KEY'],'HS256')
        return jsonify({
            'access_token':token.decode('UTF-8')
        })

    else :

        return '',401
