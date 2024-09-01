log_string = """



"""


# Split the multiline string into an array (list) of lines and filter out lines with "error"
log_array = [line for line in log_string.strip().splitlines() if "error" not in line.lower()]

# Extract messages safely
for line in log_array:
    parts = line.split(": ", 1)
    if len(parts) > 1:
        message = parts[1]
        print(message)
    # else:
        # print("No message found")