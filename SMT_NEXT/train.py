import os
import gin
import torch
import torch.nn as nn

from loguru import logger
from data import load_grandstaff_singleSys, batch_preparation_img2seq
from torch.utils.data import DataLoader

torch.set_float32_matmul_precision('high')

@gin.configurable
def main():
    logger.info("-----------------------")
    logger.info(f"Training NEXT-SMT model")
    logger.info("-----------------------")

    data_path = f"./Data/GrandStaff"
    out_dir = f"./out/"
    vocab_path = "vocab/GrandStaffGlobal"

    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(f"{out_dir}/hyp", exist_ok=True)
    os.makedirs(f"{out_dir}/gt", exist_ok=True)

    train_dataset, val_dataset, test_dataset = load_grandstaff_singleSys(data_path, vocab_path)

    w2i, i2w = train_dataset.get_dictionaries()

    train_dataloader = DataLoader(train_dataset, batch_size=1, num_workers=20, collate_fn=batch_preparation_img2seq, shuffle=True)
    val_dataloader = DataLoader(val_dataset, batch_size=1, num_workers=20, collate_fn=batch_preparation_img2seq)
    test_dataloader = DataLoader(test_dataset, batch_size=1, num_workers=20, collate_fn=batch_preparation_img2seq)
    
if __name__ == "__main__":
    main()