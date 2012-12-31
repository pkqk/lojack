import sys
import webbrowser
import datetime
import time
import csv

import httplib2
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage


def timestamp_ms(dt):
    return 1000 * time.mktime(dt.timetuple())


def fromtimestamp(timestamp_ms):
    return datetime.datetime.fromtimestamp(timestamp_ms/1000.0)


def latitude_service():
    http = httplib2.Http()
    storage = Storage('auth.json')
    flow = flow_from_clientsecrets('client.json',
        scope='https://www.googleapis.com/auth/latitude.all.best',
        redirect_uri='http://pkqk.net/auth/latitude')


    credentials = storage.get()
    if credentials is None or credentials.invalid:
        webbrowser.open(flow.step1_get_authorize_url(), new=1, autoraise=True)
        code = raw_input('Enter verification code: ').strip()
        credentials = flow.step2_exchange(code, http=http)
        storage.put(credentials)
        credentials.set_store(storage)

    http = credentials.authorize(http)
    service = build("latitude", "v1", http=http)
    return service


def history(api=latitude_service()):
    kwargs = {'max_results': 100, 'granularity': 'best'}
    items = api.location().list(**kwargs).execute().get('items', [])
    while items:
        for item in items:
            min_time = int(item['timestampMs'])
            yield item
        min_time -= 1  # one microsecond to stop duplicates
        items = api.location().list(max_time=min_time, **kwargs).execute().get('items', [])


if __name__ == "__main__":
    api = latitude_service()
    out = csv.writer(sys.stdout)
    out.writerow(("datetime", "timestamp_ms", "latitude", "longitude"))
    for point in history():
        dt = fromtimestamp(int(point['timestampMs']))
        data = [point[key] for key in ('timestampMs', 'latitude', 'longitude')]
        out.writerow([dt.isoformat()] + data)
