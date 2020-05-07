import urllib.request
import json
import time

def get_items_metrics():
    url = urllib.request.urlopen('http://127.0.0.1:8080/rest/items?recursive=false&fields=name,state,type')
    content_bytes = url.read()
    content = content_bytes.decode('utf-8')

    url.close()

    obj = json.loads(content)
    ts = int(round(time.time() * 1000))

    numbers = [ item for item in obj if item['type'].lower() == 'number' ]
    dimmers = [ item for item in obj if item['type'].lower() == 'dimmer' ]
    switches = [ item for item in obj if item['type'].lower() == 'switch' ]
    contacts = [ item for item in obj if item['type'].lower() == 'contact' ]

    res = ''
    res = res + print_metrics(numbers, 'number', ts)
    res = res + print_metrics(dimmers, 'dimmer', ts)
    res = res + print_metrics(switches, 'switch', ts)
    res = res + print_metrics(contacts, 'contact', ts)

    return res


def get_things_metrics():
    url = urllib.request.urlopen('http://127.0.0.1:8080/rest/things?recursive=false')
    content_bytes = url.read()
    content = content_bytes.decode('utf-8')

    url.close()

    obj = json.loads(content)
    ts = int(round(time.time() * 1000))

    return print_metrics(obj, 'thing', ts)


def print_metrics(metrics, type, timestamp):
    metric_name = 'openhab2_metric_' + type

    res = '# TYPE {} gauge\n'.format(metric_name)

    if type != 'thing':
        for metric in metrics:
            name = metric['name']
            value = metric['state']

            if value is None or value == 'NULL':
                continue

            if metric['type'].lower() == 'switch':
                value = 1 if value == 'ON' else 0
            elif metric['type'].lower() == 'contact':
                value = 1 if value == 'OPEN' else 0

            res = res + metric_name + '{name="' + name + '"} ' + '{} {}\n'.format(value, timestamp)

    else:
        for metric in metrics:
            label = metric['label']
            uid = metric['UID']
            status = metric['statusInfo']['status']
            statusDetail = metric['statusInfo']['statusDetail']
            value = 6

            if metric['status'].upper() == 'ONLINE':
                value = 0
            elif metric['status'].upper() == 'OFFLINE':
                value = 1
            elif metric['status'].upper() == 'UNINITIALIZED':
                value = 2
            elif metric['status'].upper() == 'INITIALIZING':
                value = 3
            elif metric['status'].upper() == 'REMOVING':
                value = 4
            elif metric['status'].upper() == 'REMOVED':
                value = 5
            else:
                value = 6

            if status is None or status == 'NULL':
                continue

            res = res + metric_name + '{label="' + label + '", statusDetail="' + statusDetail + '", uid="' + uid + '", status="' + status + '"} ' + '{} {}\n'.format(value, timestamp)

    return res


def app(environ, start_response):
    """
    Entrypoint for gunicorn
    """
    items_metrics = get_items_metrics()
    data = items_metrics.encode('utf-8')
    things_metrics = get_things_metrics()
    data = data + things_metrics.encode('utf-8')

    start_response('200 OK', [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(data)))
        ])

    return iter([data])
