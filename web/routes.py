from flask import redirect, url_for, session, request
from rauth.service import OAuth1Service, OAuth1Session
import xmltodict
from web import app
import config as cfg

goodreads_service = OAuth1Service(
    consumer_key=cfg.goodreads['key'],
    consumer_secret=cfg.goodreads['secret'],
    name='goodreads',
    request_token_url='https://www.goodreads.com/oauth/request_token',
    authorize_url='https://www.goodreads.com/oauth/authorize',
    access_token_url='https://www.goodreads.com/oauth/access_token',
    base_url='https://www.goodreads.com/'
)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def run():
    return 'Hello World!<br><a href="{url}"><button>Login</button></a>'.format(url=url_for('login'))

@app.route('/login')
def login():
    if 'access_token' in session and 'access_token_secret' in session and 'user_id' in session:
        return '<a href="{url}"><button>Continue</button></a>'.format(url=url_for('get_read_list', id=session['user_id']))

    session['request_token'], session['request_token_secret'] = goodreads_service.get_request_token(header_auth=True)
    authorize_url = goodreads_service.get_authorize_url(session['request_token'])

    return """
        <a href={url} target='_blank'>Click here to grant access</a>
        <br>
        <a href='./login/callback'>
            <button>Click Here after access has been granted</button>
        </a>
    """.format(url=authorize_url)

@app.route('/login/callback')
def login_callback():
    oauth_session = goodreads_service.get_auth_session(session['request_token'], session['request_token_secret'])

    session['access_token'] = oauth_session.access_token
    session['access_token_secret'] = oauth_session.access_token_secret
    session['user_id'] = get_user_id()

    return redirect(url_for('get_read_list', id=session['user_id']))

@app.route('/users/<id>/readList')
@login_required
def get_read_list(id):
    url = 'https://www.goodreads.com/review/list/{id}.xml?key={key}&v=2&shelf=read&per_page=200&page=1'.format(id=id, key=cfg.goodreads['key'])

    json_data = get_json_data(url)
    return json_data['GoodreadsResponse']['reviews']

def get_user_id():
    url = 'https://www.goodreads.com/api/auth_user'
    json_data = get_json_data(url)
    return json_data['GoodreadsResponse']['user']['@id']

def get_json_data(url):
    oauth_session = OAuth1Session(
        consumer_key=cfg.goodreads['key'],
        consumer_secret=cfg.goodreads['secret'],
        access_token=session['access_token'],
        access_token_secret=session['access_token_secret'])

    response = oauth_session.get(url)
    xml_data = response.content

    return xmltodict.parse(xml_data)
