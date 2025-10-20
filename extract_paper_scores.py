import csv
import sys
import re
from collections import defaultdict

def analyze_csv(input_filepath):
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

            for i, column_name in enumerate(header):
                if column_name == "ID":
                    id_index = i
                elif column_name == 'Pscore':
                    p_score_index = i
                elif column_name == 'Decision':
                    decision_index = i
                elif re.match(r'S\d+score', column_name):
                    pc_columns.append(i)
                elif re.match(r'E\d+score', column_name):
                    reviewer_columns.append(i)

            if id_index == -1:
                print("Error: The CSV file must contain an 'ID' column.", file=sys.stderr)
                return
            if p_score_index == -1:
                print("Error: The CSV file must contain an 'Pscore' column.", file=sys.stderr)
                return
            if decision_index == -1:
                print("Error: The CSV file must contain a 'Decision' column.", file=sys.stderr)
                return

            # Write the results to standard output
            writer = csv.writer(sys.stdout)
            writer.writerow([
                'ID', 
                'Pscore', 
            ])

            # Process each row of the CSV file
            for row in reader:
                # Check the Decision column before processing the row
                decision_value = row[decision_index].strip()
                if decision_value not in ["RER", "ERER"]:
                    continue  # Skip this row if the decision is not RER or ERER

                row_array = [row[id_index], row[p_score_index],]
                
                for i in pc_columns:
                    score = row[i]
                    if re.match(r'\d+\.\d+', score):
                        row_array.append(score)
                    
                for i in reviewer_columns:
                    score = row[i]
                    if re.match(r'\d+\.\d+', score):
                        row_array.append(score)

                writer.writerow(row_array)

    except FileNotFoundError:
        print(f"Error: The file at '{input_filepath}' was not found.", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_csv.py <input_file_path.csv>", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    analyze_csv(input_path)
