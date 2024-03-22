"""
This file contains the IArgus app.
"""

import yaml
import json

import requests

from flask import Flask, render_template, request, flash


app = Flask(__name__)

with open("./config.yml") as config_file:
    config = yaml.safe_load(config_file)
    api_endpoint = config["api"]["prediction_endpoint"]

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/contact")
def contact():
    return render_template('contact.html')

@app.route("/estimate_results", methods = ['POST'])
def prediction_results():
    # Récupérer le contenu du formulaire
    # Appeler l'API
    # Afficher la valeur renvoyée OU un message d'erreur
    form_data = request.form
    with open("./state_name_mapping.json") as state_map_file:
        mapping = json.load(state_map_file)
        state_code = mapping[form_data["state"]]
    features = {
        "state": state_code,
        "make": form_data["make"],
        "model": form_data["model"],
        "year": form_data["year"],
        "mileage": form_data["mileage"]
    }

    # verify is set to False for training purpose only as IArgus API
    # only has a self-signed SSL certificate
    response = requests.post(api_endpoint, json=features, verify=False)
    if response.status_code == 200:
        price = round(response.json()['predicted_price'], 2)
        message = f"The best price for your car is ${price}!"
    else: 
        message = "It looks like something went wrong... Please try again later"
    print(response.status_code)
    print(response.json())
    return render_template('estimate_results.html', msg=message)
