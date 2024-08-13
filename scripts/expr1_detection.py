import sys
from csv import DictReader

if len(sys.argv) < 2:
    print("Usage: scripts/expr1_detection.py <log file>")

log_file = sys.argv[1]
with open(log_file, "r") as csv_file:
    activities = list(DictReader(csv_file))

print(activities)