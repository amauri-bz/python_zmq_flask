#!/usr/bin/env python
# encoding: utf-8

from zmq_topology import Interface
from flask import Flask, render_template, request

"""
A Python-Flask web page to request information from the ZMQ topology by a REQ/REP interface.
"""
class HtmlPage(object):
    app = Flask(__name__, template_folder='.')

    @app.route('/', methods = ['POST', 'GET'])
    def result():
      if request.method == 'POST':
          #REQ/REP interface to access information from the ZMQ topology
          s1 = Interface('Intf1', "5555")
          ret = s1.run()
          return render_template("result.html",result = ret)
      return render_template("index.html")

def IntfTest():
    h1 = HtmlPage()
    h1.app.run(debug = True, host='0.0.0.0', port=8080)

if __name__ == "__main__":
    IntfTest()
