#!/usr/bin/env python3
import yaml
import aws_cdk as cdk

from appsec_workshop.appsec_workshop_stack import AppsecWorkshopStack

with open("./config.yaml") as stream:
    config = yaml.safe_load(stream)

app = cdk.App()
AppsecWorkshopStack(app, "AppSecWorkshopStack", config)

app.synth()
