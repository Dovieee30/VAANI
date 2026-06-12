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
print("Initial x:", x.shape)
x = m.l1(x)
print("After l1:", x.shape)
x = m.embedding(x)
print("After embedding:", x.shape)

layer = m.layers[0]

try:
    with torch.no_grad():
        out = layer(x)
        print("Layer output:", len(out))
except Exception as e:
    import traceback
    traceback.print_exc()
