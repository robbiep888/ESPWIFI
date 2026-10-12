# ESPWIFI: ESP32 Wi-Fi Motion Detection

A two-ESP32 motion-detection prototype with RSSI processing, CSI amplitude logging, and a live Python graph. It was tested with a sender in a bedroom and a fixed receiver in the adjoining bathroom, separated by a wall.

The current detector uses **RSSI variation** to estimate movement. It also provides **experimental presence estimates** from smaller fluctuations and a 10-second hold. CSI amplitude is recorded and plotted, but does not drive the current classification. Processing runs on the connected computer.

## How it works

1. The sender broadcasts ESP-NOW packets on Wi-Fi channel 11, targeting one packet every 10 milliseconds.
2. The receiver accepts CSI measurements from the configured sender address. It calculates amplitude from one CSI subcarrier and outputs that amplitude together with RSSI over USB serial at 921600 baud.
3. Python measures the sample standard deviation of RSSI in each complete one-second window. A valid window needs at least 50 readings.
4. The **motion score** is the average of the latest three one-second standard deviations.
5. After 20 seconds of setup, the next 30 seconds are used for empty-room calibration. The motion cutoff is the 95th percentile of the calibration scores plus **0.35**.

After calibration, the rules are:

| Label | Rule |
| --- | --- |
| Movement | Score at or above the calibrated motion cutoff |
| Still presence | Score above 0.2 and below the motion cutoff, or activity detected within the last 10 seconds |
| Empty | Score at or below 0.2, with the presence hold expired |

Movement takes priority. Both Movement and Still presence detections reset the hold timer. Missing or insufficient measurements produce a waiting message instead of an occupancy estimate.

## Hardware and software

- Two ESP32 development boards, configured as `esp32dev`.
- USB connections for firmware upload; the receiver remains connected to the computer during detection.
- Power for the sender during testing.
- PlatformIO with the ESP-IDF framework. Both projects pin `espressif32@6.12.0`.
- Python and the packages in `requirements.txt`. The development environment used Python 3.14.7.

Both boards must use the same channel and matching sender address. These settings are defined near the top of their respective `src/main.c` files.

## Setup and run

Run the following Python setup commands from the project root on macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Upload firmware

Use PlatformIO's Upload task for each project. With the PlatformIO CLI available, connect only the board being uploaded and run:

```bash
# Connect the sender board first.
pio run --project-dir sender --target upload

# Disconnect the sender from the computer and connect the receiver board.
pio run --project-dir receiver --target upload
```

PlatformIO detects the upload port automatically. If needed, list devices with `pio device list` and supply the appropriate `--upload-port`. See the [PlatformIO command documentation](https://docs.platformio.org/en/latest/core/userguide/cmd_run.html).

Power the sender again before starting detection. Keep the receiver in its fixed testing position and connected by USB.

### Start the live detector

List serial ports:

```bash
python -m serial.tools.list_ports
```

Set the receiver's port in `receiver/Live_Graphs/live_amplitude.py`. The development setup used `/dev/cu.usbserial-0001`; another computer may use a different port. Keep the baud rate at 921600.

Close the PlatformIO serial monitor and any other program reading that port, then run:

```bash
python receiver/Live_Graphs/live_amplitude.py
```

- **0–20 seconds:** leave the room and finish setup.
- **20–50 seconds:** keep the room empty and remain stationary away from the setup for calibration.
- **After calibration:** test movement and quiet periods without moving either board.

The graph shows **CSI amplitude**. Its title displays the **RSSI-based detection result**. Close the graph window to finish recording and close the serial connection.

Each run creates a new `Live_Test_<timestamp>.csv` beside the Python script, containing:

```text
Time_seconds,Measurement_number,Amplitude,RSSI
```

Time is measured on the computer. RSSI is recorded in dBm; CSI amplitude is in arbitrary units. Existing recordings are not overwritten.

## Recorded test results

One controlled main-script trial on October 12, 2026 used an empty room, continuous walking, and a mostly-still person. Five seconds at the start of each activity section were excluded for transitions. The motion cutoff was approximately **0.526**.

| Actual activity | Scored recording times | Matching predictions | Label agreement |
| --- | --- | --- | --- |
| Empty room | 55–80 seconds | 25/25 Empty | 100% |
| Continuous walking | 95–120 seconds | 25/25 Movement | 100% |
| Mostly still, present | 125–150 seconds | 7/25 Still presence | 28% |
| Overall | These three sections | 57/75 | 76% |

The mostly-still section also contained 18 Empty predictions. The presence hold expired while the person remained in the room.

Source: [saved recording](receiver/Live_Graphs/Live_Test_1791841317.csv). The recording also includes setup and the return to the computer, which are excluded from these results.

These are overlapping once-per-second decisions from **one recording in one fixed layout**, not independent experiments or accuracy across different rooms. Other development recordings showed variation in both the empty-room baseline and movement detection.

## Limitations and next steps

- Presence estimation is experimental. A still person can produce steady RSSI and be labeled Empty. Breathing detection has not been established.
- A 10-second hold remembers recent detections; it does not prove continuous occupancy and can delay an Empty label after someone leaves.
- Movement near the setup, including outside the target room, may affect the signal. The detector does not locate the source of activity.
- Filtering packets by sender address does not remove RF interference.
- Both boards remain fixed during measurement. Handheld operation and receiver-motion compensation have not been tested.
- Future work includes using several CSI subcarriers, comparing CSI and RSSI features, and testing additional layouts and recordings.

## Project files

- `sender/`: ESP-NOW transmitter firmware and PlatformIO configuration.
- `receiver/`: CSI/RSSI receiver firmware and PlatformIO configuration.
- `receiver/Live_Graphs/live_amplitude.py`: main live graph, detector, and recorder.
- `receiver/Live_Graphs/csv_calcs.py`: earlier signal-processing and CSV analysis experiments.
- `receiver/Live_Graphs/ML_DT_processing.py`: earlier decision-tree experiment; the current live detector uses thresholds instead.
- `receiver/Live_Graphs/*.csv`: development recordings, including the documented trial.

## Attribution

Sender and receiver firmware were adapted from the `csi_send` and `csi_recv` examples in [Espressif ESP-CSI](https://github.com/espressif/esp-csi). The original source attribution headers and Apache-2.0 license files are retained in [sender/LICENSE](sender/LICENSE) and [receiver/LICENSE](receiver/LICENSE).
