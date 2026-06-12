import sys
sys.path.insert(0, 'models/include')
import torch
import numpy as np
from models.transformer import Transformer
from configs import TransformerConfig

config = TransformerConfig(size='large')
m = Transformer(config, 263)
m.eval()

seq = np.zeros((30, 134), dtype=np.float32)
x = torch.tensor(seq).unsqueeze(0)
x = m.l1(x)
x = m.embedding(x)

try:
    with torch.no_grad():
        out = m.layers[0](x)
        print("Layer 0 out type:", type(out))
        print("Layer 0 out len:", len(out))
        print("Layer 0 out[0] type/shape:", type(out[0]), out[0].shape)
        
        x = out[0]
        out2 = m.layers[1](x)
        print("Layer 1 success!")
except Exception as e:
    import traceback
    traceback.print_exc()
