nextbus
=======

`nextbus` lets you access the location, time, and schedule of every bus listed
on [nextbus.com](http://www.nextbus.com).

Usage
=====

```python
import nextbus

# get San Francisco MUNI
agency = [a for a in agencies() if a.tag == 'sf-muni'].pop()
agency = [a for a in NextBus().agencies() if a.tag == 'sf-muni'].pop()
agency.title        # San Francisco Muni

# get N line
route = [r for r in agency.routes if r.tag == 'N'].pop()
route.title       # 'N-Judah'

# get stops along the inbound direction
inbound     = [d for d in route.directions if d.name == 'Inbound'].pop()
first_stop  = inbound.stops[0]
first_stop.title               # Judah St & La Playa St
first_stop.lat, first_stop.lon # 37.7601699, -122.50878

# what time does the first inbound N bus leave?
schedule = [s for s in route.schedule if s.direction == 'Inbound'].pop()
schedule.stops[0].time   # datetime.time(5, 8)

# where are all inbound buses right now?
locations = [(b.lat, b.lon) for b in route.vehicle_locations
             if b.direction == inbound.tag]
```
