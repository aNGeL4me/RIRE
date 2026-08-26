import os
import shutil

old_filename = "train_512_InDevign_AddNewKeysCommitidProject_updated_target1target0_ChangesNull_DelIndent_UpdateChanges_1.json"
temp_file = "temp_copy.json"
new_filename = "train_512_InDevign_updated_target1_0_ChangesNull_UpdatedChanges_1.json"

if os.path.exists(old_filename):
    shutil.copy(old_filename, temp_file) 
    os.rename(temp_file, new_filename) 
    print(f"file has been rename: {new_filename}")
else:
    print(f"file not found {new_filename}")
