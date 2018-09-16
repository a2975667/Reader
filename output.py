import sys
from pprint import pprint
from datetime import datetime

NEWS_TEMPLATE = """  > [{Title}]({link}): {Notes}
  {Other_tags}

"""

SECTION_TEMPLATE = """-|{Major_tag}|---------
{stories}"""

SUCCESS_ID = []

def create_news(entry):
    n = NEWS_TEMPLATE
    n = n.replace('{Title}', entry['fields']['Title'])
    n = n.replace('{link}', entry['fields']['Url'])
    if 'Notes' in entry['fields']:
        n = n.replace('{Notes}', entry['fields']['Notes'])
    else:
        n = n.replace(': {Notes}\n', '')

    if 'Other Tags' in entry['fields']:
        string = '#' + ' #'.join(entry['fields']['Other Tags'])
        n = n.replace('{Other_tags}', string)
    else:
        n = n.replace('{Other_tags}', '')
    
    SUCCESS_ID.append(entry['id'])
    
    return n

def create_section(topic, string):
    s = SECTION_TEMPLATE
    s = s.replace('{Major_tag}', topic)
    s = s.replace('{stories}', string)
    return s

def cleanup(string):
    while ('\n\n\n' in string):
        string = string.replace('\n\n\n', '\n\n').strip()
    return string

def output(topics, data):
    full = ""
    for topic in topics:
        topic_string = ""
        
        for entry in data[topic]:
            n = create_news(entry)
            topic_string += n

        section_string = create_section(topic, topic_string)
        full += section_string

    final = """//肯恩的閱讀筆記//

{sections}
    """.replace('{sections}', full)

    date = datetime.today().strftime('%Y%m%d')
    name = 'results/'+ str(date) + '_reader.txt'
    with open(name, mode='w', encoding='utf-8') as f:
        f.write(cleanup(final))

    return SUCCESS_ID