import numpy as np
import matplotlib.pyplot as plt

from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import re
import json
import pickle
import os

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

def getRandomOperator(username, role):
    if role != "atk" and role != "def":
        print("Invalid role specified!")
        return ""

    names = []
    roles = []
    probabilities = []

    while(True):
        timeSumMin = 0.0
        timeSumMinInv = 0.0
        for operator in operatorStats[username]['operator_records']:

            timeSumMin = timeSumMin + (operator['stats']['playtime'] / 60)
            timeSumMinInv = timeSumMinInv + (1 / (operator['stats']['playtime'] / 60))

        sumInv = 0
        for operator in operatorStats[username]['operator_records']:

            operatorName = operator['operator']['name']
            operatorTimeMin = operator['stats']['playtime'] / 60
            operatorPercentage = 100 * (operatorTimeMin) / timeSumMin
            operatorTimeMinInv = 1 / (operator['stats']['playtime'] / 60)
            operatorPercentageInv = 100 * ((operatorTimeMinInv) / timeSumMinInv)
            sumInv = sumInv + operatorPercentageInv

            names.append(operatorName)
            roles.append(operator['operator']['role'])
            probabilities.append(operatorPercentageInv)

        fig1, ax1 = plt.subplots()
        ax1.pie(probabilities,labels=names, autopct='%1.1f%%',
                shadow=True, startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

        plt.savefig(username+".pdf")

        selector = np.random.rand() * 100
        for idx, probability in enumerate(probabilities):
            selector = selector - probability
            if selector < 0.0:
                if roles[idx] == role:
                    return names[idx]

# This function returns the HTML for the given username
def getUserString(username):
    global operatorStats

    # Check if username statistics exists, and get it if they do not
    if username not in operatorStats.keys():
        get_player_stats(username)

    defenseName = getRandomOperator(username, 'def')
    attackName = getRandomOperator(username, 'atk')

    return "D: " + defenseName + ", A: " + attackName


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
                    returnMessage = ""
                    for user in users:
                        returnMessage = returnMessage + user + ": " + getUserString(user) + "<br />"

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
