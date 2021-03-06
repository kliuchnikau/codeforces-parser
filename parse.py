#!/usr/bin/python

# Python 2->3 libraries that were renamed.
try:
    from urllib2 import urlopen
except:
    from urllib.request import urlopen
try:
    from HTMLParser import HTMLParser
except:
    from html.parser import HTMLParser

# Other libraries.
from sys import argv
from subprocess import call
from functools import partial, wraps
import re
import os

# User modifiable constants:
TEMPLATE='main.rb'
SAMPLE_INPUT='input'
SAMPLE_OUTPUT='output'
MY_OUTPUT='my_output'

# Do not modify these!
VERSION='CodeForces Parser v1.5: https://github.com/johnathan79717/codeforces-parser'
RED_F='\033[31m'
GREEN_F='\033[32m'
BOLD='\033[1m'
NORM='\033[0m'
TIME_CMD='`which time`'
TIME_AP=''

# Problems parser.
class CodeforcesProblemParser(HTMLParser):

    def __init__(self, folder):
        HTMLParser.__init__(self)
        self.folder = folder
        self.num_tests = 0
        self.testcase = None
        self.start_copy = False

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            if attrs == [('class', 'input')]:
                self.num_tests += 1
                self.testcase = open(
                    '%s/%s%d' % (self.folder, SAMPLE_INPUT, self.num_tests), 'w')
            elif attrs == [('class', 'output')]:
                self.testcase = open(
                    '%s/%s%d' % (self.folder, SAMPLE_OUTPUT, self.num_tests), 'w')
        elif tag == 'pre':
            if self.testcase != None:
                self.start_copy = True

    def handle_endtag(self, tag):
        if tag == 'br':
            if self.start_copy:
                self.testcase.write('\n')
                self.end_line = True
        if tag == 'pre':
            if self.start_copy:
                if not self.end_line:
                    self.testcase.write('\n')
                self.testcase.close()
                self.testcase = None
                self.start_copy = False

    def handle_entityref(self, name):
        if self.start_copy:
            self.testcase.write(self.unescape(('&%s;' % name)))

    def handle_data(self, data):
        if self.start_copy:
            self.testcase.write(data)
            self.end_line = False

# Contest parser.
class CodeforcesContestParser(HTMLParser):

    def __init__(self, contest):
        HTMLParser.__init__(self)
        self.contest = contest
        self.start_contest = False
        self.start_problem = False
        self.name = ''
        self.problem_name = ''
        self.problems = []
        self.problem_names = []

    def handle_starttag(self, tag, attrs):
        if self.name == '' and attrs == [('style', 'color: black'), ('href', '/contest/%s' % (self.contest))]:
                self.start_contest = True
        elif tag == 'option':
            if len(attrs) == 1:
                regexp = re.compile(r"u'[A-Z].*'")
                string = str(attrs[0])
                search = regexp.search(string)
                if search is not None:
                    self.problems.append(search.group(0).split("'")[-2])
                    self.start_problem = True

    def handle_endtag(self, tag):
        if tag == 'a' and self.start_contest:
            self.start_contest = False
        elif self.start_problem:
            self.problem_names.append(self.problem_name)
            self.problem_name = ''
            self.start_problem = False

    def handle_data(self, data):
        if self.start_contest:
            self.name = data
        elif self.start_problem:
            self.problem_name += data

# Parses each problem page.
def parse_problem(folder, contest, problem):
    url = 'http://codeforces.com/contest/%s/problem/%s' % (contest, problem)
    html = urlopen(url).read()
    parser = CodeforcesProblemParser(folder)
    parser.feed(html.decode('utf-8'))
    # .encode('utf-8') Should fix special chars problems?
    return parser.num_tests

# Parses the contest page.
def parse_contest(contest):
    url = 'http://codeforces.com/contest/%s' % (contest)
    html = urlopen(url).read()
    parser = CodeforcesContestParser(contest)
    parser.feed(html.decode('utf-8'))
    return parser

# Generates the test script.
def generate_test_script(folder, num_tests, problem, test_file):
    with open(folder + 'test.sh', 'w') as test:
        test.write(
            ('#!/bin/bash\n'
            'INPUT_NAME='+SAMPLE_INPUT+'\n'
            'OUTPUT_NAME='+SAMPLE_OUTPUT+'\n'
            'MY_NAME='+MY_OUTPUT+'\n').format(problem))
        test.write(
            'for test_file in $INPUT_NAME*\n'
            'do\n'
            '    i=$((${{#INPUT_NAME}}))\n'
            '    test_case=${{test_file:$i}}\n'
            '    rm -R $MY_NAME*\n'
            '    if ! {5} ./main.rb < $INPUT_NAME$test_case > $MY_NAME$test_case; then\n'
            '        echo {1}{4}Sample test \#$test_case: Runtime Error{2} {6}\n'
            '        echo ========================================\n'
            '        echo Sample Input \#$test_case\n'
            '        cat $INPUT_NAME$test_case\n'
            '    else\n'
            '        if diff --brief $MY_NAME$test_case $OUTPUT_NAME$test_case; then\n'
            '            echo {1}{3}Sample test \#$test_case: Accepted{2} {6}\n'
            '        else\n'
            '            echo {1}{4}Sample test \#$test_case: Wrong Answer{2} {6}\n'
            '            echo ========================================\n'
            '            echo Sample Input \#$test_case\n'
            '            cat $INPUT_NAME$test_case\n'
            '            echo ========================================\n'
            '            echo Sample Output \#$test_case\n'
            '            cat $OUTPUT_NAME$test_case\n'
            '            echo ========================================\n'
            '            echo My Output \#$test_case\n'
            '            cat $MY_NAME$test_case\n'
            '            echo ========================================\n'
            '        fi\n'
            '    fi\n'
            'done\n'
            .format(num_tests, BOLD, NORM, GREEN_F, RED_F, TIME_CMD, TIME_AP))
    call(['chmod', '+x', folder + 'test.sh'])

def init_git(folder):
    FNULL = open(os.devnull, 'w')
    call(['cd', folder])
    call(['git', 'init'], stdout=FNULL, stderr=FNULL)
    call(['git', 'add', '.'], stdout=FNULL, stderr=FNULL)
    call(['git', 'commit', '-m', "'Initial commit'"], stdout=FNULL, stderr=FNULL)
    print ('Local Git repo initiated')
    print ('========================================')

# Main function.
def main():
    print (VERSION)
    if(len(argv) < 2):
        print('USAGE: ./parse.py 512')
        return
    contest = argv[1]

    # Find contest and problems.
    print ('Parsing contest %s, please wait...' % contest)
    content = parse_contest(contest)
    print (BOLD+GREEN_F+'*** Round name: '+content.name+' ***'+NORM)
    print ('Found %d problems!' % (len(content.problems)))

    # Find problems and test cases.
    for index, problem in enumerate(content.problems):
        print ('Downloading Problem %s: %s...' % (problem, content.problem_names[index]))
        folder = '%s/%s/' % (contest, problem)
        call(['mkdir', '-p', folder])

        template_file_folder = os.path.split(os.path.abspath(os.path.realpath(argv[0])))[0]
        template_file_path = os.path.join(template_file_folder, TEMPLATE)
        call(['cp', '-n', template_file_path, '%s/%s/' % (contest, problem)])
        call(['chmod', '+x', folder + TEMPLATE])

        template_file_path_haskell = os.path.join(template_file_folder, 'main.hs')
        call(['cp', '-n', template_file_path_haskell, '%s/%s/' % (contest, problem)])
        call(['chmod', '+x', folder + 'main.hs'])

        num_tests = parse_problem(folder, contest, problem)
        print('%d sample test(s) found.' % num_tests)
        generate_test_script(folder, num_tests, problem, TEMPLATE)
        print ('========================================')

    init_git(contest)
    print ('Use ./test.sh to run sample tests in each directory.')

if __name__ == '__main__':
    main()

