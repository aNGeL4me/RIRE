import json
import os
import re

def remove_leading_space(s):
    return s[1:] if s.startswith(' ') else s

def deduplicate_changes(final_changes):
    seen = set()
    unique_changes = []
    
    for change in final_changes:

        del_hash = change["deletions"].strip()
        add_hash = change["additions"].strip()
        identifier = (del_hash, add_hash)
        
        if identifier not in seen:
            seen.add(identifier)
            unique_changes.append(change)
    
    return unique_changes

def parse_patch_context(patch):
        hunks = []
        current_hunk = None
        lines = patch.split('\n')
        
        for i, line in enumerate(lines):
            if line.startswith('@@'):
                if current_hunk:
                    hunks.append(current_hunk)
                header = line.split('@@')[1].strip()
                src_range = re.search(r'-\d+,\d+', header).group()
                tgt_range = re.search(r'\+\d+,\d+', header).group()
                current_hunk = {
                    'src_start': int(src_range[1:].split(',')[0]),
                    'tgt_start': int(tgt_range[1:].split(',')[0]),
                    'lines': []
                }
            elif current_hunk:
                current_hunk['lines'].append((i, line))
        if current_hunk:
            hunks.append(current_hunk)
        return hunks

def process_changes_deletionsANDadditions(changes):
    for change in changes:
        if not change.get("deletions") and change.get("context_line_del"):
            change["context_line_del"] = ""
        if not change.get("additions") and change.get("context_line_add"):
            change["context_line_add"] = ""

    return changes

def build_additions_context_map(patch_hunks):
    additions_context_map = {}
    current_addition_block = []
    next_line_content = None

    for hunk in patch_hunks:
        lines = hunk['lines']
        for i in range(len(lines)):
            line_info = lines[i]
            line_num, line = line_info

            if line.startswith('+'):
                current_addition_block.append(line[1:]) 
            
                if i + 1 < len(lines):
                    next_line_info = lines[i + 1]
                    next_line_num, next_line = next_line_info
                    if not next_line.startswith('+'):
                        next_line_content = next_line
            else:
                if current_addition_block:
                    key = "\n".join(current_addition_block)
                    additions_context_map[key] = next_line_content
                    current_addition_block = []
                    next_line_content = None
    if current_addition_block:
        key = "\n".join(current_addition_block)#.strip()
        additions_context_map[key] = next_line_content

    return additions_context_map

def update_final_changes(final_changes, func_modified_block, func):
    updated_changes = []

    for change in final_changes:
        deletions = change.get("deletions", "")
        additions = change.get("additions", "").replace("\n", "\n+")
        context_line_add = change.get("context_line_add", "")
        context_line_add_strip = context_line_add.strip() 
        flag = True
        flag_ModifiedBlock_PreviousTextNotInFunc_FllowingTextInFunc = check_change(change, func, func_modified_block)
        # https://github.com/FFmpeg/FFmpeg/commit/e7b9d136a1ba2d048b1a17df5778e426b825676d

        #print(f"context_line_add --> {context_line_add}\nadditions --> {additions}")
        if (not deletions and additions) and context_line_add_strip in ["{", "}"]:
            code_segment = f"{context_line_add}\n+{additions}"
            #print(f"code_segment 1 --> {code_segment}")
            match = re.search(re.escape(code_segment), func_modified_block)
            #print(f"1st match --> {match}")
            if not match:
                code_segment = f"{context_line_add}\n \n+{additions}"
                #print(f"code_segment 2 --> {code_segment}")
                match = re.search(re.escape(code_segment), func_modified_block)
            #print(f"2nd match --> {match}")
            if match:
                start_index = match.start()
                previous_lines = func_modified_block[:start_index].strip().splitlines()
                #print(f"previous_lines --> {previous_lines}")
                previous_line = previous_lines[-1] if previous_lines else ""
                #print(f"previous_line --> {previous_line}")
                if re.search(re.escape(previous_line), func):
                    previous_line_real = previous_line
                else:
                    if previous_line.startswith('+') and re.search(re.escape(previous_line[1:]), func): # 对'+'顶格开头的那些
                        previous_line_real = previous_line
                    elif previous_line.startswith('-') and re.search(re.escape(previous_line[1:]), func): # 对'-'顶格开头的那些
                        previous_line_real = previous_line
                    elif re.search(re.escape(previous_line[1:]), func):
                        previous_line_real = previous_line[1:] 
                    else:
                        previous_line_real = previous_line 
                #print(f"previous_lines --> '{previous_line_real}'")
                if previous_line:
                    change["context_line_add"] = f"{previous_line_real}\n {context_line_add}"
                    #print(change["context_line_add"])
                
                if change["context_line_add"].startswith('+'):
                    flag = True
                else:
                    if re.search(re.escape(previous_line_real), func):
                        flag = True
                    elif flag_ModifiedBlock_PreviousTextNotInFunc_FllowingTextInFunc:
                        flag = True
                    else:
                        flag = False
        if flag:
            updated_changes.append(change)
        #updated_changes.append(change)
    return updated_changes

def check_change(change, func, func_modified_block): 
    # https://github.com/FFmpeg/FFmpeg/commit/77a4c8b959fa9bc6bcaa42b40a0b046cdf3fec38
    if change.get('deletions', '') != '' or not change.get('additions', ''):
        return False
    
    additions = change['additions']
    

    diff_block_pattern = re.compile(r'(@@[^@]*@@)(.*?)(?=@@|$)', re.DOTALL)
    blocks = diff_block_pattern.findall(func_modified_block)
    target_block_content = None
    additions_in_diff = '\n'.join(['+' + line for line in additions.split('\n')])
    #print(f"additions_in_diff --> {additions_in_diff}")
    for header, content in blocks: # 查找包含additions的diff块
        if additions_in_diff in content:
            #print("additions_in_diff in content")
            target_block_content = content
            break
    if not target_block_content:
        if len(blocks) == 1:
            target_block_content = blocks[0][1]
        else:
            return False
    
    start_idx = target_block_content.find(additions_in_diff)
    if start_idx == -1:
        return False
    end_idx = start_idx + len(additions_in_diff)
    following_code = target_block_content[end_idx:]

    def process_following_code(code):
        code = re.sub(r'\n ', '', code)
        return code.strip()
    processed_following = process_following_code(following_code)
    #print(f"processed_following --> {processed_following}")
    def process_func(code):
        return code.replace('\n', '')
    processed_func = process_func(func)
    
    return processed_following in processed_func

def process_function_changes(func, func_modified_block):
    func_lines = [line.rstrip('\n') for line in func.split('\n')]
    
    patch_lines = func_modified_block.split('\n')
    changes = []
    current_change = None
    func_signature = ""
    
    prev_context = None
    last_non_empty_context = None
    in_change_block = False
    
    for line in patch_lines:
        if line.startswith('@@'):
            if current_change:
                changes.append(current_change)
                current_change = None
            
            header_parts = line.split('@@')
            func_signature = '@@'.join(header_parts[2:]).rstrip('\n') if len(header_parts) > 2 else ""
            prev_context = None
            in_change_block = False
            last_non_empty_context = None
            continue
            
        if not line.startswith(('-', '+')):
            current_context = line.rstrip('\n')
            if current_context.strip():
                last_non_empty_context = current_context
                
            if current_change:
                changes.append(current_change)
                current_change = None
            prev_context = current_context
            in_change_block = False
            continue
            
        if not in_change_block:

            effective_context = prev_context if prev_context is not None else func_signature
            
            if effective_context.strip() == '' and last_non_empty_context:
                effective_context = last_non_empty_context
                
            current_change = {
                "context_line_del": effective_context,
                "context_line_add": effective_context,
                "deletions": [],
                "additions": []
            }
            in_change_block = True
            
        if line.startswith('-'):
            current_change["deletions"].append(line[1:])
        elif line.startswith('+'):
            current_change["additions"].append(line[1:])
    
    if current_change:
        changes.append(current_change)
    
    final_changes = []
    for change in changes:
        if not change["deletions"] and not change["additions"]:
            continue
            
        final_changes.append({
            "context_line_del": remove_leading_space(change["context_line_del"]),
            "context_line_add": remove_leading_space(change["context_line_add"]),
            "deletions": '\n'.join(change["deletions"]),
            "additions": '\n'.join(change["additions"])
        })
    
    original_lines = set()
    for line in func.split('\n'):
        stripped_line = line.rstrip()
        if stripped_line and not stripped_line.startswith(('//', '/*', '*/', '*')):
            original_lines.add(stripped_line)

    line_fingerprints = {} 
    for idx, line in enumerate(func.split('\n')):
        canonical_line = line.rstrip('\n') 
        line_fingerprints[canonical_line] = idx
    
    patch_hunks = parse_patch_context(func_modified_block)
    #print(f"patch_hunks --> {patch_hunks}")
    additions_context_map = build_additions_context_map(patch_hunks)
    
    target_signature = func.split('\n', 1)[0].strip()
    #print(f"target_signature -- > {target_signature}")
    # for change in final_changes:
    #     print(change)
    valid_changes = []
    for change in final_changes:
        #print(f"func_modified_block: {func_modified_block}")
        #print(f"\ncurrent change: 1 {change}")
        if change["context_line_del"] not in line_fingerprints:
            if check_change(change, func, func_modified_block):
                valid_changes.append(change)
            continue
        
        ctx_del = change["context_line_del"].strip() 
        #print(target_signature)
        if ctx_del in ('{', '}'):
            additions_content = change["additions"]#.strip()
            # 从映射中获取精确的下一行
            next_line = additions_context_map.get(additions_content, None)
            #print(next_line)
            #print(f"{additions_content} next_line --> \"{next_line}\"\n")
            next_line_varint = None
            if next_line:
                next_line_varint = next_line[1:]
            #print(f"ctx_del-->{ctx_del}")
            #print(f"additions_content-->{additions_content}")
            #print(f"additions_context_map=======>{additions_context_map}")
            #print(f"next_line-->\"{next_line}\"")
            #print(f"line_fingerprints-->{line_fingerprints}")
            if next_line_varint: 
                if next_line and (next_line_varint not in line_fingerprints):
                #print(f"{next_line} not in func")
                    continue
                if next_line and next_line_varint in target_signature:
                #print(f"next_line_varint --> {next_line_varint}\ntarget_signature --> {target_signature}")
                    continue
            #print(f"{next_line} in func")
            #print(target_signature)
        #print(f"\033[93mYYY\033[0m {change}") # \033[93mYellow\033[0m

        deletions = change["deletions"]

        if not deletions.strip():
            valid_changes.append(change)
            continue
        #print(f"rule4 --> {valid_changes}")
        all_deletion_valid = True
        for del_line in deletions.split('\n'):
            stripped_del = del_line.rstrip()

            if stripped_del and stripped_del not in original_lines:
                all_deletion_valid = False
                break
        
        if all_deletion_valid:
            valid_changes.append(change)
    #print(f"valid_changes --> {valid_changes}")
    final_changes = deduplicate_changes(valid_changes)
    #print(f"final_changes -- > {final_changes}")
    final_changes = process_changes_deletionsANDadditions(final_changes)
    #print(len(final_changes))
    #print(f"final_changes -- > {final_changes}")
    updated_changes = update_final_changes(final_changes, func_modified_block, func)
    #print(f"updated_changes -- > {updated_changes}")
    return updated_changes


def extract_func_name(signature: str) -> str:

    match = re.search(r'\b(\w+)\s*\(', signature)
    return match.group(1) if match else ""

def split_patch_blocks(patch, target_signature):
    blocks = []
    current_block = []
    in_target_block = False
    
    for line in patch.split('\n'):
        if line.startswith('@@'):
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
            in_target_block = False
        current_block.append(line)
    
    if current_block:
        blocks.append('\n'.join(current_block))
    
    matched_blocks = []
    target_pattern = re.compile(
        r'^[- ]\s*' + re.escape(target_signature) + r'\s*{?',
        re.MULTILINE
    )
    
    for block in blocks:
        header_line = block.split('\n', 1)[0]
        header_match = re.search(r'@@ -\d+,\d+ \+\d+,\d+ @@\s*(.*)', header_line)
        header_context = header_match.group(1).strip() if header_match else ""

        if header_context and (header_context in target_signature or target_signature.startswith(header_context)):
            matched_blocks.append(block)
            continue

        header_func = extract_func_name(header_context)
        target_func = extract_func_name(target_signature)
        if header_func and header_func == target_func:
            matched_blocks.append(block)
            continue

        if re.search(target_pattern, block):
            matched_blocks.append(block)
    
    return matched_blocks

def process_function_json(function_json_path, commits_base_dir):

    with open(function_json_path, 'r', encoding='utf-8') as f:
        elements = json.load(f)
    
    for element in elements:
        project = element['project']
        commit_id = element['commit_id']
        raw_func = element['input']

        element.setdefault('changes', [])

        target_signature = raw_func.split('\n', 1)[0].strip()
        
        commit_file = os.path.join(commits_base_dir, project, f"{commit_id}.json")
        #print(f"commit_file PATH --> {commit_file}")
        #break
        if not os.path.exists(commit_file):
            print(f"警告：提交文件缺失 {commit_file}")
            continue
        
        with open(commit_file, 'r', encoding='utf-8') as cf:
            commit_data = json.load(cf)


        for file_entry in commit_data.get('files', []):
            patch = file_entry.get('patch', '')
            if not patch:
                continue
            func_blocks = split_patch_blocks(patch, target_signature) # 
            # https://github.com/FFmpeg/FFmpeg/commit/c7c207aecde0773afc974ce4b7e25dca659bc5b5
            # print(func_blocks)
            for block in func_blocks:
                changes = process_function_changes(raw_func, block)
                # print(f"changes: {changes}")
                element['changes'].extend(changes)
    

    base_name = os.path.basename(function_json_path)
    name, ext = os.path.splitext(base_name)
    new_filename = f"{name}_updateChanges{ext}"
    output_path = os.path.join(os.path.dirname(function_json_path), new_filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(elements, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # process_function_json('test_changes.json', '../commits_202503102000') # function_formatted_target_1
    process_function_json('train_512_InDiversevul_AddNewKeysCommitidProjectEtc_updateProjectKeyValue_updateMessage.json', './commits_20250312')
    #process_function_json('../function_formatted_target_0.json', '../../commits_202503200950')
