from prometheus_client import Gauge

EVENTS_IN_PROGRESS = Gauge('events_in_progress', 'Number of events in progress')
