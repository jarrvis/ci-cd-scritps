__author__ = 'jarrvis'

import logging
import time
from optparse import OptionParser
import os
from os.path import basename
import json
import urllib2
import base64
import fileinput
import subprocess

parser = OptionParser()

parser.add_option("-r", "--repository",
                  dest="repository")
parser.add_option("-n", "--name",
                  dest="name")
parser.add_option("-c", "--conf_path",
                  dest="conf_path")
parser.add_option("-t", "--property_name",
                  dest="property")
parser.add_option("-u", "--artifactory_user",
                  dest="artifactory_user")
parser.add_option("-p", "--artifactory_password",
                  dest="artifactory_password")


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


def update_url(url, params=None):
    res = url
    if params is None:
        params = vars(art_config['params'])
    for key, value in params.iteritems():
        if key in res:
            res = res.replace(key, value)
    return res


@logger
def find_last_modified_artifact():
    params = vars(art_config['params'])
    user = art_config['params'].artifactory_user
    password = art_config['params'].artifactory_password
    url = art_config['api']['last.modified.artifact.url']
    url = update_url(url, params)
    base_auth = base64.encodestring('%s:%s' % (user, password)).replace('\n', '')
    try:
        req = urllib2.Request(url)
        req.add_header("Authorization", "Basic %s" % base_auth)
        req.add_header("Content-Type", 'application/json')
        res = urllib2.urlopen(req)
        return json.load(res)['uri']
    except urllib2.HTTPError as err:
        log.error(err)
        return None

@logger
def extract_artifact_version(uri):
    name = art_config['params'].name
    artifact = os.path.splitext(basename(uri))[0]
    artifact_version = artifact.replace(name+'-', '')
    return artifact_version

@logger
def update_property(version):
    if not version:
        pass
    conf_path = art_config['params'].conf_path
    property = art_config['params'].property
    if conf_path and property:
        key = property + '='
        for line in fileinput.FileInput(conf_path, inplace=1):
            if key in line:
                line = key + version
            print line


@logger
def commit_and_push():
    conf_path = art_config['params'].conf_path
    subprocess.Popen("git commit -m 'Artifact version update' " + conf_path, stdout=subprocess.PIPE)
    #p = subprocess.Popen("git push" + conf_path, stdout=subprocess.PIPE)
    out, err = p.communicate()
    sha = out.strip()

@logger
def read_config():
    global art_config
    art_config = read_json("config/artifactory-config.json")
    art_config['params'] = options

def read_json(name):
    with open(name, 'r') as stream:
        try:
            return json.load(stream)
        except TypeError as exc:
            log.error(exc)
    return None

@logger
def check_required_params():
    required = art_config['opt']['required']
    for r in required:
        if options.__dict__[r] is None:
            parser.error("parameter %s required "%r)

@logger
def main():
    artifact_uri = find_last_modified_artifact()
    version = extract_artifact_version(artifact_uri)
    update_property(version)
    commit_and_push()
    return version

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    log = logging.getLogger(__name__)
    read_config()
    check_required_params()
    main()