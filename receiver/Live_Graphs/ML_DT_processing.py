from pathlib import Path

import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text


# CSV files live beside this script. The original files are only read.
recording_folder = Path(__file__).resolve().parent
training_rows = []
test_rows = []

# 1. Read the four recordings for each condition.
for file_prefix in ["Empty", "Still", "Moving"]:
    if file_prefix == "Empty":
        correct_state = "Empty"
    else:
        correct_state = "Occupied"

    for test_number in [1, 2, 3, 4]:
        file_name = f"{file_prefix}_Test{test_number}.csv"
        recording = pd.read_csv(recording_folder / file_name)

        # The same three-reading median filter used in csv_calcs.py.
        recording["Filtered_amplitude"] = (
            recording["Amplitude"]
            .rolling(window=3, center=True, min_periods=1)
            .median()
        )

        # The first empty test had an uncertain extra setup second.
        if file_prefix == "Empty" and test_number == 1:
            start_second = 21
        else:
            start_second = 20

        # 2. Make one row of measurements for each usable second.
        for second in range(start_second, start_second + 60):
            window = recording[
                (recording["Time_seconds"] >= second)
                & (recording["Time_seconds"] < second + 1)
            ]
            amplitudes = window["Filtered_amplitude"]

            row = {
                "File": file_name,
                "Second": second,
                "Correct_state": correct_state,
                "Average_amplitude": amplitudes.mean(),
                "Spread": amplitudes.std(),
                "Average_change": amplitudes.diff().abs().mean(),
            }

            # Keep each entire file in either training or testing.
            if test_number == 4:
                test_rows.append(row)
            else:
                training_rows.append(row)


training_data = pd.DataFrame(training_rows)
test_data = pd.DataFrame(test_rows)

# File names, times, and correct answers are NOT inputs to the tree.
input_columns = ["Average_amplitude", "Spread", "Average_change"]

# 3. Learn a small tree. Each final branch needs at least 20 examples.
# Balanced weights give Empty and Occupied equal importance.
tree = DecisionTreeClassifier(
    max_depth=3,
    min_samples_leaf=20,
    class_weight="balanced",
    random_state=0,
)
tree.fit(training_data[input_columns], training_data["Correct_state"])

print("Training: tests 1, 2, and 3 for each condition.")
print("Testing: test 4 for each condition, excluded from training.")
print("\nLearned rules:")
print(export_text(tree, feature_names=input_columns, decimals=3))

# 4. Predict the state of the held-out recordings.
test_data["Predicted_state"] = tree.predict(test_data[input_columns])

print("Results on the held-out recordings:")
for file_name in test_data["File"].unique():
    recording_results = test_data[test_data["File"] == file_name]
    correct_predictions = (
        recording_results["Predicted_state"] == recording_results["Correct_state"]
    ).sum()

    print(f"\n{file_name}: {correct_predictions}/{len(recording_results)} correct")
    print(recording_results["Predicted_state"].value_counts().to_string())

print("\nThese are one-second decisions from three test recordings.")
print("Validate the learned rules on new recordings before using them live.")
