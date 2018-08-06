import numpy as np
import matplotlib.pyplot as plt

from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import re
import json
import pickle
import os
from itertools import compress

operatorStats = {}


# This functions checks to see if the user has already been
def get_player_stats(username):
    global operatorStats

    print(username + " is being looked up")

    r = requests.get("https://api.r6stats.com/api/v1/players/%s/operators?platform=uplay" % username)
    if r.status_code == 200:
        operatorStats[username] = r.json()

        outfile = open('stats.pickle', 'wb')
        pickle.dump(operatorStats, outfile)
        outfile.close()

    else:
        print("Error " + str(r.status_code))

def getRandomOperator(username, role, banlist):
    offset = 5000

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

        sumInv = 0
        for operator in operatorStats[username]['operator_records']:
            operatorName = operator['operator']['name']
            operatorTimeMinInv = 1 / ((operator['stats']['playtime'] + offset) / 60)
            operatorPercentageInv = 100 * ((operatorTimeMinInv) / timeSumMinInv)
            sumInv = sumInv + operatorPercentageInv

            names.append(operatorName)
            roles.append(operator['operator']['role'])
            probabilities.append(operatorPercentageInv)

        # Plot:
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


        # Select operator:
        selector = np.random.rand() * 100
        for idx, probability in enumerate(probabilities):
            selector = selector - probability
            if selector < 0.0 and roles[idx] == role and names[idx] not in banlist:
                return names[idx]


# This function returns the HTML for the given username
def getOperators(username, role, number):
    global operatorStats

    operators = []

    # Check if username statistics exists, and get it if they do not
    if username not in operatorStats.keys():
        get_player_stats(username)

    for i in range(number):
        operators.append(getRandomOperator(username, role, operators))

    return ', '.join(operators)

class ServerRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global operatorStats

        if self.path != '/favicon.ico':
            print("Got a get request: %s" % self.path)

            commands = re.split('\?|&', self.path)[1:]

            returnMessage = " "

            for command in commands:
                if command.startswith("users"):
                    users = command.split('=')[1].split(',')
                    returnMessage = "Attack: <br />"

                    # Do attack:
                    for user in users:
                        returnMessage = returnMessage + " - " + user + ": " + getOperators(user, 'atk', 3) + "<br />"

                    # Defense:
                    returnMessage = returnMessage + "Defense: <br />"
                    for user in users:
                        returnMessage = returnMessage + " - " + user + ": " + getOperators(user, 'def', 3) + "<br />"



            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Write content as utf-8 data
            self.wfile.write(bytes(returnMessage, "utf8"))
            return

    def do_POST(self):
        print("Got a post request")
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

    server_address = ('127.0.0.1', 8081)
    httpd = HTTPServer(server_address, ServerRequestHandler)
    print('running server...')
    httpd.serve_forever()


run()
