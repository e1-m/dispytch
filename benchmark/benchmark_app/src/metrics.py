from prometheus_client import Gauge, Histogram, Counter

EVENTS_IN_PROGRESS = Gauge('events_in_progress', 'Number of events in progress')

PROCESSING_LATENCY = Histogram(
    'processing_latency_seconds',
    'Time spent processing a single message',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

EVENT_PROCESSED_TOTAL = Counter(
    'event_processed_total',
    'Total number of events processed'
)
