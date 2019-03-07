#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os
import json
import shutil
import urllib3
import logging

logger = logging.getLogger(__name__)

HTTP = urllib3.PoolManager()

TEMPLATE_DIR = 'template'
OUTPUT_ABBS = 'abbs'
KEYS_NECESSARY = ['name', 'deps']
REPOLOGY_ENDPOINT = 'https://repology.org/api/v1/project/%s'


def autobuild_generate(src_file):
    content = json.loads(src_file.read())
    for key in KEYS_NECESSARY:
        if key not in content.keys():
            raise ValueError('field  \'%s\' is required')
    pkg_name = content['name']
    pkg_dep = ' '.join(content['deps'])
    pkg_desc = 'Empty package for Debiantai compatibility' + \
               (', ' + content['description'] if 'description' in content.keys() else '')
    if 'version' in content.keys():
        if content['version']['method'] == 'static':
            pkg_ver = content['version']['']
        elif content['version']['method'] == 'repology':
            r = HTTP.request('GET', REPOLOGY_ENDPOINT % content['version']['repology'])
            api_response = json.loads(r.data.decode('utf-8'))
            if 'distro' in content['version']:
                distro = content['version']['distro']
            else:
                distro = 'debian_testing'
            for package in api_response:
                if package['repo'] == distro:
                    pkg_ver = package['version']
                    break
            if not pkg_ver:
                raise ValueError('unable to obtain version info from repology')
        else:
            pkg_ver = '9999'
    dest = OUTPUT_ABBS + '/extra-spiral/' + content['name']
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(TEMPLATE_DIR, dest)
    for path, subdirs, files in os.walk(dest, followlinks=True):
        for name in files:
            dest_file_name = path + '/' + name
            with open(dest_file_name) as f:
                dest_file_content = f.read()
            dest_file_content = dest_file_content.replace('@NAME@', pkg_name)
            dest_file_content = dest_file_content.replace('@DEPS@', pkg_dep)
            dest_file_content = dest_file_content.replace('@DESC@', pkg_desc)
            dest_file_content = dest_file_content.replace('@VER@', pkg_ver)
            print(dest_file_content)
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
                except ValueError as e:
                    logger.error('%s omitted, %s' % (name, e))
                    continue


if __name__ == '__main__':
    generate('repo/packages/')