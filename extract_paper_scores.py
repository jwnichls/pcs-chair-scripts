import csv
import sys
import re
from collections import defaultdict

def analyze_csv(input_filepath, time_zone_data):
    """
    Analyzes a CSV file to extract the paper ID and scores.
    This file can then be imported into another spreadsheet
    for analysis.

    Args:
        input_filepath (str): The path to the input CSV file.
    """
    try:
        total_processed_rows = 0

        with open(input_filepath, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            header = next(reader)  # Read the header row

            # Find the indices of Pname, Decision, and all E<number>name/E<number>score columns
            id_index = -1
            p_score_index = -1
            decision_index = -1
            pc_columns = [] # A list of tuples: (name_index, score_index)
            reviewer_columns = [] # A list of tuples: (name_index, score_index)
            meta_recommendation_column = -1
            recommendation_columns = []
            discuss_columns = []
            name_columns = []

            decision_map = {
                "A": "6.0",
                "MnR": "5.0",
                "MnMaR": "4.0",
                "MaR": "3.0",
                "RMa": "2.0",
                "R": "1.0",                
            }

            for i, column_name in enumerate(header):
                if column_name == "ID":
                    id_index = i
                elif column_name == 'Pscore':
                    p_score_index = i
                elif column_name == 'Decision':
                    decision_index = i
                elif column_name == 'PReviewer Recommendation':
                    meta_recommendation_column = i
                elif re.match(r'S\d+score', column_name):
                    pc_columns.append(i)
                elif re.match(r'E\d+score', column_name):
                    reviewer_columns.append(i)
                elif re.match(r'\w\d+Reviewer Recommendation', column_name):
                    recommendation_columns.append(i)
                elif re.match(r'\w[\d]?Discuss at PC Meeting', column_name):
                    discuss_columns.append(i)
                elif re.match(r'\w[\d]?name', column_name):
                    name_columns.append(i)

            if id_index == -1:
                print("Error: The CSV file must contain an 'ID' column.", file=sys.stderr)
                return
            if p_score_index == -1:
                print("Error: The CSV file must contain an 'Pscore' column.", file=sys.stderr)
                return
            if decision_index == -1:
                print("Error: The CSV file must contain a 'Decision' column.", file=sys.stderr)
                return
            if meta_recommendation_column == -1:
                print("Error: The CSV file must contain a meta reviewer recommendation column.", file=sys.stderr)
                return

            # Write the results to standard output
            writer = csv.writer(sys.stdout)
            writer.writerow([
                'ID',
                'Locations',
                'Discuss',
                'Decision',
                'Pscore',
                '',
                '',
                '',
                '',
                'Precommendation',
            ])

            # Process each row of the CSV file
            for row in reader:
                # Check the Decision column before processing the row
                decision_value = row[decision_index].strip()
                if decision_value not in ["RER", "ERER", "A-N", "Minor-N", "Major-N", "R-N", "T"]:
                    continue  # Skip this row if the decision is not RER or ERER

                if decision_value == "RER" or decision_value == "T":
                    decision_value = ""

                location_intersection = set()
                if row[name_columns[0]] in time_zone_data:
                    location_intersection = set(time_zone_data[row[name_columns[0]]])

                for i in name_columns[1:]:
                    if row[i] in time_zone_data:
                        location_intersection = set(time_zone_data[row[i]]) & location_intersection
                locations = list(location_intersection)
                locations.sort()

                discuss_flag = False
                for i in discuss_columns:
                    if row[i] == "Discuss":
                        discuss_flag = True
                        break

                row_array = [row[id_index], locations, discuss_flag, decision_value, row[p_score_index],]
                
                for i in pc_columns:
                    score = row[i]
                    if re.match(r'\d+\.\d+', score):
                        row_array.append(score)
                    
                for i in reviewer_columns:
                    score = row[i]
                    if re.match(r'\d+\.\d+', score):
                        row_array.append(score)

                while len(row_array) < 9:
                    row_array.append("")

                row_array.append(row[meta_recommendation_column])
                    
                for i in recommendation_columns:
                    if row[i] != "":
                        row_array.append(row[i]) 

                while len(row_array) < 14:
                    row_array.append("")

                if row[meta_recommendation_column] != "":
                    row_array.append(decision_map[row[meta_recommendation_column]])
                else:
                    row_array.append('')

                for i in recommendation_columns:
                    if row[i] != "":
                        row_array.append(decision_map[row[i]])

                writer.writerow(row_array)

    except FileNotFoundError:
        print(f"Error: The file at '{input_filepath}' was not found.", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)


def extract_time_zone_data(file_path):
    """
    Opens a CSV file, iterates through each row, and creates a dictionary.

    The dictionary uses the content of the 'Name' column as keys.
    The values are a list combining the contents of the 'Asia', 'Europe', 
    and 'US' columns for that row.

    Args:
        file_path: The path to the CSV file.

    Returns:
        A dictionary mapping Name (str) to a list of values 
        (List[Any]) from the other three columns.
    """
    result_dict = {}
    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
            # Use DictReader to access columns by header name
            reader = csv.DictReader(csvfile)

            # Check if required columns exist
            required_columns = ['Name', 'Slots available']
            if not all(col in reader.fieldnames for col in required_columns):
                raise ValueError(
                    f"CSV file must contain the following columns: {required_columns}"
                )

            for row in reader:
                name = row['Name']
                slots_available = list(map(str.strip, row['Slots available'].split(',')))
                
                # Assign the list as the value for the 'Name' key
                result_dict[name] = slots_available

    except FileNotFoundError:
        print(f"Error: File not found at path: {file_path}")
        return {}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}

    return result_dict


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python extract_paper_scores.py <submissions_file_path.csv> [<time_zone_file_path.csv>]", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    
    time_zone_data = {}
    if len(sys.argv) > 2:
        time_zone_path = sys.argv[2]
        time_zone_data = extract_time_zone_data(time_zone_path)
    
    analyze_csv(input_path, time_zone_data)
