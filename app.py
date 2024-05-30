"""
This file contains the IArgus app.
"""

import yaml
import json
import os

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
    
    try:
        api_token = os.environ["API_TOKEN"]
    except KeyError:
        print("No API token was set, asking for one right now...")
        token_request = {}
        with open("./config.yml") as config_file:
            config = yaml.safe_load(config_file)
            token_request["first_name"] = config["api"]["admin_first_name"]
            token_request["surname"] = config["api"]["admin_surname"]
            token_request["email"] = config["api"]["admin_email"]
            print(token_request)
        
        try:
            # verify is set to False for training purpose only as IArgus API
            # only has a self-signed SSL certificate
            response = requests.post(api_endpoint + "/get_token", json=token_request, verify=False)
            os.environ["API_TOKEN"] = response.json()["token"]
        
        except:
            message = "Price estimation is currently unavailable. Please try again later"
            return render_template('estimate_results.html', msg=message)


    form_data = request.form
    with open("./state_name_mapping.json") as state_map_file:
        mapping = json.load(state_map_file)
        state_code = mapping[form_data["state"]]
    features = {
        "state": state_code,
        "make": form_data["make"],
        "model": form_data["model"],
        "year": form_data["year"],
        "mileage": form_data["mileage"],
        "security_token": os.environ["API_TOKEN"]
    }

    # verify is set to False for training purpose only as IArgus API
    # only has a self-signed SSL certificate
    response = requests.post(api_endpoint + "/predict", json=features, verify=False)
    if response.status_code == 200:
        if "predicted_price" not in response.json():
            # If we arrive here, it means the price was not returned because our token is
            # not valid anymore, so we ask for a new one
            with open("./config.yml") as config_file:
                config = yaml.safe_load(config_file)
                token_request["first_name"] = config["api"]["admin_first_name"]
                token_request["surname"] = config["api"]["admin_surname"]
                token_request["email"] = config["api"]["admin_email"]
                response = requests.post(api_endpoint + "/get_token", json=token_request, verify=False)
                os.environ["API_TOKEN"] = response.json()["token"]

                features["security_token"] = os.environ["API_TOKEN"]
                response = requests.post(api_endpoint + "/predict", json=features, verify=False)

        price = round(response.json()['predicted_price'], 2)
        message = f"The best price for your car is ${price}!"
        

    else: 
        message = "It looks like something went wrong... Please try again later"
    return render_template('estimate_results.html', msg=message)
