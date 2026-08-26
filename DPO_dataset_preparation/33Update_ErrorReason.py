import json

def update_cleaned_json(cleaned_file, error_file, output_file):
    # Read the original cleaned file and the error correction file
    with open(cleaned_file, 'r', encoding='utf-8') as f:
        cleaned_data = json.load(f)
    with open(error_file, 'r', encoding='utf-8') as f:
        error_data = json.load(f)

    # Create a mapping from func_signature to element for easy updating
    signature_to_elem = {item["func_signature"]: item for item in cleaned_data}

    for error_elem in error_data:
        func_sig = error_elem.get("func_signature")
        output = int(error_elem.get("output", -1))
        if func_sig not in signature_to_elem:
            print(f"func_signature not found: {func_sig}, skipping this element")
            continue

        # Update the target element
        target = signature_to_elem[func_sig]
        if output == 1:
            # Vulnerable sample structure
            keys = ["AsUnsafe1", "AsUnsafe2", "AsSafe"]
        elif output == 0:
            # Non-vulnerable sample structure
            keys = ["AsSafe1", "AsSafe2", "AsUnsafe"]
        else:
            print(f"Invalid output value for func_signature: {func_sig}, skipping")
            continue

        for key in keys:
            if key in error_elem:
                target[key] = error_elem[key]
            else:
                print(f"{func_sig} missing field {key}, skipping this field")

    # Write the updated data to a new file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=4, ensure_ascii=False)

    print(f"Update complete, total {len(error_data)} records updated, results saved to {output_file}")

# Example call
update_cleaned_json(
    cleaned_file="train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_2nd.json",
    error_file="train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_error3.json",
    output_file="train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_3rd.json"
)
