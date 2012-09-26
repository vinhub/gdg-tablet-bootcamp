#!/usr/bin/env python
"""
build.py - Combine (and minify) javascript files in js directory.
"""

import re
import os
import sys
import stat
import hmac
import hashlib
import urllib
import urllib2
from base64 import b64encode
from datetime import datetime
from fnmatch import fnmatch
import json

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_PATH = os.path.join(ROOT_PATH, 'app')
sys.path.insert(0, APP_PATH)

import settings

# See http://code.google.com/closure/compiler/docs/gettingstarted_api.html
CLOSURE_API = 'http://closure-compiler.appspot.com/compile'


def print_closure_messages(json, prop):
    if prop not in json:
        return

    print "Closure %s:" % prop
    for message in json[prop]:
        print "%d:%d: %s" % (message['lineno'], message['charno'],
                             message.get('error', '') + message.get('warning', ''))


HASH_PREFIX = '/* Source hash: %s */\n'


def closure_compiler(js_code):
    params = [
        ('compilation_level', 'SIMPLE_OPTIMIZATIONS'),
        ('output_info', 'compiled_code'),
        ('output_info', 'errors'),
        ('output_info', 'warnings'),
        ('output_info', 'statistics'),
        ('output_format', 'json'),
    ]

    params.append(('js_code', js_code))
    data = urllib.urlencode(params)
    output = urllib2.urlopen(CLOSURE_API, data).read()
    output = json.loads(output)

    print_closure_messages(output, 'errors')
    # print_closure_messages(output, 'warnings')

    return (HASH_PREFIX % hashlib.sha256(js_code).hexdigest()) + output['compiledCode']


def combine_javascript():
    for app_name, app in settings.App.all_apps.items():
        js_dir = os.path.join(APP_PATH, 'js')

        js_code = ''
        for basename in app.scripts:
            with open(os.path.join(js_dir, basename + '.js')) as js_file:
                js_code += "\n/* %s */\n" % basename
                js_code += js_file.read()

        print "Combining files into %s.js." % app_name
        with open(os.path.join(js_dir, 'combined', '%s.js' % app_name), 'w') as combined_file:
            combined_file.write(js_code)

        print "Combining files into %s-min.js." % app_name
        with open(os.path.join(js_dir, 'combined', '%s-min.js' % app_name), 'w') as combined_min_file:
            minified = closure_compiler(js_code)
            combined_min_file.write(minified)


def main():
    combine_javascript()


if __name__ == '__main__':
    main()
