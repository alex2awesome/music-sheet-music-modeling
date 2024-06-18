import os
import gin
import fire
import torch
import torch.nn as nn

from loguru import logger
from data import load_grandstaff_singleSys, batch_preparation_img2seq
from torch.utils.data import DataLoader
from ModelManager import get_SMT, SMT
from lightning.pytorch import Trainer
from lightning.pytorch.callbacks import ModelCheckpoint
from lightning.pytorch.loggers import WandbLogger
from lightning.pytorch.callbacks.early_stopping import EarlyStopping

torch.set_float32_matmul_precision('high')

@gin.configurable
def main():
    logger.info("-----------------------")
    logger.info(f"Training NEXT-SMT model")
    logger.info("-----------------------")

    partition_path = f"./Data/GrandStaff/partition"
    out_dir = f"./out/"
    vocab_path = "vocab/GrandStaffGlobal"
    metric_to_watch = "val_SER"
    corpus_name = "GrandStaff"
    model_name = "NEXT_SMT"

    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(f"{out_dir}/hyp", exist_ok=True)
    os.makedirs(f"{out_dir}/gt", exist_ok=True)

    train_dataset, val_dataset, test_dataset = load_grandstaff_singleSys(partition_path, vocab_path)

    w2i, i2w = train_dataset.get_dictionaries()

    train_dataloader = DataLoader(train_dataset, batch_size=1, num_workers=20, collate_fn=batch_preparation_img2seq, shuffle=True)
    val_dataloader = DataLoader(val_dataset, batch_size=1, num_workers=20, collate_fn=batch_preparation_img2seq)
    test_dataloader = DataLoader(test_dataset, batch_size=1, num_workers=20, collate_fn=batch_preparation_img2seq)

    max_height, max_width = train_dataset.get_max_hw()
    max_len = train_dataset.get_max_seqlen()
    print(max_height, max_width, max_len)

    model = get_SMT(in_channels=1,
                            max_height=max_height, max_width=max_width, 
                            max_len=max_len, 
                            out_categories=len(train_dataset.get_i2w()), w2i=w2i, i2w=i2w, model_name=model_name, out_dir=out_dir)
    
    # wandb_logger = WandbLogger(project='ICDAR 2024', group=f"{corpus_name}", name=f"{model_name}", log_model=False)

    early_stopping = EarlyStopping(monitor=metric_to_watch, min_delta=0.01, patience=5, mode="min", verbose=True)
    
    checkpointer = ModelCheckpoint(dirpath=f"weights/{corpus_name}/", filename=f"{model_name}", 
                                   monitor=metric_to_watch, mode='min',
                                   save_top_k=1, verbose=True)

    # trainer = Trainer(max_epochs=5000, check_val_every_n_epoch=5, logger=wandb_logger, callbacks=[checkpointer, early_stopping])
    trainer = Trainer(
        max_epochs=5000, 
        check_val_every_n_epoch=5, 
        callbacks=[checkpointer, early_stopping],
        strategy='ddp_find_unused_parameters_true'

    )
    
    trainer.fit(model, train_dataloader, val_dataloader)

if __name__ == "__main__":
    main()