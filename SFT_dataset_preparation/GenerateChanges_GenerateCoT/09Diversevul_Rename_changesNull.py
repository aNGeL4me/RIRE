import shutil

src = "train_512_InDiversevul_AddNewKeysCommitidProjectEtc_updateProjectKeyValue_updateMessage_updateChanges_ChangesNull_DelIndent.json"
dst = "train_512_InDiversevul_updateChanges_ChangesNull_DelIndent.json"

try:
    shutil.copyfile(src, dst)
except FileNotFoundError:
    print(f"source file not exists: {src}")
except Exception as e:
    print(f"error: {e}")
