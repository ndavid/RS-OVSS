from yacs.config import CfgNode as CN 
from pathlib import Path
import os

_C = CN()

def init_general_config(_C, src_path):
    """Initialize general configuration settings."""
    # Ensure src_path is a Path object
    if not isinstance(src_path, Path):
        src_path = Path(src_path)
    
    _C.NAME = ''
    _C.DIR_PATH = str(src_path)
    _C.RESULTS_PATH = str(src_path / 'output')
    _C.WANDB_LOG = False
    _C.WANDB_PROJECT = 'TACOSS'
    _C.MAX_EPOCHS = 10
    _C.MODEL_TYPE = 'contrastive_segformer'
    _C.MODEL_FROM_FILE = ''
    _C.FREEZE_ENCODER = False
    _C.seed = 1234
    _C.test_batch_size = 8
    _C.output_dir = str(src_path / 'output')


def init_flair_config(_C, data_path, src_path):
    """Initialize FLAIR dataset configuration."""
    # Ensure paths are Path objects
    if not isinstance(data_path, Path):
        data_path = Path(data_path)
    if not isinstance(src_path, Path):
        src_path = Path(src_path)
    
    _C.FLAIR = CN()
    _C.FLAIR.N_CLASS = 13
    _C.FLAIR.SPLIT = ''
    _C.FLAIR.DATA_DIR = str(data_path / "flair_aerial_train")
    _C.FLAIR.SPLIT_PATH = str(src_path / 'data' / 'flair_split')
    _C.FLAIR.TEST_SPLIT_PATH = str(src_path / 'data' / 'flair_split' / 'base' / 'test.csv')
    _C.FLAIR.PLOT_SPLIT_PATH = str(src_path / 'data' / 'flair_split' / 'base' / 'plot.csv')
    _C.FLAIR.TRAIN_PATCH_SIZE = 512
    _C.FLAIR.TEST_PATCH_SIZE = 512
    _C.FLAIR.CLASSES = [{
        0:'Others',
        1: "building",      2: "pervious surface",      3: "impervious surface",    4: "bare soil",
        5: "water",         6: "coniferous",            7: "deciduous",             8: "brushwood",
        9: "vineyard",      10: "herbaceous vegetation",11: "agricultural land",    12: "plowed land",
    }]


def init_tlm_config(_C, data_path, src_path):
    """Initialize TLM dataset configuration."""
    # Ensure paths are Path objects
    if not isinstance(data_path, Path):
        data_path = Path(data_path)
    if not isinstance(src_path, Path):
        src_path = Path(src_path)
    
    _C.TLM = CN()
    _C.TLM.N_CLASS = 14
    _C.TLM.RGB_DIR = str(data_path / 'swisstopo' / 'SI_2020_50cm_100m')
    _C.TLM.LABEL_DIR = str(data_path / 'contrastive-lc' / 'tlm_14cls_100m')
    _C.TLM.TEST_SPLIT_PATH = str(src_path / 'data' / 'tlm_split' / 'soleil_100m.csv')
    _C.TLM.TEST_PATCH_SIZE = 200
    _C.TLM.EMBEDDING_PATH = str(src_path / 'data' / 'tlm_labels' / 'tlm_labels_sbert.pt')
    _C.TLM.CLASSES = [{ 
        0:'Others',    1:'agricultural area',2:'building',    3:'bush forest',
        4:'forest',    5:'glacier',6:'lake',    7:'wetlands',
        8:'vineyards',    9:'railways',10:'river',    11:'road',
        12:'rocks',    13:'open forest',14:'rocks with grass',   
    }]
    _C.TLM.DEBUG = False


def init_training_config(_C):
    """Initialize training configuration."""
    _C.train = CN()
    _C.train.batch_size = 10
    _C.train.num_workers = 8
    _C.train.optimizer_type = 'adamw'
    _C.train.scheduler_type = 'polynomial'
    _C.train.lr = 6e-5
    _C.train.val_epoch_freq = 1
    _C.train.contrastive = []


def get_cfg_defaults(src_path=None, data_path=None):
    """Get a yacs CfgNode object with default values for my_project."""
    # Auto-detect src_path if not provided
    if src_path is None:
        # Try environment variable first
        src_path_str = os.environ.get('RS_OVSS_SRC_PATH')
        
        if src_path_str is not None:
            src_path = Path(src_path_str)
        else:
            # Use repository root (parent of config directory)
            src_path = Path(__file__).parent.parent
    else:
        # Convert to Path if string provided
        if not isinstance(src_path, Path):
            src_path = Path(src_path)
    
    # Auto-detect data_path if not provided
    if data_path is None:
        # Try environment variable first
        data_path_str = os.environ.get('RS_OVSS_DATA_PATH')
        
        if data_path_str is not None:
            data_path = Path(data_path_str)
        else:
            # Try predefined paths
            all_data_path = [Path("/media/DATA/TACOSS/")]
            for path in all_data_path:
                if path.is_dir():
                    data_path = path
                    break
        
        if data_path is None:
            raise Exception('Failed to find data path. Set RS_OVSS_DATA_PATH environment variable.')
    else:
        # Convert to Path if string provided
        if not isinstance(data_path, Path):
            data_path = Path(data_path)
    
    # Initialize configuration with subconfigs
    _C = CN()
    init_general_config(_C, src_path)
    init_flair_config(_C, data_path, src_path)
    init_tlm_config(_C, data_path, src_path)
    init_training_config(_C)
    
    # Return a clone so that the defaults will not be altered
    return _C.clone()



