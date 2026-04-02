import multiprocessing

import numpy as np

import time

import argparse

import psutil

import os
 
# Hardware-agnostic GPU support via OpenCL (AMD, Intel, NVIDIA)

try:

    import pyopencl as cl

    GPU_SUPPORT = True

except ImportError:

    GPU_SUPPORT = False
 
def stress_cpu(duration):

    """Engages CPU cores with high-intensity floating point calculations."""

    stop_time = time.time() + duration

    while time.time() < stop_time:

        # Complex math to heat up Ryzen/Intel cores

        _ = [x**2 for x in range(10000)]
 
def stress_ram(target_gb, duration):

    """Allocates and continuously modifies RAM to test bandwidth and limits."""

    try:

        # float64 = 8 bytes. Calculation: (GB * 1024^3) / 8

        size = int((target_gb * 1024**3) // 8)

        print(f"[RAM] Attempting to allocate {target_gb:.2f} GB...")

        # This allocates the memory

        data = np.ones(size, dtype=np.float64)

        stop_time = time.time() + duration

        print(f"[RAM] Allocation successful. Cycling data for {duration}s...")

        while time.time() < stop_time:

            # Force memory bus activity (Memory Speed/Latency test)

            data *= 1.000001 

            time.sleep(0.1)

    except MemoryError:

        print("[RAM] ALERT: Memory Limit Hit! Docker OOM or System Cap reached.")

    except Exception as e:

        print(f"[RAM] Error: {e}")
 
def stress_gpu(duration):

    """Universal GPU stressor using OpenCL."""

    if not GPU_SUPPORT:

        print("[GPU] OpenCL not found. Skipping GPU stress.")

        return

    try:

        # Auto-selects the first available compute device (Intel/AMD/NVIDIA)

        ctx = cl.create_some_context(interactive=False)

        queue = cl.CommandQueue(ctx)

        # Allocate a dummy 512MB VRAM buffer

        vram_buffer = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, 512 * 1024**2)

        print(f"[GPU] Device engaged. Holding VRAM for {duration}s...")

        stop_time = time.time() + duration

        while time.time() < stop_time:

            time.sleep(1)

    except Exception as e:

        print(f"[GPU] Could not engage device: {e}")
 
if __name__ == "__main__":

    # 1. AUTO-DETECTION

    logical_cores = multiprocessing.cpu_count()

    # Detects RAM visible to the OS/Container

    mem_info = psutil.virtual_memory()

    total_visible_ram_gb = mem_info.total / (1024**3)

    # Target 90% of available RAM to allow the OS/Docker to stay responsive

    safe_max_ram = (mem_info.available / (1024**3)) * 0.9
 
    parser = argparse.ArgumentParser(description="Universal Hardware Stressor for DevOps Lab")

    parser.add_argument("--cpu", type=int, default=logical_cores, help="Number of CPU threads")

    parser.add_argument("--mem", type=float, default=safe_max_ram, help="RAM to consume in GB")

    parser.add_argument("--time", type=int, default=60, help="Duration in seconds")

    args = parser.parse_args()
 
    print("--- DevOps Resource Stressor ---")

    print(f"Detected Cores: {logical_cores}")

    print(f"Detected RAM:   {total_visible_ram_gb:.2f} GB")

    print(f"Targeting:      {args.cpu} Cores | {args.mem:.2f} GB RAM | {args.time}s")

    print("--------------------------------")
 
    processes = []
 
    # Start CPU processes

    for i in range(args.cpu):

        p = multiprocessing.Process(target=stress_cpu, args=(args.time,), name=f"CPU_{i}")

        p.start()

        processes.append(p)
 
    # Start RAM process

    m = multiprocessing.Process(target=stress_ram, args=(args.mem, args.time), name="RAM_Stresser")

    m.start()

    processes.append(m)
 
    # Start GPU process (in main thread or separate)

    g = multiprocessing.Process(target=stress_gpu, args=(args.time,), name="GPU_Stresser")

    g.start()

    processes.append(g)
 
    try:

        for p in processes:

            p.join()

        print("\n[DONE] Stress test completed successfully.")

    except KeyboardInterrupt:

        print("\n[STOP] Manual interrupt received. Killing workers...")

        for p in processes:

            p.terminate()
 