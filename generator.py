#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

"""
Generates autobuild files from template
"""

import os
import json
import shutil
import urllib3
import logging

logger = logging.getLogger(__name__)

HTTP = urllib3.PoolManager(cert_reqs='CERT_REQUIRED')

# Configurations
SOURCE_DIR = 'repo/packages/'
TEMPLATE_DIR = 'template'
OUTPUT_ABBS = 'TREE'
OUTPUT_CATEGORY = 'extra-spiral'
KEYS_NECESSARY = ['name', 'deps']
VERSION_LOG = 'versions.json'
REPOLOGY_ENDPOINT = 'https://repology.org/api/v1/project/%s'


class NoUpdatesException(Exception):
    """Raised when there are no available updates for the package"""


class Generator(object):
    """Main class of the Spiral generator"""

    def __init__(
            self, sources='repo/packages/', version_log='versions.json',
            output='TREE/extra-spiral/', template='template'
    ):
        """
        Initialize the generator object
        :param sources: Path to the source files
        :param version_log: Path to the version log
        :param output: Where to output
        :param template: Path to the template
        """
        if not os.path.exists(template):
            logger.error('Template directory does not exist, quitting...')
            raise ValueError('Given template directory(%s) does not exist' % template)
        self.output = output
        self.sources = sources
        self.template = template
        self.version_log = version_log
        if os.path.exists(version_log):
            with open(version_log) as f:
                try:
                    self.versions = json.loads(f.read())
                except ValueError:
                    logger.error('Invalid version log, ignoring...')
                    self.versions = dict()
        else:
            self.versions = dict()

    @staticmethod
    def check_upper(string):
        return all(map(str.isupper, string))

    @staticmethod
    def check_version(version):
        """
        Get correct version from the source definition

        :param version: Version part of the source definition
        :return: The version of the package generated from the source file
        """
        if version['method'] == 'static':
            return version['static']
        elif version['method'] == 'repology':
            r = HTTP.request('GET', REPOLOGY_ENDPOINT % version['repology'])
            api_response = json.loads(r.data.decode('utf-8'))
            if 'distro' in version.keys():
                distro = version['distro']
            else:
                distro = 'debian_testing'  # Follow Debiantai testing as default
            latest_ver = ''
            for package in api_response:
                if package['repo'] == distro:
                    return package['version']
                if package['status'] == 'newest':
                    latest_ver = package['version']
            if distro == 'latest' and latest_ver:
                return latest_ver
            else:
                raise ValueError('unable to obtain version info from repology')
        else:
            return '9999'

    def get_package_info(self, src):
        for key in KEYS_NECESSARY:
            if key not in src.keys():
                raise ValueError('field  \'%s\' is required')
        pkg_info = dict()
        pkg_info['NAME'] = src['name']
        pkg_info['DEPS'] = ' '.join(src['deps'])
        pkg_info['DESC'] = 'Empty package for Debiantai compatibility' + \
                           (', ' + src['description'] if 'description' in src.keys() else '')
        pkg_info['VER'] = '9999'
        if 'version' in src.keys():
            pkg_info['VER'] = self.check_version(src['version'])
        if pkg_info['NAME'] in self.versions.keys():
            if pkg_info['VER'] == self.versions[pkg_info['NAME']]:
                raise NoUpdatesException("no available updates")
        self.versions[pkg_info['NAME']] = pkg_info['VER']
        # Copy all uppercase keys
        for key in src.keys():
            if self.check_upper(key):
                pkg_info[key] = src[key]
        return pkg_info

    def autobuild_generate(self, content):
        """
        Generate autobuild files from template

        :param content: Content (parsed) of the source file
        :return: Version logs
        """
        pkg_info = self.get_package_info(content)
        dest = self.output + content['name'] + '/'
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(self.template, dest)
        for path, subdirs, files in os.walk(dest, followlinks=True):
            for name in files:
                dest_file_name = path + '/' + name
                with open(dest_file_name) as f:
                    dest_file_content = f.read()
                for key in pkg_info.keys():
                    dest_file_content = dest_file_content.replace(
                        '@' + key + '@', pkg_info[key]
                    )
                    print(dest_file_content)
                    print(dest_file_name)
                with open(dest_file_name, 'w') as f:
                    f.write(dest_file_content)

    def generate(self):
        """
        Generate autobuild tree from given spiral format repo

        :return: None
        """
        logger.info('>>> Generation start')
        if os.path.exists(self.output):
            shutil.rmtree(self.output)
        os.makedirs(self.output)
        for path, subdirs, files in os.walk(self.sources, followlinks=True):
            for name in (files + subdirs):
                with open(path + name) as f:
                    try:
                        self.autobuild_generate(json.loads(f.read()))
                        logger.info('%s: prepared' % name)
                    except Exception as e:
                        logger.error('%s: omitted, %s' % (name, e))
                        continue
        logger.info('>>> Generation finished')
        logger.info('>>> Saving version log...')
        with open(self.version_log, 'w') as f:
            f.write(json.dumps(self.versions, ensure_ascii=False))
        logger.info('>>> All done, execute build.sh to start building packages')
        return


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    generator = Generator(
        sources=SOURCE_DIR, output=OUTPUT_ABBS + '/' + OUTPUT_CATEGORY + '/',
        version_log=VERSION_LOG, template=TEMPLATE_DIR
    )
    generator.generate()
