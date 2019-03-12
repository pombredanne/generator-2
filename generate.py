#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os
import json
import shutil
import urllib3
import logging

logger = logging.getLogger(__name__)

HTTP = urllib3.PoolManager(cert_reqs='CERT_REQUIRED')

TEMPLATE_DIR = 'template'
OUTPUT_ABBS = 'TREE'
KEYS_NECESSARY = ['name', 'deps']
VERSION_LOG = 'versions.json'
REPOLOGY_ENDPOINT = 'https://repology.org/api/v1/project/%s'

VERSIONS = dict()


def check_version(version):
    if version['method'] == 'static':
        return version['static']
    elif version['method'] == 'repology':
        r = HTTP.request('GET', REPOLOGY_ENDPOINT % version['repology'])
        api_response = json.loads(r.data.decode('utf-8'))
        if 'distro' in version.keys():
            distro = version['distro']
        else:
            distro = 'debian_testing'
        latest_ver = ''
        for package in api_response:
            if package['repo'] == distro:
                return package['version']
            if package['status'] == 'newest':
                latest_ver = package['version']
        if latest_ver:
            return latest_ver
        else:
            raise ValueError('unable to obtain version info from repology')
    else:
        return '9999'


def autobuild_generate(src_file):
    content = json.loads(src_file.read())
    for key in KEYS_NECESSARY:
        if key not in content.keys():
            raise ValueError('field  \'%s\' is required')
    pkg_name = content['name']
    pkg_dep = ' '.join(content['deps'])
    pkg_desc = 'Empty package for Debiantai compatibility' + \
               (', ' + content['description'] if 'description' in content.keys() else '')
    pkg_ver = '9999'
    if 'version' in content.keys():
        pkg_ver = check_version(content['version'])
    if pkg_name in VERSIONS.keys():
        if pkg_ver == VERSIONS[pkg_name]:
            logger.info('%s: no updates found, ignoring...')
            return
    VERSIONS[pkg_name] = pkg_ver
    dest = OUTPUT_ABBS + '/extra-spiral/' + content['name']
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(TEMPLATE_DIR, dest)
    for path, subdirs, files in os.walk(dest, followlinks=True):
        for name in files:
            dest_file_name = path + '/' + name
            with open(dest_file_name) as f:
                dest_file_content = f.read()
            dest_file_content = dest_file_content.replace('@NAME@', str(pkg_name))
            dest_file_content = dest_file_content.replace('@DEPS@', str(pkg_dep))
            dest_file_content = dest_file_content.replace('@DESC@', str(pkg_desc))
            dest_file_content = dest_file_content.replace('@VER@', str(pkg_ver))
            with open(dest_file_name, 'w') as f:
                f.write(dest_file_content)
    return


def generate(repo_location):
    if not os.path.exists(TEMPLATE_DIR):
        logger.error('Template directory does not exist, quitting...')
        exit(1)
    if not os.path.exists(OUTPUT_ABBS):
        os.makedirs(OUTPUT_ABBS + '/extra-spiral/')
    for path, subdirs, files in os.walk(repo_location, followlinks=True):
        for name in (files + subdirs):
            with open(path + name) as f:
                try:
                    autobuild_generate(f)
                    logger.info('%s prepared' % name)
                except ValueError as e:
                    logger.error('%s omitted, %s' % (name, e))
                    continue


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    if os.path.exists(VERSION_LOG):
        with open(VERSION_LOG) as f:
            try:
                VERSIONS = json.loads(f.read())
            except ValueError:
                logger.error('Invalid version cache, ignoring...')
                VERSIONS = dict()
    generate('repo/packages/')
    with open(VERSION_LOG, 'w') as f:
        f.write(json.dumps(VERSIONS, ensure_ascii=False))