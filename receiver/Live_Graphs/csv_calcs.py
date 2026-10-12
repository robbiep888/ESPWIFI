import csv
import os
import pandas as pd
import matplotlib.pyplot as plt



#Run1:
#Moving1 Avg: 28.581786492374725    Spread: 2.1260292869563657
#Still1 Avg:  28.098397521768252    Spread: 2.0380423468738
#Empty1 Avg:  24.581052189964762    Spread: 1.9284670370318968




recorded_moving_measurements = pd.read_csv(
    "/Users/bert/ESPWIFI/receiver/Live_Graphs/Moving_Test1.csv"
)

recorded_still_measurements = pd.read_csv(
    "/Users/bert/ESPWIFI/receiver/Live_Graphs/Still_Test1.csv"
)

recorded_empty_measurements = pd.read_csv(
    "/Users/bert/ESPWIFI/receiver/Live_Graphs/Empty_Test1.csv"
)


recorded_all_measurements = pd.read_csv(
    "/Users/bert/ESPWIFI/receiver/Live_Graphs/Allmovement_Test1.csv"
)





# Finding large amplitude noise
large_amplitude_reading = recorded_empty_measurements[
    recorded_empty_measurements["Amplitude"] > 60
]
print(large_amplitude_reading[["Time_seconds", "Amplitude"]])

print("================================================================================================================================================================================")






# Record accurate data between 20 and 80 seconds
clean_measurements = recorded_empty_measurements[
    (recorded_empty_measurements["Time_seconds"] >= 20) & (recorded_empty_measurements["Time_seconds"] <= 80)
]

print("Average", clean_measurements["Amplitude"].mean())
print("Spread", clean_measurements["Amplitude"].std())


print("============================================================================================================")


for second in range(20, 80):
    window = recorded_moving_measurements[
        (recorded_moving_measurements["Time_seconds"] >= second)
        & (recorded_moving_measurements["Time_seconds"] < second + 1)
    ]

    average = window["Amplitude"].mean()
    spread = window["Amplitude"].std()

    print(second, average, spread)

print("============================================================================================================")

for second in range(20, 80):
    window = recorded_still_measurements[
        (recorded_still_measurements["Time_seconds"] >= second)
        & (recorded_still_measurements["Time_seconds"] < second + 1)
    ]

    average = window["Amplitude"].mean()
    spread = window["Amplitude"].std()

    print(second, average, spread)

print("============================================================================================================")

for second in range(20, 80):
    window = recorded_empty_measurements[
        (recorded_empty_measurements["Time_seconds"] >= second)
        & (recorded_empty_measurements["Time_seconds"] < second + 1)
    ]

    average = window["Amplitude"].mean()
    spread = window["Amplitude"].std()

    print(second, average, spread)

print("============================================================================================================")




recorded_all_measurements["Filtered_amplitude"] = (
    recorded_all_measurements["Amplitude"]
    .rolling(window=3, center=True, min_periods=1)
    .median()
)

large_readings = recorded_all_measurements[
    recorded_all_measurements["Amplitude"] > 60
]

print(large_readings[
    ["Time_seconds", "Amplitude", "Filtered_amplitude"]
])

print("============================================================================================================")


window_seconds = []
filtered_spreads = []

for second in range(20, 240):
    window = recorded_all_measurements[
        (recorded_all_measurements["Time_seconds"] >= second)
        & (recorded_all_measurements["Time_seconds"] < second + 1)
    ]

    raw_spread = window["Amplitude"].std()
    filtered_spread = window["Filtered_amplitude"].std()

    window_seconds.append(second)
    filtered_spreads.append(filtered_spread)

    if len(filtered_spreads) >= 3:
        detection_score = sum(filtered_spreads[-3:]) / 3

        if detection_score >= 1.05:
            print(second, detection_score, "Possible presence")
        else:
            print(second, detection_score, "Quiet")

    print(second, raw_spread, filtered_spread)


plt.plot(window_seconds, filtered_spreads)
plt.xlabel("Time (seconds)")
plt.ylabel("Filtered spread")
plt.show()