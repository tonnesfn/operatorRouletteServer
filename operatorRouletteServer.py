import numpy as np
import matplotlib.pyplot as plt

from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import re
import json
import pickle
import os
from itertools import compress
import urllib

offset = 5000
operatorStats = {}


# This functions checks to see if the user has already been
def get_player_stats(username):
    global operatorStats
    global offset

    print(username + " is being looked up")

    r = requests.get("https://api.r6stats.com/api/v1/players/%s/operators?platform=uplay" % username)
    if r.status_code == 200:
        operatorStats[username] = r.json()

        outfile = open('stats.pickle', 'wb')
        pickle.dump(operatorStats, outfile)
        outfile.close()

        # Plot for username:

        names = []
        roles = []
        probabilities = []

        timeSumMinInv = 0.0
        for operator in operatorStats[username]['operator_records']:
            timeSumMinInv = timeSumMinInv + (1 / ((operator['stats']['playtime'] + offset) / 60))

        for operator in operatorStats[username]['operator_records']:
            operatorName = operator['operator']['name']
            operatorTimeMinInv = 1 / ((operator['stats']['playtime'] + offset) / 60)
            operatorPercentageInv = 100 * ((operatorTimeMinInv) / timeSumMinInv)

            names.append(operatorName)
            roles.append(operator['operator']['role'])
            probabilities.append(operatorPercentageInv)

        fig1, ax1 = plt.subplots()
        ax1.pie(list(compress(probabilities, np.array(roles) == "atk")),labels=list(compress(names, np.array(roles) == "atk")), autopct='%1.1f%%', shadow=True, startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.savefig(username+"_atk.pdf")
        plt.close()

        fig1, ax1 = plt.subplots()
        ax1.pie(list(compress(probabilities, np.array(roles) == "def")),labels=list(compress(names, np.array(roles) == "def")), autopct='%1.1f%%', shadow=True, startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.savefig(username + "_def.pdf")
        plt.close()

    else:
        print("Error " + str(r.status_code))

def getRandomOperator(username, role, banlist):
    global offset

    if role != "atk" and role != "def":
        print("Invalid role specified!")
        return ""

    names = []
    roles = []
    probabilities = []

    while(True):
        timeSumMinInv = 0.0
        for operator in operatorStats[username]['operator_records']:
            timeSumMinInv = timeSumMinInv + (1 / ((operator['stats']['playtime'] + offset) / 60))

        for operator in operatorStats[username]['operator_records']:
            operatorName = operator['operator']['name']
            operatorTimeMinInv = 1 / ((operator['stats']['playtime'] + offset) / 60)
            operatorPercentageInv = 100 * ((operatorTimeMinInv) / timeSumMinInv)

            names.append(operatorName)
            roles.append(operator['operator']['role'])
            probabilities.append(operatorPercentageInv)

        print(banlist)

        # Select operator:
        selector = np.random.rand() * 100
        for idx, probability in enumerate(probabilities):
            selector = selector - probability
            if selector < 0.0 and roles[idx] == role and names[idx] not in banlist:
                print(names[idx])
                return names[idx]


# This function returns a list of operators
def getOperators(username, role, number):
    global operatorStats

    operators = []

    # Check if username statistics exists, and get it if they do not
    if username not in operatorStats.keys():
        get_player_stats(username)

    for i in range(number):
        operators.append(getRandomOperator(username, role, operators))


    return operators


def getOperatorsHTML(username, role, number):
    operators = getOperators(username, role, number)

    returnString = ""

    for operator in operators:
        returnString = returnString + '<img src="images/operators/' + operator + '.png" alt="' + operator + '" style="width:9vw; height:auto"/>'

    return returnString

class ServerRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global operatorStats

        if self.path != '/favicon.ico':

            if self.path.endswith(".png"):

                try:
                    with open(os.curdir + os.sep + urllib.parse.unquote(self.path), 'rb') as file:
                        f = file.read()
                    mimetype = 'image/png'
                    self.send_response(200)
                    self.send_header('Content-type', mimetype)
                    self.end_headers()

                    self.wfile.write(f)

                except OSError as e:
                    print(e)
                    self.send_response(404)
                    self.end_headers()

            else:
                commands = re.split('\?|&', self.path)[1:]

                returnMessage = "<html> <head> <meta charset=\"UTF-8\"> </head>\n"

                for command in commands:
                    if command.startswith("users"):
                        users = command.split('=')[1].split(',')

                        for user in users:
                            returnMessage += user.lower() + ":<br />"
                            returnMessage += '<div style="margin-left: auto; margin-right: auto; width: 95vw; display: block;">'
                            returnMessage += getOperatorsHTML(user.lower(), 'atk', 5) + "<span style=\"margin-right:2.5vw; display:inline-block;\">&nbsp;</span>"
                            returnMessage += getOperatorsHTML(user.lower(), 'def', 5) + "<br />"
                            returnMessage += '</div>'

                returnMessage += "\n</html>"

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                # Write content as utf-8 data
                self.wfile.write(bytes(returnMessage, "utf8"))
                return

    def do_POST(self):
        self.send_response(500)
        self.end_headers()
        return


def run():
    global operatorStats

    if os.path.isfile("stats.pickle"):
        infile = open('stats.pickle', 'rb')
        operatorStats = pickle.load(infile)
        infile.close()
    else:
        operatorStats = {}

    server_address = ('localhost', 8081)
    httpd = HTTPServer(server_address, ServerRequestHandler)
    print('running server...')
    httpd.serve_forever()


run()
