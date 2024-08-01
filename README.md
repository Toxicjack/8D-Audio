# 8D Audio Processor

This repository contains the 8D Audio Processor project.

## Download and Reassemble the ZIP File

Due to file size limitations, the ZIP file has been split into smaller parts. Follow these steps to reassemble and extract the files:

### On Windows

1. Download all the split parts (`part1.zip`, `part2.zip`, etc.).
2. Use 7-Zip to reassemble and extract the files:
   - Right-click on the first part (`part1.zip`).
   - Select `7-Zip` > `Extract here`.

### On Mac/Linux

1. Download all the split parts (`part1.zip`, `part2.zip`, etc.).
2. Open a terminal and navigate to the directory containing the split parts.
3. Run the following command to reassemble and extract the files:
   ```sh
   cat part*.zip > combined.zip
   unzip combined.zip
