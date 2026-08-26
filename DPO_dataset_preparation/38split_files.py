import json
import os

def split_json_file_by_lines(input_file, output_prefix, chunk_size=54):  # Split total of 37 samples into 4 parts, each with 344 lines; or 3 parts with 459 lines each
    with open(input_file, "r", encoding="utf-8") as fin:
        lines = [line.strip() for line in fin if line.strip()]
    
    total = len(lines)
    num_parts = (total + chunk_size - 1) // chunk_size  # Round up division

    for i in range(num_parts):
        part_lines = lines[i * chunk_size: (i + 1) * chunk_size]
        output_file = f"./02generate_diff_split_pre/train512_22837_randomSampled3970_0x01_3r_2646_{output_prefix}_part{i+1}.json"
        with open(output_file, "w", encoding="utf-8") as fout:
            for line in part_lines:
                fout.write(line + "\n")
        print(f"Wrote {output_file}, total {len(part_lines)} records")

# Need to copy to ./cot/cot_before/ directory
split_json_file_by_lines("train512_22837_randomSampled3970_0x01_3reasons_cleaned_updated_randomSampled2646_DelIndent.json", "split")
