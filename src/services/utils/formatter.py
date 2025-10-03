import ast
import base64
import json
import re


def contains_tags(input_string):
    # checking if the input string has any tag format in it
    tag_pattern = re.compile(r"<[^>]+>")
    match = tag_pattern.search(input_string)
    return bool(match)


def extract_text_from_tag(s: str, tag: str):
    start_tag = "<" + tag + ">"
    end_tag = "</" + tag + ">"
    start_index = s.find(start_tag)
    if start_index == -1:
        return s  # Tag not found, return string
    end_index = s.find(end_tag, start_index)
    if end_index == -1:
        return s  # End tag not found, return string
    return s[start_index + len(start_tag) : end_index]


def convert_to_percentage_list(float_list_str):
    # Handling where input is None
    if float_list_str is None:
        return []
    try:
        # Convert to array of strings with percentage values rounded to 2 decimal places
        float_str_list = ast.literal_eval(float_list_str)
        if float_str_list is None:
            return []
        percent_list = [f"{float(value) * 100:.2f}%" for value in float_str_list]
        return percent_list
    except (ValueError, SyntaxError):
        # Handle cases where ast.literal_eval fails
        return []


def append_text_to_urls(urls, text):
    if urls is None or urls.strip() == "":
        return []
    try:
        urls_list = ast.literal_eval(urls)
        if urls_list is None:
            return []
        url_str = str([url if "?" in url else url + "?" + text for url in urls_list])
        return url_str
    except (ValueError, SyntaxError):
        # Handle cases where ast.literal_eval fails
        return []


def formatter_string_to_list(string_list):
    # If the string starts and ends with square brackets, indicating a list
    if string_list.startswith("[") and string_list.endswith("]"):
        # Add quotes to elements if they are not enclosed in quotes
        modified_string_list = (
            "["
            + ",".join(
                f'"{x}"' if not x.startswith('"') else x
                for x in string_list[1:-1].split(",")
            )
            + "]"
        )
    else:
        # If it's already a valid list, just return it
        modified_string_list = string_list
    # Use ast.literal_eval to safely evaluate the string as a Python expression
    list_of_strings = ast.literal_eval(modified_string_list)
    return list_of_strings


def base64_encode_urls(url_string):
    # Convert the input string to a list of URLs safely
    urls = ast.literal_eval(url_string)
    # Encode each URL using Base64
    encoded_urls = [base64.urlsafe_b64encode(url.encode()).decode() for url in urls]
    return encoded_urls


def process_response(query, content, settings):
    answer = extract_text_from_tag(content, "a")
    sources = extract_text_from_tag(content, "sources")
    sources_format = formatter_string_to_list(sources)
    percentage = extract_text_from_tag(content, "percentage")
    percent_format = convert_to_percentage_list(percentage)
    filepath = extract_text_from_tag(content, "filepath")
    new_filepath = append_text_to_urls(filepath, f"{settings.demo_blob_sastoken}")
    encoded_urls = base64_encode_urls(new_filepath)
    recommended_questions = extract_text_from_tag(content, "recommended")

    return {
        "query": query,
        "answer": answer,
        "sources": sources_format,
        "percentage": percent_format,
        "filepath": encoded_urls,
        "recommended_questions": recommended_questions,
    }


def valid_schema_name(name):
    """
    Validate schema name to ensure it only contains alphanumeric characters and underscores.

    :param name: The schema name to validate.
    :return: True if valid, False otherwise.
    """
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", name))


def process_dollar_columns(df):
    # Identify columns that may contain dollar amounts
    dollar_columns = [
        col
        for col in df.columns
        if df[col].astype(str).str.contains(r"\$").any()
        or df[col].astype(str).str.contains(r"^-").any()
    ]

    # Process each dollar column
    for col in dollar_columns:
        try:
            # Function to format each value
            def format_value(value):
                # Check if the value is a string and contains a dollar sign
                if isinstance(value, str) and "$" in value:
                    # Remove dollar sign and commas, then convert to float
                    value = value.replace("$", "").replace(",", "")
                try:
                    value = float(value)
                except ValueError:
                    return value  # Return the original value if it cannot be converted

                # Apply formatting conditions
                if value < -100:
                    return f"-${int(abs(value)):,}"
                elif -100 <= value < 100:
                    return f"-${abs(value):,.2f}" if value < 0 else f"${value:,.2f}"
                else:
                    return f"${int(value):,}"

            # Apply the formatting function to each value in the column
            df[col] = df[col].apply(format_value)
        except Exception as e:
            print(f"Error processing column {col}: {e}")
            continue

    return df


def process_datetime_columns(data):
    data = json.loads(f"""{data}""")
    for key, value in data.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                if isinstance(subvalue, str) and "T00:00:00" in subvalue:
                    # Strip time part
                    data[key][subkey] = data[key][subkey].replace("T00:00:00", "")
    data = json.dumps(data)
    return data
