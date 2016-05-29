#!/usb/bin/python
# coding: utf-8
import requests
import json
import datetime
import time
# fromPlace: "Pasilan asema",
# from: {lat: 60.198959, lon: 24.934948},
# toPlace: "Itäkeskus",

URL = "https://api.digitransit.fi/routing/v1/routers/hsl/index/graphql"
Q_ITINERARY = """
{
  plan(
    from: {lat: 60.198959, lon: 24.934948},
    to: {lat: 60.207197, lon: 25.084257},
    modes: "BUS,WALK",
    walkReluctance: 2.1,
    walkBoardCost: 600,
    minTransferTime: 180,
    walkSpeed: 1.2,
  ) {
    itineraries{
      walkDistance,
      duration,
      legs {
        trip {
          gtfsId
          id
            pattern {
              id
            }
        }
        mode
        startTime
        endTime
        realTime
        route{
          shortName
        },
        from {
          lat
          lon
          name
          stop {
            gtfsId
            code
            name
          }
        },
        to {
          lat
          lon
          name
        },
        agency {
          id
        },
        distance
        legGeometry {
          length
          points
        }
      }
    }
  }
}
"""

Q_ARRIVAL = """
{
  stop(id: "%s") {
    id
    gtfsId
    name
    direction
    desc
    platformCode
    patterns {
      route {
        shortName
      }
    }
    stoptimesWithoutPatterns(numberOfDepartures: 5) {
      trip {
        gtfsId
      }
      realtimeArrival
      scheduledArrival
    }
  }
}
"""

HEADERS = {"Content-Type": "application/graphql", "Accept": "application/json; charset=UTF-8"}

USER_LEAD_TIME_SECONDS = 2 * 60

def planTrip():
    response = requests.post(URL, data=Q_ITINERARY, headers=HEADERS)
    # print response.headers
    # print response.text
    response_json = json.loads(response.text)
    # print json.dumps(response_json, indent=2)
    # print response_json
    walkToStopSeconds = 0
    # TODO: Check if user can catch the bus for the itinerary chosen here
    print "Got %d itineraries" % len(response_json[u'data'][u'plan'][u'itineraries'])
    for itinerary in response_json[u'data'][u'plan'][u'itineraries']:
        for leg in itinerary[u'legs']:
            # print json.dumps(leg, indent=2)
            if leg[u'mode'] == 'WALK':
                walkToStopSeconds = (leg[u'endTime'] - leg[u'startTime']) / 1000
                # print 'Walk to stop: %d' % walkToStopSeconds
            if leg[u'mode'] == 'BUS':
                stopId = leg[u'from'][u'stop'][u'gtfsId']
                tripId = leg[u'trip'][u'gtfsId']
                busNumber = leg[u'route'][u'shortName']
                # print stopId
                # print tripId
                if canCatchBus(stopId, tripId, busNumber, walkToStopSeconds)[0]:
                    return stopId, tripId, busNumber, walkToStopSeconds
                else:
                    break
    # print len(response_json[u'data'][u'plan'][u'itineraries'])


def canCatchBus(stopId, tripId, busNumber, walkTime):
    query = Q_ARRIVAL % stopId
    response = requests.post(URL, data=query, headers=HEADERS)
    response_json = json.loads(response.text)
    foundTrip = False
    for connection in response_json[u'data'][u'stop'][u'stoptimesWithoutPatterns']:
        # print trip[u'trip'][u'gtfsId']
        if tripId == connection[u'trip'][u'gtfsId']:
            foundTrip = True
            # print "Arriving at %s" % str(datetime.timedelta(seconds=connection[u'realtimeArrival']))
            now = datetime.datetime.now()
            seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
            realtimeArrival = connection[u'realtimeArrival']
            timeLeft = realtimeArrival - seconds_since_midnight
            if connection[u'realtimeArrival'] > (seconds_since_midnight + USER_LEAD_TIME_SECONDS + walkTime):
                print "User can make it to bus %s arriving at %s. Time left: %d. Need %d" % (busNumber, str(datetime.timedelta(seconds=realtimeArrival)), timeLeft, USER_LEAD_TIME_SECONDS + walkTime)
                return True, connection[u'realtimeArrival'], connection[u'scheduledArrival']
            else:
                print "Trip %s too close! Would need %d seconds but only %d left." % (tripId, USER_LEAD_TIME_SECONDS + walkTime, timeLeft)
    if not foundTrip:
        print "Trip gone from list!"
    return False, -1, -1


def writeConnectionToJson(stopId, tripId, busNumber, walkTime, connectionArrival, scheduledArrival):
    with open('connection.json', 'w') as connfile:
        data = {}
        data['stopId'] = stopId
        data['tripId'] = tripId
        data['busNumber'] = busNumber
        data['walkTime'] = walkTime
        data['leadTime'] = USER_LEAD_TIME_SECONDS
        data['connectionArrival'] = connectionArrival
        data['scheduledArrival'] = scheduledArrival
        connfile.write(json.dumps(data))


def loopCanCatchBus(stopId, tripId, busNumber, walkTime):
    while True:
        ok, arrival, scheduledArrival = canCatchBus(stopId, tripId, busNumber, walkTime)
        yield ok, arrival, scheduledArrival
        if not ok:
            break

if __name__ == "__main__":
    while True:
        stopId, tripId, busNumber, walkTime = planTrip()
        if stopId is None:
            print "No itinerary found!"
        # print tripId
        for ok, arrival, scheduledArrival in loopCanCatchBus(stopId, tripId, busNumber, walkTime):
            if ok:
                writeConnectionToJson(stopId, tripId, busNumber, walkTime, arrival, scheduledArrival)
                time.sleep(10)

