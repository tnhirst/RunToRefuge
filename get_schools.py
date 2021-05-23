import fiona
import re
import esy.osm.pbf
from shapely.geometry import Point, Polygon, shape
from shapely.ops import transform
import pyproj
from tqdm import tqdm

wgs84 = pyproj.CRS('EPSG:4326')
bng = pyproj.CRS('EPSG:27700')
to_bng = pyproj.Transformer.from_crs(wgs84, bng, always_xy=True).transform
to_wgs = pyproj.Transformer.from_crs(bng, wgs84, always_xy=True).transform


def extract_address(properties):
    address = ""
    if 'addr:housename' in properties:
        address += properties['addr:housename'] + ', '
    if 'addr:housenumber' in properties:
        address += properties['addr:housenumber'] + ' '
    if 'addr:street' in properties:
        address += properties['addr:street'] + ', '
    if 'addr:city' in properties:
        address += properties['addr:city'] + ', '
    if 'addr:postcode' in properties:
        address += properties['addr:postcode']
    else:
        address = address[:-1]
    return address


def extract_other_tags(properties):
    tags_string = properties['other_tags']
    tags = re.split(r',(?=")', tags_string)
    for tag in tags:
        elements = tag.split("=>")
        print(elements)


def parse_school(school_shape):
    properties = school_shape['properties']
    if 'other_tags' in school_shape['properties']:
        extract_other_tags(properties)
    return {
        'name': properties['name'],
        'address': extract_address(properties)
    }


def parse_school_from_osm(school_way, school_nodes):
    outline = transform(to_bng, Polygon([Point(n.lonlat)for n in school_nodes]))
    if 'name' not in school_way.tags:
        school_way.tags['name'] = "UNKNOWN"
    return {
        'name': school_way.tags['name'],
        'address': extract_address(school_way.tags),
        'centroid': transform(to_wgs, outline.centroid),
        'outline': outline
    }


fiona.drvsupport.supported_drivers['KML'] = 'rw'
with fiona.open('Full_Run_to_Refuge_Route.kml') as source:
    route = transform(to_bng, shape(next(iter(source))['geometry']))
osm = esy.osm.pbf.File('schools.osm.pbf')
nodes = [e for e in osm if isinstance(e, esy.osm.pbf.file.Node)]
ways = [e for e in osm if isinstance(e, esy.osm.pbf.file.Way)]
schools = []

with open('schools.csv', 'w', encoding="utf-8") as sink:
    sink.write("name,address,google_map,route_proximity\n")
    for way in tqdm(ways):
        school = parse_school_from_osm(way, [n for n in nodes if n.id in way.refs])
        sink.write(f""
                   f"\"{school['name']}\","
                   f"\"{school['address']}\","
                   f"\"https://www.google.com/maps/@{school['centroid'].y},{school['centroid'].x},16z\""
                   f",{school['outline'].distance(route)}\n")
