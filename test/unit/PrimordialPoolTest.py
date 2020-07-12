import logging
import os
import unittest

from src.shapeandshare.dicebox import PrimordialPool
from src.shapeandshare.dicebox.config import DiceboxConfig
from src.shapeandshare.dicebox.utils import make_sure_path_exists


class PrimordialPoolTest(unittest.TestCase):

    def test_pool(self):
        config_file = 'test/fixtures/mnist/dicebox.config'
        dicebox_config: DiceboxConfig = DiceboxConfig(config_file=config_file)

        ###############################################################################
        # Setup logging.
        ###############################################################################
        make_sure_path_exists(dicebox_config.LOGS_DIR)
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p',
            level=logging.INFO,
            filemode='w',
            filename="%s/primordialpool.%s.log" % (dicebox_config.LOGS_DIR, os.uname()[1])
        )
        logging.info("***Evolving %d generations with population %d***" % (dicebox_config.GENERATIONS, dicebox_config.POPULATION))
        pool: PrimordialPool = PrimordialPool(config=dicebox_config)
        pool.generate()


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(PrimordialPoolTest())
