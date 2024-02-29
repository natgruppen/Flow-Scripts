#!/usr/bin/env python3

from flow import Flow
from pprint import pprint
from dateutil import parser
import datetime
import argparse

def _findSite(site):
    sites = Flow.httpList('inventory/pop', searchItems={ 'name': site})['data']
    
    if len(sites) == 1:
        return sites[0]
    
    print(f"No or more than one site found for {site}")
    quit()

def _removeLabels(labels,address):
    for label in Flow.httpList('address/address/label', address['id'])['data']:
        if label['labelName'] in labels:
            print(f"Remove label {label['labelName']} from {address['id']}")
            Flow.httpDelete('address/address/label', { "label_id": label['label_id'] }, address['id'])

def _terminateAgreements(terminationDate,address):
    for agreement in Flow.httpList('address/address/agreement', address['id'])['data']:
        if 'endDate' in agreement:
            if parser.parse(agreement['endDate']).replace(tzinfo=None) > terminationDate.replace(tzinfo=None):
                print(f"Agreement terminates too late {agreement['id']} {agreement['endDate']}. Terminate job needs to be removed manually and the script run again.")
        else:
            print(f"Terminate agreement {agreement['id']}")
            agreementOperation = {
                "agreement_id": agreement['id'],
                "type": "REMOVE",
                "date": terminationDate.strftime("%Y-%m-%dT23:59:00+0100")
            }
            resp = Flow.httpCreate('catalogue/operation/create', agreementOperation, agreement['id'])
            if not resp['success']:
                print(f"Unable to remove agreement {agreement['id']}, maybe not active yet?")
            

parser = argparse.ArgumentParser(description='Avslutar abonnemang och tar bort labels Published och Blocked på adresser')
parser.add_argument('--site', metavar='site', type=str, nargs="+", help="Site som adresser är kopplade till", required=True)
parser.add_argument('--terminationDate', metavar='terminationDate', type=datetime.date.fromisoformat, help="Datum som abonnemang ska avslutas", required=True)
parser.add_argument('--population', type=str, help="Hantera bara adresser med population")

args = parser.parse_args()

for site in args.site:
    _site = _findSite(site)
    
    for _device in Flow.httpList('inventory/pop/device', objectId=_site['id'])['data']:
        for _port in Flow.httpList('inventory/device/port', objectId=_device['id'])['data']:
            for _outlet in Flow.httpList('inventory/port/outlets', objectId=_port['id'])['data']:
                _address = Flow.httpOpen('address/address', objectId=_outlet['address_id'])['data']
                if _address['attributes']['population'] != args.population and args.population != None:
                    continue
                _removeLabels(['Blocked','Published'], _address)
                _terminateAgreements(args.terminationDate, _address)