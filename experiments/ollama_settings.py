#!/usr/bin/env python3
"""
Ollama VRAM Calculator
Estimates total GPU memory usage for a given model with configurable settings.
"""
import re

def calculate_ollama_vram(raw_text: str, context_length: int):
    # 1. Identify the architecture (The anchor for all other metadata)
    arch_match = re.search(r"general\.architecture\s+([\w-]+)", raw_text)
    if not arch_match:
        return "Error: Could not find architecture in the provided text."

    arch = arch_match.group(1).strip()

    # 2. Define Regex Patterns (using the dynamic architecture prefix)
    patterns = {
        "params": r"general\.parameter_count\s+([\d.e+]+)",
        "context": rf"{arch}\.context_length\s+(\d+)",
        "layers": rf"{arch}\.block_count\s+(\d+)",
        "kv_heads": rf"{arch}\.attention\.head_count_kv\s+(\d+)",
        "quant_str": r"quantization\s+([A-Z0-9_]+)",
        # Head Dim can be in three different places depending on the model
        "head_dim_meta": rf"{arch}\.attention\.key_length\s+(\d+)",
        "head_dim_rope": rf"{arch}\.rope\.dimension_count\s+(\d+)",
        "tensor_shape": r"blk\.0\.attn_k\.weight\s+\w+\s+\[\d+\s+(\d+)\]"
    }

    # 3. Extraction Helper
    def get_val(key, is_float=False):
        match = re.search(patterns[key], raw_text)
        if match:
            return float(match.group(1)) if is_float else int(match.group(1))
        return None

    # 4. Data Collection
    params = get_val("params", is_float=True)
    context = get_val("context") if get_val("context") <= context_length else context_length
    layers = get_val("layers")
    kv_heads = get_val("kv_heads")

    # Logic to find Head Dim: Metadata -> RoPE -> Tensor Fallback
    head_dim = get_val("head_dim_meta") or get_val("head_dim_rope")
    if not head_dim:
        tensor_val = get_val("tensor_shape")
        head_dim = (tensor_val // kv_heads) if tensor_val and kv_heads else 128

    # 5. Quantization Bit-Width Mapping
    quant_match = re.search(patterns["quant_str"], raw_text)
    quant_label = quant_match.group(1) if quant_match else "Unknown"

    # Estimated bits per weight (including overhead for GGUF/Ollama quants)
    quant_map = {
        "Q2_K": 3.35, "Q3_K_M": 3.91, "Q4_0": 4.5, "Q4_K_M": 4.85,
        "Q5_K_M": 5.5, "Q6_K": 6.6, "Q8_0": 8.5, "F16": 16.0, "MXFP4": 4.0
    }
    bpw = quant_map.get(quant_label, 4.5)  # Default to 4.5 if unknown

    # 6. VRAM Calculations
    # Weights VRAM (GiB)
    vram_weights = (params * bpw) / (8 * 1024 ** 3)

    # KV Cache VRAM (GiB) - Assuming FP16 (2 bytes per scalar)
    # Formula: 2 (K+V) * Layers * Context * KV_Heads * Head_Dim * 2 Bytes
    vram_kv_cache = (2 * layers * context * kv_heads * head_dim * 2) / (1024 ** 3)

    # Overhead (Activation buffers + CUDA context)
    vram_overhead = max(1.0, vram_weights * 0.1)

    total_vram = vram_weights + vram_kv_cache + vram_overhead

    return {
        "Architecture": arch,
        "Layers": layers,
        "Quantization": quant_label,
        "Model Weights (GB)": round(vram_weights, 2),
        "KV Cache (GB)": round(vram_kv_cache, 2),
        "Total Required VRAM (GB)": round(total_vram, 2)
    }