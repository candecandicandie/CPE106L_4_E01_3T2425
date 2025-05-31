def main():
    filename = input("Enter the filename: ")
    
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print("File not found.")
        return

    total_lines = len(lines)
    print(f"\nFile '{filename}' loaded with {total_lines} lines.\n")

    while True:
        print(f"There are {total_lines} lines. Enter a line number (1 to {total_lines}), or 0 to quit.")
        try:
            line_number = int(input("Line number: "))
        except ValueError:
            print("Please enter a valid number.")
            continue

        if line_number == 0:
            print("Exiting program.")
            break
        elif 1 <= line_number <= total_lines:
            print(f"Line {line_number}: {lines[line_number - 1].rstrip()}\n")
        else:
            print(f"Invalid line number. Please enter a number between 1 and {total_lines}.\n")

if __name__ == "__main__":
    main()

import os
print("Current working directory:", os.getcwd())
