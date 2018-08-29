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

        # Select operator:
        selector = np.random.rand() * 100
        for idx, probability in enumerate(probabilities):
            selector = selector - probability
            if selector < 0.0 and roles[idx] == role and names[idx] not in banlist:
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


def getControlBar(users, autoRefresh):
    returnString = ""

    if len(users) != 0:
        userString = ",".join(users) + ','
    else:
        userString = ''

    # Add user form
    returnString += '<br /><div style="margin-left: auto; margin-right: auto; width: 500px"><form oninput="users.value = \'' + userString + '\' + latest.value" action="/" onsubmit="latest.name = \'\'" method="get"> <input type="text" name="latest" placeholder="Username"><input type="hidden" name="users"><input type="submit" value="Add">'

    # Auto refresh button
    if autoRefresh:
        returnString += '<button style="margin-left: 10px"; type = "button" onclick = "location.href = \'/?users=' + userString[:-1] + '\';">Disable autorefresh</button>'
    else:
        returnString += '<button style="margin-left: 10px"; type = "button" onclick = "location.href = \'/?autorefresh=true&users=' + userString[:-1] + '\';">Enable autorefresh</button>'
    returnString += '</form></div>'

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
                commands = re.split('\?|&', urllib.parse.unquote(self.path))[1:]

                # Auto refresh feature:
                autoRefresh = False
                for command in commands:
                    if command.startswith("autorefresh"):
                        autoRefresh = True

                returnMessage = "<html> <head> <meta charset=\"UTF-8\">"
                if autoRefresh: returnMessage += '<meta http-equiv="refresh" content="60" >'
                returnMessage += "</head> <body style=\"background-color: #151618\">\n"

                users = []

                for command in commands:
                    if command.startswith("users"):
                        users = command.split('=')[1].split(',')

                        # Get operator images:
                        for user in users:
                            attack = getOperators(user.lower(), 'atk', 5)
                            defence = getOperators(user.lower(), 'def', 5)

                            # User div
                            returnMessage += '<div style="margin-bottom: 25px">'

                            # Print username
                            returnMessage += '<div style="padding-bottom: 10px; margin: 0px; margin-left: auto; margin-right: auto; width: 90vw; display: block; text-align: center; color: white; font-size: 5.9vw;">' + user.lower() + "</div>"

                            # Print images
                            returnMessage += '<div style="margin-left: auto; margin-right: auto; width: 90vw; display: block;">'
                            for op in attack:
                                returnMessage += '<img src="http://robotikk.net/R6/images/operators/' + op + '.png" alt="' + op + '" style="width:8vw; height:auto"/>'

                            returnMessage += "<span style=\"margin-right:4vw; display:inline-block;\"></span>"

                            for op in defence:
                                returnMessage += '<img src="http://robotikk.net/R6/images/operators/' + op + '.png" alt="' + op + '" style="width:9vw; height:auto"/>'

                            returnMessage += '</div>'

                            # Print operator names
                            returnMessage += '<div style="margin-left: auto; margin-right: auto; width: 90vw; display: block; font-size: 2.0vw;">'
                            for op in attack:
                                returnMessage += '<div style="width:8vw; display:inline-block; text-align:center; color: white;">' + op + '</div>'

                            returnMessage += "<span style=\"margin-right:4vw; display:inline-block;\"></span>"

                            for op in defence:
                                returnMessage += '<div style="width:9vw; display:inline-block; text-align:center; color: white; font-size: 2.0vw;">' + op + '</div>'

                            # Close op name div
                            returnMessage += '</div>'

                            # Close user div
                            returnMessage += '</div>'

                # Add user selection bar:
                returnMessage += getControlBar(users, autoRefresh)

                returnMessage += "\n</body></html>"

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

    server_address = ('192.168.1.6', 8081)
    httpd = HTTPServer(server_address, ServerRequestHandler)
    print('running server...')
    httpd.serve_forever()


run()
