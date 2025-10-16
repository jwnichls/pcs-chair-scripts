import csv
import sys
import re
from collections import defaultdict

def analyze_csv(input_filepath):
    """
    Analyzes a CSV file to count reviews remaining by the secondary and
    external reviewers.

    Args:
        input_filepath (str): The path to the input CSV file.
    """
    try:
        # Dictionary to store the count for each unique Pname
        # The key is the Pname, the value is the count of rows with < 2 confirmed reviewers
        external_review_counts = defaultdict(int)
        pc_review_counts = defaultdict(int)
        external_total_review_counts = defaultdict(int)
        pc_total_review_counts = defaultdict(int)
        total_processed_rows = 0

        with open(input_filepath, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            header = next(reader)  # Read the header row

            # Find the indices of Pname, Decision, and all E<number>name/E<number>score columns
            decision_index = -1
            pc_columns = [] # A list of tuples: (name_index, score_index)
            reviewer_columns = [] # A list of tuples: (name_index, score_index)

            for i, column_name in enumerate(header):
                if column_name == 'Decision':
                    decision_index = i
                elif re.match(r'S\d+name', column_name):
                    # Extract the number from the column name (e.g., 'E1name' -> '1')
                    number = re.search(r'S(\d+)name', column_name).group(1)
                    score_column = f'S{number}score'
                    try:
                        score_index = header.index(score_column)
                        pc_columns.append((i, score_index))
                    except ValueError:
                        # Skip if the corresponding score column is not found
                        continue
                elif re.match(r'E\d+name', column_name):
                    # Extract the number from the column name (e.g., 'E1name' -> '1')
                    number = re.search(r'E(\d+)name', column_name).group(1)
                    score_column = f'E{number}score'
                    try:
                        score_index = header.index(score_column)
                        reviewer_columns.append((i, score_index))
                    except ValueError:
                        # Skip if the corresponding score column is not found
                        continue

            if decision_index == -1:
                print("Error: The CSV file must contain a 'Decision' column.", file=sys.stderr)
                return

            # Process each row of the CSV file
            for row in reader:

                # Check the Decision column before processing the row
                decision_value = row[decision_index].strip()
                if decision_value not in ["RER", "ERER"]:
                    continue  # Skip this row if the decision is not RER or ERER

                # Iterate through all identified reviewer columns to count confirmed reviewers
                for name_idx, score_idx in reviewer_columns:
                    # Check if the name field is not empty and the score field does not contain "T"
                    r_name = row[name_idx].strip()
                    if (r_name != ''):
                        score = row[score_idx].strip()
                        
                        if r_name not in external_review_counts:
                            external_review_counts[r_name] = 0
                            external_total_review_counts[r_name] = 1
                        elif ('T' != score):
                            external_total_review_counts[r_name] += 1
                                                    
                        if re.match(r'\d+\.\d+', score):
                            external_review_counts[r_name] += 1

                # Iterate through all PC columns to count completed pc reviews
                for name_idx, score_idx in pc_columns:
                    # Check if the name field is not empty and the score field does not contain "T"
                    r_name = row[name_idx].strip()
                    if (r_name != ''):
                        score = row[score_idx].strip()
                        
                        if r_name not in pc_review_counts:
                            pc_review_counts[r_name] = 0
                            pc_total_review_counts[r_name] = 1
                        else:
                            pc_total_review_counts[r_name] += 1
                            
                        if re.match(r'\d+\.\d+', score):
                            pc_review_counts[r_name] += 1

        # Write the results to standard output
        writer = csv.writer(sys.stdout)
        writer.writerow([
            'Reviewer', 
            'PC?', 
            'Reviews Completed', 
            'Total Reviews Assigned',
        ])
        for r_name, count in sorted(pc_review_counts.items()):
            writer.writerow([
                r_name,
                "true",
                count,
                pc_total_review_counts[r_name],
            ])
        for r_name, count in sorted(external_review_counts.items()):
            writer.writerow([
                r_name,
                "false",
                count,
                external_total_review_counts[r_name],
            ])

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
