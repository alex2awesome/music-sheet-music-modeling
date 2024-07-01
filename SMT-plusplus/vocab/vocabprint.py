import numpy as np


w2i = np.load("/pool001/spangher/music-sheet-music-modeling/SMT-plusplus/vocab/GrandStaff_BeKerni2w.npy", allow_pickle=True).item()
i2w = np.load("/pool001/spangher/music-sheet-music-modeling/SMT-plusplus/vocab/GrandStaff_BeKernw2i.npy", allow_pickle=True).item()


print(i2w)
