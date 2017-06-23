import subprocess
import requests
import re
import os

exit_code = 0

extensions = requests.get('http://standard.open-contracting.org/extension_registry/master/extensions.json').json()['extensions']

os.makedirs('extensions', exist_ok=True)
os.chdir('extensions')
extensions_dir = os.getcwd()

for entry in extensions:
    os.chdir(extensions_dir)
    m = re.match('https://raw.githubusercontent.com/([^/]*)/([^/]*)/([^/]*)', entry['url'])
    if not m:
        print('Error, we can\'t guess a git repo from entry url {}', entry['url'])
        exit_code = 1
        
    subprocess.call(['git', 'clone', '-b', m.group(3), 'https://github.com/{}/{}.git'.format(m.group(1), m.group(2))])
    os.chdir(m.group(2))
    subprocess.call(['ocds_extension_tester.py'])
exit(exit_code)
