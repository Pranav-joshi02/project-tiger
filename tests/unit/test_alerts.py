from alerts.engine import generate_alerts
def test_buffer_event(): assert generate_alerts({"buffer_entry":True})[0]["type"]=="buffer_entry"
