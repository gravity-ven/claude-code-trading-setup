# AI/ML Memory Optimization Guide
## System: 128GB RAM, 100GB Swap

---

## 1. PyTorch Optimization (CRITICAL)

### Enable Memory-Efficient Training

```python
import torch
import gc

# 1. Enable gradient checkpointing (trades compute for memory)
# Reduces memory by 50-80% for large models
model.gradient_checkpointing_enable()

# 2. Use mixed precision training (FP16/BF16)
# Reduces memory by 50% + faster training
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()
with autocast():
    output = model(input)
    loss = criterion(output, target)

# 3. Reduce batch size dynamically
# Start small, increase until OOM, then back off
BATCH_SIZE = 8  # Adjust based on model size

# 4. Clear cache regularly
torch.cuda.empty_cache()
gc.collect()

# 5. Use DataLoader with num_workers
# Parallel data loading reduces memory spikes
train_loader = DataLoader(
    dataset,
    batch_size=BATCH_SIZE,
    num_workers=8,  # Match your CPU cores
    pin_memory=True
)
```

---

## 2. Model Quantization

### Reduce Model Size by 75%

```python
# INT8 quantization (4x smaller than FP32)
import torch.quantization

model_int8 = torch.quantization.quantize_dynamic(
    model,
    {torch.nn.Linear},
    dtype=torch.qint8
)

# Memory savings:
# - FP32 model: 100GB → INT8 model: 25GB
# - Minimal accuracy loss (<1% typically)
```

---

## 3. Gradient Accumulation

### Simulate Large Batches Without Memory

```python
# Instead of batch_size=128 (OOM)
# Use batch_size=16 with accumulation_steps=8
# Effective batch_size = 16 * 8 = 128

accumulation_steps = 8
optimizer.zero_grad()

for i, (inputs, labels) in enumerate(train_loader):
    outputs = model(inputs)
    loss = criterion(outputs, labels) / accumulation_steps
    loss.backward()

    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

---

## 4. Model Parallelism

### Split Model Across CPU + GPU (if applicable)

```python
# For models > 96GB RAM
import torch.nn as nn

class SplitModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.layer1 = nn.Linear(1000, 5000).to('cuda')  # GPU
        self.layer2 = nn.Linear(5000, 5000).to('cpu')   # CPU RAM
        self.layer3 = nn.Linear(5000, 1000).to('cuda')  # GPU

    def forward(self, x):
        x = self.layer1(x)
        x = x.to('cpu')  # Move to CPU
        x = self.layer2(x)
        x = x.to('cuda')  # Move back to GPU
        x = self.layer3(x)
        return x
```

---

## 5. Memory Monitoring

### Track Memory Usage in Real-Time

```python
import psutil
import os

def print_memory_usage():
    """Monitor RAM and swap usage"""
    process = psutil.Process(os.getpid())

    # RAM usage
    mem_info = process.memory_info()
    ram_gb = mem_info.rss / 1024**3

    # System-wide memory
    system_mem = psutil.virtual_memory()
    system_ram_gb = system_mem.used / 1024**3
    system_ram_avail = system_mem.available / 1024**3

    # Swap usage
    swap = psutil.swap_memory()
    swap_used_gb = swap.used / 1024**3

    print(f"Process RAM: {ram_gb:.2f} GB")
    print(f"System RAM: {system_ram_gb:.2f} GB / {system_ram_avail:.2f} GB available")
    print(f"Swap Used: {swap_used_gb:.2f} GB")

    # Warning if approaching limits
    if system_ram_avail < 10:
        print("⚠️  WARNING: Less than 10GB RAM available!")
    if swap_used_gb > 50:
        print("⚠️  WARNING: Heavy swap usage - performance degraded!")

# Use in training loop
for epoch in range(epochs):
    print_memory_usage()
    train_epoch()
```

---

## 6. Efficient Data Loading

### Prevent Memory Leaks in Data Pipeline

```python
from torch.utils.data import Dataset, DataLoader

class EfficientDataset(Dataset):
    def __init__(self, data_path):
        # DON'T load all data into memory
        # Store file paths only
        self.file_paths = load_file_list(data_path)

    def __getitem__(self, idx):
        # Load data on-the-fly
        data = load_and_process(self.file_paths[idx])
        return data

    def __len__(self):
        return len(self.file_paths)

# Use persistent workers to avoid memory leaks
loader = DataLoader(
    dataset,
    batch_size=32,
    num_workers=8,
    persistent_workers=True,  # Keeps workers alive
    prefetch_factor=2          # Preload 2 batches
)
```

---

## 7. Linux Memory Tuning

### Optimize Swap Behavior

```bash
# Check current swappiness (default: 60)
cat /proc/sys/vm/swappiness

# Set swappiness to 10 (use RAM more aggressively)
# Lower = use swap less, higher = use swap more
sudo sysctl vm.swappiness=10

# Make permanent (add to /etc/sysctl.conf)
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf

# Monitor swap usage
watch -n 1 'free -h && swapon --show'
```

---

## 8. Hugging Face Transformers Optimization

### For Large Language Models

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# 1. Load in 8-bit (75% memory reduction)
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-70b-hf",
    load_in_8bit=True,          # INT8 quantization
    device_map="auto",           # Automatic device placement
    torch_dtype=torch.float16   # FP16 for non-quantized parts
)

# 2. Use Flash Attention 2 (2x faster, 50% less memory)
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-70b-hf",
    attn_implementation="flash_attention_2"
)

# 3. Gradient checkpointing
model.gradient_checkpointing_enable()

# 4. Use efficient inference
model.eval()  # Disables dropout, batch norm
with torch.no_grad():  # Disables gradient computation
    outputs = model.generate(input_ids)
```

---

## 9. Emergency Memory Recovery

### When OOM Happens

```python
import torch
import gc

def emergency_memory_cleanup():
    """Call when approaching OOM"""
    # Clear all CUDA cache
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

    # Force garbage collection
    gc.collect()

    # Clear Python cache
    import sys
    sys.modules.clear()

    print("Emergency cleanup complete")

# Set OOM handler
torch.cuda.set_per_process_memory_fraction(0.9)  # Use max 90% GPU memory
```

---

## 10. Recommended Workflow for Your System

### 128GB RAM + 100GB Swap

```python
# Step 1: Profile your model first
import torch.profiler

with torch.profiler.profile(
    activities=[
        torch.profiler.ProfilerActivity.CPU,
        torch.profiler.ProfilerActivity.CUDA,
    ],
    profile_memory=True,
    record_shapes=True
) as prof:
    model(sample_input)

print(prof.key_averages().table(sort_by="self_cpu_memory_usage"))

# Step 2: Apply optimizations based on profile
# - If memory spike during forward pass → gradient checkpointing
# - If memory spike during backward pass → gradient accumulation
# - If steady high memory → model quantization

# Step 3: Train with monitoring
for epoch in range(num_epochs):
    print_memory_usage()  # From section 5

    for batch in train_loader:
        # Your training code
        pass

    # Periodic cleanup
    if epoch % 10 == 0:
        emergency_memory_cleanup()
```

---

## Memory Budget Reference

### Typical Model Sizes (FP32)

| Model | Parameters | Memory Required |
|-------|-----------|-----------------|
| GPT-2 Small | 117M | 0.5 GB |
| GPT-2 Medium | 345M | 1.4 GB |
| GPT-2 Large | 774M | 3.1 GB |
| GPT-2 XL | 1.5B | 6 GB |
| GPT-3 6.7B | 6.7B | 27 GB |
| GPT-3 13B | 13B | 52 GB |
| Llama-2 70B | 70B | 280 GB ⚠️ |

### With Your 96GB RAM:

✅ **Can train** (with optimizations):
- GPT-2 XL (6GB) ✅
- GPT-3 6.7B (27GB) ✅
- GPT-3 13B (52GB) ✅

⚠️ **Need aggressive optimization**:
- Llama-2 70B (280GB) - Use INT8 quantization → 70GB ✅

---

## Quick Checklist

Before training large models:

- [ ] WSL configured with 96GB RAM (`free -h` confirms)
- [ ] Swappiness set to 10 (`cat /proc/sys/vm/swappiness`)
- [ ] Gradient checkpointing enabled
- [ ] Mixed precision (FP16/BF16) enabled
- [ ] Model quantized if > 50GB
- [ ] Memory monitoring script running
- [ ] Batch size optimized (start small)
- [ ] DataLoader using multiple workers
- [ ] Disk space available for swap (100GB free)

---

**Last Updated**: November 29, 2025
**System Config**: 128GB RAM, 96GB allocated to WSL, 100GB swap
