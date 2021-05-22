from pprint import pprint

import fiona
from shapely.geometry import shape
import requests
import json

fiona.drvsupport.supported_drivers['KML'] = 'rw'

with open('config.json') as config_file:
    config = json.load(config_file)


def get_mp(constituency):
    mp = requests.get(
        f"https://www.theyworkforyou.com/api/getMP?"
        f"constituency={constituency['name']}&"
        f"output=js&"
        f"key={config['TWFY_key']}")\
        .json()
    details = requests.get(
        f"https://www.theyworkforyou.com/api/getMPInfo?"
        f"id={mp['person_id']}&"
        f"output=js&"
        f"key={config['TWFY_key']}")\
        .json()
    return {
               'full_name': mp['full_name'],
               'twitter': f"https://twitter.com/{details['twitter_username']}" if details and 'twitter_username' in details else 'None',
               'website': details['mp_website'] if details and 'mp_website' in details else 'None',
               'facebook': details['facebook_page'] if details and 'facebook_page' in details else 'None'}


if __name__ == '__main__':
    with fiona.open('Full_Run_to_Refuge_Route.kml') as source:
        route = shape(next(iter(source))['geometry'])
    with fiona.open('constituencies/Westminster_Parliamentary_Constituencies_(December_2015)_Boundaries.shp') as source:
        constituencies = []
        for item in source:
            constituency = {
                'id': item['properties']['pcon15cd'],
                'name': item['properties']['pcon15nm'],
                'shape': shape(item['geometry'])
            }
            if route.intersects(constituency['shape']):
                constituencies.append(constituency)
    with open('output.csv', 'w') as sink:
        for constituency in constituencies:
            mp = get_mp(constituency)
            sink.write(
                f"{constituency['id']},"
                f"\"{constituency['name']}\","
                f"\"{mp['full_name']}\","
                f"{mp['twitter']},"
                f"{mp['website']},"
                f"{mp['facebook']}\n")


