import json

def check_reason_field_endings(file_path, error_output_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    errors = []

    for elem in data:
        output = elem.get("output", "").strip()
        output = int(output) if output.isdigit() else -1  # Prevent errors from non-numeric values

        def check_endswith(key, expected_suffix):
            value = elem.get(key, "")
            return value.strip().endswith(expected_suffix)

        if output == 1:
            valid = (
                check_endswith("AsSafe", "Result: [Secure]") and
                check_endswith("AsUnsafe1", "Result: [Vulnerable]") and
                check_endswith("AsUnsafe2", "Result: [Vulnerable]")
            )
        elif output == 0:
            valid = (
                check_endswith("AsUnsafe", "Result: [Vulnerable]") and
                check_endswith("AsSafe1", "Result: [Secure]") and
                check_endswith("AsSafe2", "Result: [Secure]")
            )
        else:
            valid = False  # Invalid output value

        if not valid:
            errors.append(elem)

    # Write error samples to error.json
    with open(error_output_path, 'w', encoding='utf-8') as f:
        json.dump(errors, f, indent=4, ensure_ascii=False)

    print(f"Processing completed, found {len(errors)} formatting error samples, saved to {error_output_path}")

# Example usage
check_reason_field_endings(
    file_path='train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_1st.json',
    error_output_path='train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_error2.json'
)
