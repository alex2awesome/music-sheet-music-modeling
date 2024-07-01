import os

import hydra
import omegaconf
from config_typings import Config

import torch

from SMT import SMT

from loguru import logger
from data import GraphicCLDataModule
from lightning.pytorch import Trainer
from lightning.pytorch.callbacks import ModelCheckpoint
from lightning.pytorch.loggers import WandbLogger
from lightning.pytorch.callbacks.early_stopping import EarlyStopping

torch.set_float32_matmul_precision('high')

@hydra.main(version_base=None, config_path="config", config_name="config")
def main(config:Config):
    data_module = GraphicCLDataModule(config.data, config.cl, fold=config.data.fold)
    
    train_dataset = data_module.train_dataset

    try:
        model = SMT.load_from_checkpoint(config.experiment.pretrain_weights, config=config.model_setup)
        logger.info(f"Loaded pretrain weights from {config.experiment.pretrain_weights}")
    except omegaconf.errors.ConfigAttributeError:
        logger.warning("No pretrain weights provided, training from scratch")
        model = SMT(config=config.model_setup, w2i=train_dataset.w2i, i2w=train_dataset.i2w)
        
    
    wandb_logger = WandbLogger(project='FP_SMT', group=f"SMTppNEXT", name=f"GrandStaff", log_model=True)

    early_stopping = EarlyStopping(monitor=config.experiment.metric_to_watch, min_delta=0.01, patience=5, mode="min", verbose=True)
    
    checkpointer = ModelCheckpoint(dirpath=f"weights/{config.metadata.corpus_name}/", filename=f"{config.metadata.model_name}_fold_{config.data.fold}", 
                                   monitor=config.experiment.metric_to_watch, mode='min',
                                   save_top_k=1, verbose=True)

    trainer = Trainer(max_epochs=config.experiment.max_epochs, 
                      check_val_every_n_epoch=config.experiment.val_after, 
                      logger=wandb_logger, callbacks=[checkpointer, early_stopping], precision='16-mixed')
    
    train_dataset.set_logger(wandb_logger)
    train_dataset.set_trainer_data(trainer)
    
    trainer.fit(model, datamodule=data_module)
    
    model = SMT.load_from_checkpoint(checkpointer.best_model_path, config=config.model_setup)

    trainer.test(model, datamodule=data_module)

if __name__ == "__main__":
    main()