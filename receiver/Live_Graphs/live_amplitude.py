import serial
import time
import matplotlib.pyplot as plt
import csv
import statistics
from pathlib import Path


serial_connection = serial.Serial(
    "/dev/cu.usbserial-0001", 921600, timeout=0.1
)


elapsed_times = []
amplitude_values = []
rssi_values = []
rssi_spreads = []
quiet_scores = []
motion_threshold = None
last_presence_second = None
next_second = 0
starting_time = time.monotonic()

plt.ion()
graph_figure, graph_axes = plt.subplots()
graph_line = graph_axes.plot([], [])[0]
graph_axes.set_xlabel("Time (seconds)")
graph_axes.set_ylabel("Amplitude")

recording_file = open(
    Path(__file__).with_name(f"Live_Test_{int(time.time())}.csv"),
    "x",
    newline=""
)

csv_writer = csv.writer(recording_file)
csv_writer.writerow(["Time_seconds", "Measurement_number", "Amplitude", "RSSI"])

while plt.fignum_exists(graph_figure.number):
    while serial_connection.in_waiting > 0:
        received_line = serial_connection.readline().decode(errors="ignore")

        if received_line.startswith("Amplitude,") and received_line.endswith("\n"):
            signal_amplitude = float(received_line.split(",")[2])
            signal_rssi = int(received_line.split(",")[3])
            elapsed_times.append(time.monotonic() - starting_time)
            amplitude_values.append(signal_amplitude)
            rssi_values.append(signal_rssi)
            csv_writer.writerow([
                elapsed_times[-1],
                received_line.split(",")[1],
                signal_amplitude,
                signal_rssi
            ])

            
    elapsed_time = time.monotonic() - starting_time

    while next_second + 1 <= elapsed_time:
        second_rssi = []

        for index in range(len(elapsed_times)):
            if next_second <= elapsed_times[index] < next_second + 1:
                second_rssi.append(rssi_values[index])

        if len(second_rssi) >= 50:
            rssi_spreads.append(statistics.stdev(second_rssi))

            if len(rssi_spreads) >= 3:
                motion_score = sum(rssi_spreads[-3:]) / 3

                if 22 <= next_second < 50:
                    quiet_scores.append(motion_score)

                if next_second >= 50 and motion_threshold is None:
                    if len(quiet_scores) >= 20:
                        quiet_baseline = statistics.quantiles(
                            quiet_scores, n=20, method="inclusive"
                        )[-1]
                        motion_threshold = quiet_baseline + 0.35

                if next_second < 20:
                    graph_axes.set_title("Setup: leave the room")
                elif next_second < 50:
                    graph_axes.set_title("Calibrating: keep room empty")
                elif motion_threshold is None:
                    graph_axes.set_title("Calibration failed: restart")
                elif motion_score >= motion_threshold:
                    graph_axes.set_title("Movement")
                    last_presence_second = next_second
                elif motion_score > 0.2:
                    graph_axes.set_title("Still presence")
                    last_presence_second = next_second
                elif (
                    last_presence_second is not None
                    and next_second - last_presence_second < 10
                ):
                    graph_axes.set_title("Still presence")
                else:
                    graph_axes.set_title("Empty")
            else:
                graph_axes.set_title("Collecting 3 seconds of data")
        else:
            rssi_spreads.clear()
            graph_axes.set_title("Waiting for enough data")

        next_second += 1


    graph_line.set_data(elapsed_times, amplitude_values)
    graph_axes.relim()
    graph_axes.autoscale_view()

    if elapsed_times:
        latest_time = elapsed_times[-1]
        graph_axes.set_xlim(
            max(0, latest_time - 10),
            max(10, latest_time)
    )
    plt.pause(0.05)

serial_connection.close()
recording_file.close()
