import os
import time
import json
import shutil
from datetime import datetime
from tqdm import tqdm
from SCvalidators.SCvalidator import SmetaParser

from _presets import MainPresets as PRESETS
SOURCE_FILE = "SCvalidators/examples/smeta_complex.docx"
ITERATIONS = 10


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

exp_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
exp_path = os.path.join("experiments", f"exp_{exp_time}")

ensure_dir(exp_path)
shutil.copy(SOURCE_FILE, os.path.join(exp_path, "source.docx"))

print(f"Старт эксперимента. Папка: {exp_path}")

for preset in PRESETS:
    preset_path = os.path.join(exp_path, preset["name"])
    ensure_dir(preset_path)

    parser = SmetaParser(preset={"MODEL": preset["model"], "TEMP": preset["temp"], "TOP-P": preset["top_p"]})
    with open(os.path.join(preset_path, "config.json"), "w") as f:
            json.dump(preset, f, indent=2)
    
    for i in tqdm(range(1, ITERATIONS + 1), desc=f"Generating {preset['name']}"):
        output_file = os.path.join(preset_path, f"res_{i}.json")
        try:
            result = parser.parse(docx_path=SOURCE_FILE, verbose=False, log=True)
            
            if result[0]:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result[1], f, ensure_ascii=False, indent=2)
            else:
                with open(output_file + ".error", "w", encoding="utf-8") as f:
                    f.write(result[1])

        except Exception as e:
            with open(output_file + ".cr_error", "w", encoding="utf-8") as f:
                    f.write(str(e))
                
        time.sleep(2)
    print(f'Тестирование пресета "{preset["name"]}" завершено')
print(f'Тестирование завершено!')