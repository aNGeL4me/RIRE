import json
import os
def split_json_file_by_lines(input_file, output_prefix, chunk_size=160):
    with open(input_file, "r", encoding="utf-8") as fin:
        lines = [line.strip() for line in fin if line.strip()]
    
    total = len(lines)
    num_parts = (total + chunk_size - 1) // chunk_size

    for i in range(num_parts):
        part_lines = lines[i * chunk_size: (i + 1) * chunk_size]
        output_file = f"./01generate_3reaons_splited_pre/train_512_22837_randomSampled3970_0x01_{output_prefix}_part{i+1}.json"
        with open(output_file, "w", encoding="utf-8") as fout:
            for line in part_lines:
                fout.write(line + "\n")
        print(f"Wrote {len(part_lines)} lines to {output_file}")

# Needs to be copied to ./cot/cot_before/ directory
split_json_file_by_lines("train_512_22837_randomSampled3970_0x01_DelIndent.json", "split")
