import datetime
import re
import xml.etree.ElementTree as ET

from configurati import attrs
import requests


WEBSERVICES = 'http://webservices.nextbus.com/service/publicXMLFeed'


class NextBus(object):

  def __init__(self):
    self.agency = None
    self.route  = None
    self.time   = None

  def vehicle_locations(self, agency, route, time=0):
    return _fetch_xml({
      'command': 'vehicleLocations',
      'a': agency,
      'r': route,
      't': _epoch(time),
    })

  def schedule(self, agency, route):
    return _fetch_xml({
      'command': 'schedule',
      'a': agency,
      'r': route,
    })

  def routes(self, agency):
    return _fetch_xml({
      'command': 'routeList',
      'a': agency,
    })

  def stops(self, agency, route):
    return _fetch_xml({
      'command': 'routeConfig',
      'a': agency,
      'r': route,
    })

  def agencies(self):
    return _fetch_xml({
      'command': 'agencyList',
    })


def agencies():
  result = NextBus().agencies()
  return [Agency(**e.attrs) for e in result if e.tag == 'agency']


class Agency(object):
  def __init__(self, tag, title, regionTitle, shortTitle=None, **kwargs):
    self.tag          = str(tag)
    self.title        = str(title)
    self.short_title  = str(shortTitle or title)
    self.region_title = str(regionTitle)

  @property
  def routes(self):
    result = _fetch_xml({
      'command': 'routeList',
      'a': self.tag,
    })
    return [Route(agency=self.tag, **e.attrs) for e in result if e.tag == 'route']

  def __str__(self):
    return "Agency: %s" % self.title
  def __repr__(self):
    return "Agency(tag=%s, title=%s, regionTitle=%s, shortTitle=%s)" % \
        (self.tag, self.title, self.region_title, self.short_title)


class Route(object):
  def __init__(self, agency, tag, title, shortTitle=None, **kwargs):
    self.agency      = str(agency)
    self.tag         = str(tag)
    self.title       = str(title)
    self.short_title = str(shortTitle or title)

  @property
  def directions(self):
    result = _fetch_xml({
      'command': 'routeConfig',
      'a': self.agency,
      'r': self.tag,
    })
    stops = [Stop(route=self.tag, **e.attrs) for e in result[0].children
             if e.tag == 'stop']
    stops = { stop.tag: stop for stop in stops }

    directions = []
    for direction in filter(lambda x: x.tag == 'direction', result[0].children):
      directions.append(Direction(
        route=self.tag,
        stops=[stops[str(e.attrs.tag)] for e in direction.children],
        **direction.attrs
      ))

    return directions

  @property
  def stops(self):
    result = _fetch_xml({
      'command': 'routeConfig',
      'a': self.agency,
      'r': self.tag,
    })
    stops = [Stop(route=self.tag, **e.attrs) for e in result[0].children
             if e.tag == 'stop']
    return stops

  @property
  def schedule(self):
    result = _fetch_xml({
      'command': 'schedule',
      'a': self.agency,
      'r': self.tag,
    })
    result = result.pop(0)

    stops = { stop.tag: stop for stop in self.stops }

    runs = []
    for run in [e for e in result.children if e.tag == 'tr']:
      run_ = []
      for stop in run.children:
        if stop.text == '--':
          time = None
        else:
          hour, minute, second = stop.text.split(":")
          time = datetime.time(int(hour), int(minute), int(second))

        run_.append(attrs({
          'stop': stops[str(stop.attrs.tag)],
          'time': time
        }))
      runs.append(Run(
        route=self.tag,
        stops=run_,
        scheduleClass=result.attrs.scheduleClass,
        serviceClass=result.attrs.serviceClass,
        direction=result.attrs.direction,
        **run.attrs
      ))

    return runs

  def __str__(self):
    return "Route: %s" % self.title

  def __repr__(self):
    return "Route(agency=%s, tag=%s, title=%s, shortTitle=%s)" % \
        (self.agency, self.tag, self.title, self.short_title)


class Run(object):
  def __init__(self, route, stops, scheduleClass, serviceClass, direction, blockID, **kwargs):
    self.route          = route
    self.stops          = stops
    self.schedule_class = scheduleClass
    self.service_class  = serviceClass
    self.direction      = direction
    self.block_id       = blockID

  def __str__(self):
    return "Run: %s heading %s at %s" % (self.route, self.direction, self.stops[0].time)

  def __repr__(self):
    return "Run(route=%s, stops=%s, scheduleClass=%s, serviceClass=%s, direction=%s, blockId=%s)" % \
        (self.route, map(repr, self.stops), self.schedule_class, self.service_class, self.direction, self.block_id)


class Direction(object):
  def __init__(self, route, stops, tag, title, name, **kwargs):
    self.route = str(route)
    self.stops = stops
    self.tag   = str(tag)
    self.title = str(title)
    self.name  = str(name)

  def __str__(self):
    return "Direction: %s on %s" % (self.name, self.route)

  def __repr__(self):
    return "Direction(route=%s, stops=%s, tag=%s, title=%s, name=%s)" % \
        (self.route, [repr(stop) for stop in self.stops], self.tag, self.title, self.name)


class Stop(object):
  def __init__(self, route, tag, title, lat, lon, stopId=None, shortTitle=None, **kwargs):
    self.route       = str(route)
    self.tag         = str(tag)
    self.title       = str(title)
    self.lat         = float(lat)
    self.lon         = float(lon)
    self.short_title = str(shortTitle or title)
    self.stop_id     = str(stopId)

  def __str__(self):
    return "Stop: %s on %s" % (self.title, self.tag)

  def __repr__(self):
    return "Stop(route=%s, tag=%s, title=%s, lat=%s, lon=%s, stopId=%s, title=%s)" % \
        (self.route, self.tag, self.title, self.lat, self.lon, self.stop_id, self.short_title)


def _fetch_xml(args):
  """Download XML, convert to attributes dictionary"""
  response = requests.get(WEBSERVICES, params=args)
  xml = ET.fromstring(response.text)
  return _xml2attrs(xml).children


def _xml2attrs(elem):
  """Convert XML to attributes dictionary"""

  def convert(v):
    if re.search('^-?\d+[.]\d+$', v):
      return float(v)
    elif re.search('^-?\d+$', v):
      return int(v)
    elif v == 'true':
      return True
    elif v == 'false':
      return False
    else:
      return v

  result = attrs({
    'tag': elem.tag,
    'attrs': attrs({ k: convert(v) for (k, v) in elem.attrib.items() }),
  })

  if len(elem.getchildren()) > 0:
    result.children = [_xml2attrs(child) for child in elem.getchildren()]
  if elem.text:
    result.text = elem.text

  return result


def _epoch(time):
  """milliseconds since _epoch"""
  _epoch = datetime.utcfromtimestamp(0)
  delta = dt - _epoch
  return int(delta.total_seconds() * 1000)


if __name__ == '__main__':
  agencies   = agencies()
  routes     = agencies[0].routes
  directions = routes[0].directions
  stops      = routes[0].stops
  schedule   = routes[0].schedule
