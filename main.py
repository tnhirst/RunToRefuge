import fiona
from shapely.geometry import shape

fiona.drvsupport.supported_drivers['KML'] = 'rw'

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
            sink.write(f"{constituency['name']}\n")

