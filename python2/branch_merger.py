__author__ = 'KAI8WZ'

import logging
import time
from optparse import OptionParser

import json
import urllib2
import base64

parser = OptionParser()

parser.add_option("-k", "--project-key",
                  dest="project_key")
parser.add_option("-r", "--repository",
                  dest="slug")
parser.add_option("-s", "--source-branch",
                  dest="source_branch")
parser.add_option("-d", "--dest-branch",
                  dest="dest_branch")
parser.add_option("-t", "--title",
                  dest="title")
parser.add_option("-m", "--description",
                  dest="description")
parser.add_option("-u", "--socialcoding_user",
                  dest="socialcoding_user")
parser.add_option("-p", "--socialcoding-password",
                  dest="socialcoding_password")


(options, args) = parser.parse_args()

# FROM: pipeline-BD.Utility.Scripts-python
def logger(func):
    def inner(*args, **kwargs):  #1
        log.info("[%s] Arguments were: %s, %s" % (func.__name__, args, kwargs))
        finished = False
        while not finished:
            try:
                result = func(*args, **kwargs)  #2
                finished = True
                return result
            except urllib2.HTTPError as e:
                log.error(e)
                finished = False
                time.sleep(5)

    return inner

@logger
def create_pull_request():
    user = sc_config['params'].socialcoding_user
    password = sc_config['params'].socialcoding_password
    url = sc_config['api']['create.pull.request.url']
    url = update_url(url)
    data = fill_template(create_pr_template)
    base_auth = base64.encodestring('%s:%s' % (user, password)).replace('\n', '')
    try:
        req = urllib2.Request(url, data=json.dumps(data))
        req.add_header("Authorization", "Basic %s" % base_auth)
        req.add_header("Content-Type", 'application/json')
        res = urllib2.urlopen(req)
        return json.load(res)['id']
    except urllib2.HTTPError as err:
        log.error(err)
        return None

@logger
def merge_pull_request(pr_id):
    if pr_id is None:
        pass
    params = vars(sc_config['params'])
    params['pr_id'] = str(pr_id)
    user = sc_config['params'].socialcoding_user
    password = sc_config['params'].socialcoding_password
    url = sc_config['api']['merge.pull.request.url']
    url = update_url(url, params)
    base_auth = base64.encodestring('%s:%s' % (user, password)).replace('\n', '')
    try:
        req = urllib2.Request(url, data="")
        req.add_header("Authorization", "Basic %s" % base_auth)
        req.add_header("Content-Type", 'application/json')
        res = urllib2.urlopen(req)
        return res.read()
    except urllib2.HTTPError as err:
        log.error(err)
        return None

def update_url(url, params=None):
    res = url
    if params is None:
        params = vars(sc_config['params'])
    for key, value in params.iteritems():
        if key in res:
            res = res.replace(key, value)
    return res

# fill template of bitbucket api request content with parameters
def fill_template(pr_template):
    result = pr_template
    params = vars(sc_config['params'])
    for key, value in params.iteritems():
        if value:
            update_dict(key, value, result)
    return result

# deep dict update. property is updated if either key or value eq opt param key - optional params by key, required by value
def update_dict(key, value, dictionary):
    if dictionary is not None:
        for k, v in dictionary.iteritems():
            if k == key or v == key:
                dictionary[k] = value
            elif isinstance(v, dict):
                update_dict(key, value, v)
            elif isinstance(v, list):
                for d in v:
                    update_dict(key, value, d)

@logger
def read_config():
    global sc_config, create_pr_template
    sc_config = read_json("config/socialcoding-config.json")
    sc_config['params'] = options
    create_pr_template = read_json("config/pr-create-template.json")

def read_json(name):
    with open(name, 'r') as stream:
        try:
            return json.load(stream)
        except TypeError as exc:
            log.error(exc)
    return None

@logger
def check_required_params():
    required = sc_config['opt']['required']
    for r in required:
        if options.__dict__[r] is None:
            parser.error("parameter %s required "%r)

@logger
def main():
    pr_id = create_pull_request()
    merge_pull_request(pr_id)
    return None

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    log = logging.getLogger(__name__)
    read_config()
    check_required_params()
    main()