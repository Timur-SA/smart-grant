import os
import time
import json
import shutil
import asyncio
from datetime import datetime
from tqdm.asyncio import tqdm
from SCvalidators.SCvalidator import SmetaParser
from _presets import MODELS, PARAM_SETS

SOURCE_FILE = "SCvalidators/examples/smeta_complex.docx"
ITERATIONS = 1
MAX_RPM = 40


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
def strip_vendor(model_id: str) -> str: 
    return model_id.split("/")[-1]


class RateLimiter:
    """RPM-limiter"""
    def __init__(self, max_rpm: int):
        self.interval = 60.0 / max_rpm
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def acquire(self):
        async with self._lock:
            now = asyncio.get_event_loop().time()
            wait = self._last + self.interval - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = asyncio.get_event_loop().time()


async def run_single(parser: SmetaParser, source_file: str, output_file: str, rate_limiter: RateLimiter, semaphore: asyncio.Semaphore):
    async with semaphore:
        await rate_limiter.acquire()
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: parser.parse(docx_path=source_file, verbose=False, log=True),
            )
            if result[0]:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result[1], f, ensure_ascii=False, indent=2)
            else:
                with open(output_file + ".error", "w", encoding="utf-8") as f:
                    f.write(result[1])
        except Exception as e:
            with open(output_file + ".cr_error", "w", encoding="utf-8") as f:
                f.write(str(e))

async def run_param_set(model_id: str, param_set: dict, param_dir: str, rate_limiter: RateLimiter, semaphore: asyncio.Semaphore):
    ensure_dir(param_dir)

    parser = SmetaParser(
        preset={
            "MODEL": model_id,
            "TEMP": param_set["temp"],
            "TOP-P": param_set["top_p"],
        }
    )

    tasks = []
    for i in range(1, ITERATIONS + 1):
        output_file = os.path.join(param_dir, f"res_{i}.json")
        tasks.append(run_single(parser, SOURCE_FILE, output_file, rate_limiter, semaphore))

    short = strip_vendor(model_id)
    desc = f"{short : <40} | {param_set['name'] :>10}"

    for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc=desc):
        await coro

async def run_model(model_id: str, model_dir: str, rate_limiter: RateLimiter, semaphore: asyncio.Semaphore):
    ensure_dir(model_dir)

    tasks = []
    for param_set in PARAM_SETS:
        param_dir = os.path.join(model_dir, param_set["name"])
        tasks.append(
            run_param_set(model_id, param_set, param_dir, rate_limiter, semaphore)
        )


    for task in tasks:
        await task

    print(f"\n ✓ {strip_vendor(model_id)} — все наборы параметров завершены")


async def main():
    exp_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
    exp_path = os.path.join("experiments", f"exp_{exp_time}")
    ensure_dir(exp_path)

    shutil.copy(SOURCE_FILE, os.path.join(exp_path, "source.docx"))

    experiment_config = {
        "timestamp": exp_time,
        "source_file": SOURCE_FILE,
        "iterations": ITERATIONS,
        "max_rpm": MAX_RPM,
        "models": MODELS,
        "param_sets": PARAM_SETS,
        "total_requests": len(MODELS) * len(PARAM_SETS) * ITERATIONS,
    }
    with open(os.path.join(exp_path, "config.json"), "w", encoding="utf-8") as f:
        json.dump(experiment_config, f, ensure_ascii=False, indent=2)

    #HEADER
    print(f"{'=' * 60}")
    print(f"  Эксперимент: {exp_path}")
    print(f"  Моделей: {len(MODELS)}")
    print(f"  Наборов параметров: {len(PARAM_SETS)}")
    print(f"  Итераций: {ITERATIONS}")
    print(f"  Всего запросов: {experiment_config['total_requests']}")
    print(f"  RPM лимит: {MAX_RPM}")
    print(f"{'=' * 60}\n")

    rate_limiter = RateLimiter(max_rpm=MAX_RPM)
    semaphore = asyncio.Semaphore(MAX_RPM)

    model_tasks = []
    for model_id in MODELS:
        model_dir = os.path.join(exp_path, strip_vendor(model_id))
        model_tasks.append(run_model(model_id, model_dir, rate_limiter, semaphore))

    await asyncio.gather(*model_tasks)

    #RESULTS
    print(f"\n{'=' * 60}")
    print(f"  Эксперимент завершён!")
    print(f"  Результаты: {exp_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())