import os
import sys
from datetime import datetime, timedelta
from pprint import pprint

import dateutil.parser
import pytz
import requests
from airtable import Airtable
from dotenv import load_dotenv
from lxml.html import fromstring

from output import output


def update_entry(id, url):
    # safe check
    if url[:4] not in 'http':
        url = 'https://' + url
    
    # remove error url
    try: 
        r = requests.get(url)
    except requests.exceptions.ConnectionError:
        ERROR_LINKS.append(url)
        airtable.delete(id)
        return -1

    # check connection
    if r.status_code != 200:
        ERROR_LINKS.append(url)
    else:
        print(r.status_code)
        tree = fromstring(r.content)
        title = tree.findtext('.//title').strip()
        url = tinyurl(url)
        airtable.update(id, {'Title': title, 'Url': url})

def tinyurl(url):
    endpoint = 'http://tinyurl.com/api-create.php?url=' + url
    response = requests.get(endpoint)
    url = response.content.decode("utf-8")
    return url

def update_table(data):
    for entry in data:
        entry_data = entry['fields']
        entry_id = entry['id']

        if 'Url' not in entry_data:
            airtable.delete(entry_id)
            continue
        
        if 'Done' in entry_data:
            link_time = dateutil.parser.parse(entry_data['Datetime'])
            if (NOW - link_time) > timedelta(days=1) and entry_data['Done'] == 1:
                airtable.delete(entry_id)
                continue

        if entry_data['Title'] == 'Not Resolved':
            update_entry(entry['id'], entry['fields']['Url'])


def extract_selection(data):
    selected = []
    for entry in data:
        entry_data = entry['fields']
        entry_id = entry['id']
        if 'Done' not in entry_data:
            selected.append(entry)
        elif entry_data['Done'] != 1:
            selected.append(entry)
    return selected
    
def extract_report(data):
    topic_list = ['others']
    entry_dict = {'others':[]}

    # sorting topic into dicts
    for entry in data:
        entry_data = entry['fields']
        entry_id = entry['id']
        if 'Main Tag' in entry_data:
            if entry_data['Main Tag'] not in topic_list:
                topic = entry_data['Main Tag']
                topic_list.append(topic)
                entry_dict[topic] = [entry]
            else:
                entry_dict[topic].append(entry)
        else:
            entry_dict['others'].append(entry)
    
    # workaround
    topic_list = topic_list[::-1]

    # output to writefile
    success_id = output(topic_list, entry_dict)
    mark_done(success_id)


def mark_done(id_list):
    for id in id_list:
        airtable.update(id, {'Done': True})


if __name__ == '__main__':
    print('Reader Engine Started...')
    
    # Global Variables
    ERROR_LINKS = []
    NOW = datetime.utcnow().replace(tzinfo=pytz.UTC)
    load_dotenv()
    
    print('Setting Airtable Connection...')
    # Airtable Setup
    base_key = os.getenv("BASE_KEY")
    api_key = os.getenv("API_KEY")
    table_name = 'Reader'
    airtable = Airtable(base_key, table_name, api_key=api_key)
    
    print('Updating table...')
    update_table(airtable.get_all())
    print('Extracting Report...')
    selection = extract_selection(airtable.get_all())
    extract_report(selection)

    if len(ERROR_LINKS) > 0:
        with open('error.txt','w') as f:
            f.write("\n".join(ERROR_LINKS))
    
    print('Done.')
