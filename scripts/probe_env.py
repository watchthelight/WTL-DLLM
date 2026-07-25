# wtl-dllm · scripts/probe_env.py
# what: probe python/gpu/ram, write docs/results/env.json, recommend a model preset
# why:  every training config downstream keys off this file
# by:   <wtl> watchthelight
# tags: scripts, environment

import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "docs" / "results" / "env.json"


def probe_torch():
    try:
        import torch
    except ImportError:
        return {"installed": False}
    info = {
        "installed": True,
        "version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
    }
    if info["cuda_available"]:
        props = torch.cuda.get_device_properties(0)
        info.update(
            device_name=props.name,
            vram_gb=round(props.total_memory / 2**30, 1),
            bf16_supported=torch.cuda.is_bf16_supported(),
            capability=f"{props.major}.{props.minor}",
        )
    return info


def probe_nvidia_smi():
    if not shutil.which("nvidia-smi"):
        return None
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=15,
        )
        line = out.stdout.strip().splitlines()[0]
        name, mem = [p.strip() for p in line.split(",")]
        return {"device_name": name, "vram": mem}
    except Exception:
        return None


def probe_ram():
    try:
        import psutil
        return round(psutil.virtual_memory().total / 2**30, 1)
    except ImportError:
        if platform.system() == "Windows":
            try:
                out = subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"],
                    capture_output=True, text=True, timeout=20,
                )
                return round(int(out.stdout.strip()) / 2**30, 1)
            except Exception:
                return None
    return None


def recommend(torch_info, smi):
    vram = torch_info.get("vram_gb")
    if vram is None and smi and "MiB" in smi.get("vram", ""):
        vram = round(int(smi["vram"].split()[0]) / 1024, 1)
    if vram is None:
        return "cpu-5m"
    if vram < 9:
        return "gpu-10m"
    return "gpu-17m"


def main():
    torch_info = probe_torch()
    smi = probe_nvidia_smi()
    env = {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "cpu_count": __import__("os").cpu_count(),
        "ram_gb": probe_ram(),
        "torch": torch_info,
        "nvidia_smi": smi,
        "preset_recommendation": recommend(torch_info, smi),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(env, indent=2) + "\n")
    print(json.dumps(env, indent=2))
    print(f"\n-> wrote {OUT}")
    print(f"-> recommended preset: {env['preset_recommendation']}")


if __name__ == "__main__":
    main()
