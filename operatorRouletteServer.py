from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import re
import json
import pickle
import os
import numpy as np

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


# This function returns the HTML for the given username
def getUserString(username):
    global operatorStats

    # Check if username statistics exists, and get it if they do not
    if username not in operatorStats.keys():
        get_player_stats(username)
    else:
        print(username + " already exists:")

        timeSumMin = 0.0
        timeSumMinInv = 0.0
        for operator in operatorStats[username]['operator_records']:
            timeSumMin = timeSumMin + (operator['stats']['playtime'] / 60)
            timeSumMinInv = timeSumMinInv + (1 / (operator['stats']['playtime'] / 60))
        print("Total played, {} min, inv: {}".format(timeSumMin, timeSumMinInv))

        selector = np.random.rand() * 100
        sumInv = 0
        for operator in operatorStats[username]['operator_records']:
            print(operator)
            operatorName = operator['operator']['name']
            operatorTimeMin = operator['stats']['playtime']/60
            operatorPercentage = 100 * (operatorTimeMin) / timeSumMin
            operatorTimeMinInv = 1 / (operator['stats']['playtime'] / 60)
            operatorPercentageInv = 100 * ((operatorTimeMinInv) / timeSumMinInv)
            sumInv = sumInv + operatorPercentageInv

            selector = selector - operatorPercentageInv
            if (selector < 0.0):
                return operatorName

            #np.random.rand()
            print("  Operator {}, playtime: {} min, percent: {}, invPercent: {}".format(operatorName, int(operatorTimeMin), operatorPercentage, operatorPercentageInv))

        print(sumInv)

    return "1"


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
