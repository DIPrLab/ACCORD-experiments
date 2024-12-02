from csv import reader
import random, math, json
import numpy as np
from datetime import datetime, timezone, timedelta
from src.detection import ConflictDetectionEngine
from scripts.expr_util import increase_selectivity, decrease_selectivity, actions_selected_by_ac, ALL_ACTIONS, PERMISSION_CHANGE_ACTION_TYPES, INITIAL_PERMISSION_LEVELS, FINAL_PERMISSION_LEVELS, CONSTRAINT_TYPES, PERMISSION_OPERATORS

# Parameters
log_file = "results/logs/activity-log_mock5freq40_2000actions_files4folders2_2024-10-19T02:26:54Z-2024-10-19T04:58:40Z.csv"
data_filename = "results/expr3/2024-11-30-17:36.csv"
constraints_filename_prefix = "results/expr3/constraints_2024-11-26"
level_names = ["high", "medium", "low"]
activity_counts = [400, 800, 1200, 1600, 2000, 2400, 2800, 3200, 3600, 4000]
num_constraints = 200
trials = 10

# Begin Experiment 3
random.seed()

data_file = open(data_filename, "w+")
data_file.write("log_file,activity_count,users,resources,selectivity_level,selectivity,construction_time_mean,construction_time_std,detection_time_mean,detection_time_std\n")

with open(log_file, "r") as csv_file:
    logs = list(reader(csv_file))[1:][::-1] # Skip header row & reverse to be chronological

constraints_data = {}
for count in activity_counts:
    with open(constraints_filename_prefix + "_" + str(count) + ".json", "r") as constraints_file:
        constraints_data[str(count)] = json.load(constraints_file)[str(count)]

for activity_count in activity_counts:
    logs_subset = logs[:activity_count]
    constraints_lists = constraints_data[str(activity_count)]

    for range_name in level_names:
        constraints_for_level = constraints_lists[range_name]

        print("activity count", activity_count, "selectivity level", range_name)
        constraints_obj = constraints_for_level[0]
        # Time detection algorithm
        print("detecting")
        constraints = constraints_obj["constraints"]

        raw_construction_times = []
        raw_detection_times = []
        for _ in range(trials):
            t0 = datetime.now()
            engine = ConflictDetectionEngine(constraints)
            t1 = datetime.now()
            result = engine.check_conflicts(logs_subset)
            t2 = datetime.now()
            construction_time = t1 - t0
            construction_time_ms = construction_time.seconds * 1000 + (construction_time.microseconds / 1000) # Ignore "days" property
            raw_construction_times.append(construction_time_ms)
            detection_time = t2 - t1
            detection_time_ms = detection_time.seconds * 1000 + (detection_time.microseconds / 1000) # Ignore "days" property
            raw_detection_times.append(detection_time_ms)

        raw_total_times = [i + j for i, j in zip(raw_construction_times, raw_detection_times)]
        print(raw_total_times, raw_construction_times, raw_detection_times)
        for _ in range(2):
            mindex = 0
            for i, elem in enumerate(raw_total_times):
                if elem < raw_total_times[mindex]:
                    mindex = i
            raw_total_times.pop(mindex)
            raw_detection_times.pop(mindex)
            raw_construction_times.pop(mindex)
            maxdex = 0
            for i, elem in enumerate(raw_total_times):
                if elem > raw_total_times[maxdex]:
                    maxdex = i
            raw_total_times.pop(maxdex)
            raw_detection_times.pop(maxdex)
            raw_construction_times.pop(maxdex)

        raw_construction_times = np.array(raw_construction_times)
        raw_detection_times = np.array(raw_detection_times)
        print("done")

        dtimes = np.array(raw_detection_times)
        dmean = dtimes.mean()
        dstd = dtimes.std()
        ctimes = np.array(raw_construction_times)
        cmean = ctimes.mean()
        cstd = ctimes.std()
        users = str(constraints_obj["users"])
        resources = str(constraints_obj["resources"])
        selectivity = str(constraints_obj["selectivity"])

        data_line = ",".join([log_file, str(activity_count), users, resources, range_name, selectivity, str(cmean), str(cstd), str(dmean), str(dstd)])
        data_file.write(data_line + "\n")

data_file.close()
