import json
import csv
import os
import shutil
import uuid
import configparser
from datetime import datetime

# Generate a unique process ID
process_id = str(uuid.uuid4())

def flatten_json(json_object, parent_key='', separator='.'):
    """
    Recursively flattens a nested JSON object.

    Args:
        json_object (dict): The JSON object to flatten.
        parent_key (str): The base key for nested keys.
        separator (str): The separator for nested keys.

    Returns:
        dict: A flattened dictionary.
    """
    items = []
    for k, v in json_object.items():
        new_key = f"{parent_key}{separator}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, separator=separator).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                items.extend(flatten_json(
                    item, f"{new_key}[{i}]", separator=separator).items())
        else:
            items.append((new_key, v))
    return dict(items)


def append_flattened_to_csv(data, filename, numero_control):
    """
    Appends flattened data to a CSV file.

    Args:
        data (dict): The flattened data to append.
        filename (str): The path to the CSV file.
        numero_control (str): The control number to include in the record.
    """
    file_exists = os.path.exists(filename)
    keys = set(data.keys())
    keys.add("numeroControl")
    keys.add("processID")

    with open(filename, 'a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=sorted(keys))
        if not file_exists:
            writer.writeheader()
        data["numeroControl"] = numero_control
        data["processID"] = process_id
        writer.writerow(data)


def update_control_file(control_file, process_id, start_date, end_date, status):
    """
    Updates the control CSV file with process details.

    Args:
        control_file (str): The path to the control CSV file.
        process_id (str): The unique process ID.
        start_date (str): The start timestamp of the process.
        end_date (str): The end timestamp of the process.
        status (str): The status of the process (e.g., "Success" or "Failed").
    """
    file_exists = os.path.exists(control_file)
    with open(control_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(
            file, fieldnames=["processID", "start_date", "end_date", "status"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "processID": process_id,
            "start_date": start_date,
            "end_date": end_date,
            "status": status
        })


def process_files_in_folder(input_folder, output_folder, processed_folder):
    """
    Processes JSON files in the input folder, converts them to CSV, and moves them to the processed folder.

    Args:
        input_folder (str): The folder containing input JSON files.
        output_folder (str): The folder to save the output CSV files.
        processed_folder (str): The folder to move processed JSON files.
    """
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(processed_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.endswith('.json'):
            file_path = os.path.join(input_folder, filename)

            with open(file_path, 'r', encoding='utf-8-sig') as file:
                json_data = json.load(file)

            numero_control = json_data.get(
                "identificacion", {}).get("numeroControl", "N/A")

            for key, value in json_data.items():
                output_file = os.path.join(output_folder, f"{key}.csv")
                if isinstance(value, dict):
                    flattened = flatten_json(value)
                    append_flattened_to_csv(
                        flattened, output_file, numero_control)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            flattened = flatten_json(item)
                            append_flattened_to_csv(
                                flattened, output_file, numero_control)
                        else:
                            append_flattened_to_csv(
                                {key: item}, output_file, numero_control)
                else:
                    append_flattened_to_csv(
                        {key: value}, output_file, numero_control)

                if key == "cuerpo documento":
                    append_flattened_to_csv({}, output_file, numero_control)

            processed_path = os.path.join(processed_folder, filename)
            shutil.move(file_path, processed_path)
            print(f"Processed and moved file: {filename}")


def main():
    """
    Main function to read configuration, process files, and update the control file.
    """
    config = configparser.ConfigParser()
    config.read('config.ini')

    input_folder = config.get('Folders', 'input_folder', fallback='files/fc')
    output_folder = config.get(
        'Folders', 'output_folder', fallback='files/fc/output_csv')
    processed_folder = config.get(
        'Folders', 'processed_folder', fallback='files/fc/processed')
    control_file = config.get(
        'Folders', 'control_file', fallback='files/fc/output_csv/control.csv')

    start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        process_files_in_folder(input_folder, output_folder, processed_folder)
        status = "Success"
    except Exception as e:
        print(f"Error during processing: {e}")
        status = "Failed"

    end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    update_control_file(control_file, process_id, start_date, end_date, status)


if __name__ == "__main__":
    main()
