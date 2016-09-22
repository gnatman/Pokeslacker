'''
This is a simple example for running a simple Slack bot that will
respond to user summons, query the requested information from an
outside source, and provide a formatted response to the user.
'''


import json

from flask import Flask, request, Response
import requests
from slackclient import SlackClient


# If you can use a credentials file, this would be how to load it in
# with open('credentials.json', 'r') as f:
#     data = json.read(f)
# SLACK_DEV_TOKEN = data['slack_dev_token']
# SLACK_WEBHOOK_TOKEN = data['webhook_token']

SLACK_DEV_TOKEN = <SLACK TOKEN>  # Put your API dev token here
SLACK_WEBHOOK_TOKEN = <WEBHOOK TOKEN>  # Put your webhook token here

slack_client = SlackClient(SLACK_DEV_TOKEN)


def extract_types(json_in, relation):
    # relation can be something like double_damage_to
    # to find what type it is super effective against
    types_list = [t['name'] for t in json_in['damage_relations'][relation]]
    # Check that the query produced an output
    if len(types_list) > 0:
        return types_list
    else:
        return ['None']


def get_relations(input_type):
    # Perform an HTTP GET request,
    # grab the text portion of the response.
    url = 'http://pokeapi.co/api/v2/type/{}/'.format(input_type)
    requests_text = requests.get(url).text
    # Load the GET request text into a Python dictionary.
    json_returned = json.loads(requests_text)
    # Pull out all the relevant information to report to the user.
    half_damage_from = extract_types(json_returned, 'half_damage_to')
    no_damage_from = extract_types(json_returned, 'no_damage_from')
    double_damage_from = extract_types(json_returned, 'double_damage_from')
    half_damage_to = extract_types(json_returned, 'half_damage_to')
    double_damage_to = extract_types(json_returned, 'double_damage_to')
    no_damage_to = extract_types(json_returned, 'no_damage_to')

    # Format the output in the return statement.
    outstring = '\n'.join(['{0} is super effective against: {1}',
                           '{0} is not very effective against: {2}',
                           '{0} is weak to: {3}',
                           '{0} is resistant to: {4}',
                           '{0} takes no damage from: {5}',
                           '{0} deals no damage to: {6}'])

    return outstring.format(input_type,
                            ', '.join(double_damage_to),
                            ', '.join(half_damage_to),
                            ', '.join(double_damage_from),
                            ', '.join(half_damage_from),
                            ', '.join(no_damage_from),
                            ', '.join(no_damage_to))


pokemon_types = ['bug', 'dark', 'dragon', 'electric', 'fairy', 'fighting',
                 'fire', 'flying', 'ghost', 'grass', 'ground', 'ice', 'normal',
                 'poison', 'psychic', 'rock', 'steel', 'water']

cached_dictionary = {}
for type_to_cache in pokemon_types:
    cached_dictionary[type_to_cache] = get_relations(type_to_cache)
    # Status update because it could seem like nothing's happening
    print('{} added to cache.'.format(type_to_cache))
print('Caching completed.')

app = Flask(__name__)


# A simple function to handle posting the message
def send_message(channel_id, message):
    slack_client.api_call('chat.postMessage',
                          channel=channel_id,
                          text=message,
                          username='PokeSlacker',
                          icon_emoji=':joystick:')


# This is the server listening for posts to the root directory
@app.route('/', methods=['POST'])
def inbound():
    # if statement ensures outside sources won't spam the channel
    if request.form.get('token') == SLACK_WEBHOOK_TOKEN:
        # Channel the request came from
        channel_id = request.form.get('channel_id')
        # Text sent by the user
        input_text = request.form.get('text').lower()
        # Using a dictionary get, we can also handle errors elegantly
        message = cached_dictionary.get(
            input_text,
            'Type {} not found, please try again.'.format(input_text)
        )
        send_message(channel_id, message)
        return Response(), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0')
