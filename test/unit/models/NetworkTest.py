import os
import unittest

from src.config.dicebox_config import DiceboxConfig
from src.config.network_config import NetworkConfig
from src.factories.network_factory import NetworkFactory
from src.models.optimizers import Optimizers


class NetworkTest(unittest.TestCase):
    TEST_DATA_BASE = 'test/fixtures'
    local_config_file = '%s/dicebox.config' % TEST_DATA_BASE

    dicebox_config: DiceboxConfig = DiceboxConfig(config_file=local_config_file)
    network_factory: NetworkFactory = NetworkFactory(config=dicebox_config)

    def setUp(self):
        self.maxDiff = None

    def test_clear_model(self):
        network = self.network_factory.create_random_network()
        network.compile()

    def test_getters(self):
        definition = {
            'input_shape': 1,
            'output_size': 1,
            'optimizer': Optimizers.ADAM.value
        }
        network = self.network_factory.create_network(network_definition=definition)
        self.assertEqual(network.get_input_shape(), 1)
        self.assertEqual(network.get_output_size(), 1)



if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(NetworkTest())