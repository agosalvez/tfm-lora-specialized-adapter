import torch
print(f"🔍 PyTorch versión: {torch.__version__}")
print(f"🎯 CUDA disponible: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"🔧 GPU: {torch.cuda.get_device_name(0)}")
    print(f"💾 VRAM total: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    print(f"💾 VRAM libre: {torch.cuda.memory_reserved(0) / 1024**3:.1f} GB")
else:
    print("❌ CUDA no detectado")
