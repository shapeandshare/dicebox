# from tensorflow.keras.callbacks import ModelCheckpoint
import logging
import os
from datetime import datetime
from typing import Union, Any

import numpy
from numpy import ndarray
from tensorflow.keras.callbacks import EarlyStopping

from .config.dicebox_config import DiceboxConfig
from .connectors.filesystem_connecter import FileSystemConnector
from .connectors.sensory_service_connector import SensoryServiceConnector
from .models.network import DropoutLayer, DenseLayer, Network, Optimizers
from .models.network_config import NetworkConfig


class DiceboxNetwork(Network):
    __accuracy: float

    __fsc: FileSystemConnector  # file system connector
    __ssc: SensoryServiceConnector  # sensory service connector

    # Helper: Early stopping.
    __early_stopper = EarlyStopping(patience=25)

    ##############################################################################
    # Feature disabled until a flipper can be added and the filenames created safely.
    # Since this now runs in a container some additional considerations must be made.
    ##############################################################################
    # Checkpoint
    # filepath = "%s/weights-improvement-{epoch:02d}-{val_acc:.2f}.hdf5" % __config.WEIGHTS_DIR
    # checkpoint = ModelCheckpoint(filepath, monitor='val_acc', verbose=1, save_best_only=True, mode='max')
    # __callbacks_list = [__early_stopper, checkpoint]

    __callbacks_list = [__early_stopper]

    def __init__(self,
                 config: DiceboxConfig,
                 network_config: Union[NetworkConfig, Union] = None,
                 create_fsc: bool = True,
                 disable_data_indexing: bool = False):

        super().__init__(config=config, network_config=network_config)

        self.__accuracy: float = 0.0

        if create_fsc is True:
            logging.debug('creating a new fsc..')
            logging.info('self.config.DATA_DIRECTORY: (%s)' % self.config.DATA_DIRECTORY)
            self.__fsc = FileSystemConnector(config=config,
                                             data_directory=self.config.DATA_DIRECTORY,
                                             disable_data_indexing=disable_data_indexing)
        else:
            logging.debug('creating a new ssc..')
            self.__ssc = SensoryServiceConnector(role='client', config=self.config)

    # ## Logging
    #
    # def print_network(self) -> None:
    #     """Print out a __network."""
    #     logging.info(self.__network)
    #     logging.info("Network accuracy: %.2f%%" % (self.__accuracy * 100))

    ## Training

    def train(self, update_accuracy=False) -> float:
        if self.config.DICEBOX_COMPLIANT_DATASET is True:
            x_train, x_test, y_train, y_test = self.get_dicebox_filesystem()
        else:
            raise Exception('Unknown dataset type!  Please define, or correct.')

        self.compile()

        self.model.fit(x_train, y_train,
                       batch_size=self.config.BATCH_SIZE,
                       epochs=10000,  # using early stopping, so no real limit
                       verbose=1,
                       validation_data=(x_test, y_test),
                       callbacks=[self.__early_stopper])

        score = self.model.evaluate(x_test, y_test, verbose=0)

        if update_accuracy is True:
            self.__accuracy = score

        return score[1]  # 1 is accuracy. 0 is loss.

    # careful now.. maybe this shouldn't exist..
    def set_accuracy(self, accuracy: float):
        self.__accuracy = accuracy

    def get_accuracy(self) -> float:
        return self.__accuracy

    ## Prediction

    def classify(self, network_input: Any) -> ndarray:
        if self.config.DICEBOX_COMPLIANT_DATASET is True:
            x_test: ndarray = self.__get_dicebox_raw(network_input)
        else:
            logging.error("UNKNOWN DATASET (%s) passed to classify" % self.config.NETWORK_NAME)
            raise Exception("UNKNOWN DATASET (%s) passed to classify" % self.config.NETWORK_NAME)

        if self.__network.model is None:
            logging.error('Unable to classify without a model.')
            raise Exception('Unable to classify without a model.')

        model_prediction: ndarray = self.__network.model.predict_classes(x_test, batch_size=1, verbose=0)
        logging.info(model_prediction)

        return model_prediction

    ## Weights Storage Functions

    def save_model_weights(self, filename: str) -> None:
        if self.__network.model is None:
            logging.error('No model! Compile the network first.')
            raise Exception('No model! Compile the network first.')

        logging.debug('loading weights file..')
        try:
            self.__network.model.save_weights(str(filename))  # https://github.com/keras-team/keras/issues/11269
        except Exception as e:
            logging.error('Unable to save weights file.')
            logging.error(e)
            raise e

    def load_model_weights(self, filename: str) -> None:
        if self.__network.model is None:
            logging.error('No model! Compile the network first.')
            raise Exception('No model! Compile the network first.')

        logging.debug('loading weights file..')
        try:
            self.__network.model.load_weights(str(filename))  # https://github.com/keras-team/keras/issues/11269
        except Exception as e:
            logging.error('Unable to load weights file.')
            logging.error(e)
            raise e

    ## Data Centric Functions

    def __get_dicebox_raw(self, raw_image_data: Any) -> ndarray:
        # TODO: variable reuse needs to be cleaned up..

        # ugh dump to file for the time being
        filename = "%s/%s" % (self.config.TMP_DIR, datetime.now().strftime('%Y-%m-%d_%H_%M_%S_%f.tmp.png'))
        with open(filename, 'wb') as f:
            f.write(raw_image_data)

        try:
            test_image_data = self.__fsc.process_image(filename)
        except:
            logging.error('Exception caught processing image data.')
            raise Exception('Exception caught processing image data.')
        finally:
            os.remove(filename)

        test_image_data = numpy.array(test_image_data)
        test_image_data = test_image_data.astype('float32')
        test_image_data /= 255

        x_test = [test_image_data]
        x_test = numpy.array(x_test)

        return x_test

    def get_dicebox_filesystem(self) -> [ndarray, ndarray, ndarray, ndarray]:
        noise = self.config.NOISE
        test_batch_size = self.config.TEST_BATCH_SIZE
        train_batch_size = self.config.TRAIN_BATCH_SIZE

        logging.info('noise: %s' % noise)
        logging.info('train_batch_size: %s' % train_batch_size)
        logging.info('test_batch_size: %s' % test_batch_size)

        train_image_data, train_image_labels = self.__fsc.get_batch(train_batch_size, noise=noise)
        # train_image_data, train_image_labels = Network.__ssc.get_batch(train_batch_size, noise=noise)
        train_image_data = numpy.array(train_image_data)
        train_image_data = train_image_data.astype('float32')
        train_image_data /= 255
        train_image_labels = numpy.array(train_image_labels)

        test_image_data, test_image_labels = self.__fsc.get_batch(test_batch_size, noise=noise)
        # test_image_data, test_image_labels = Network.__ssc.get_batch(test_batch_size, noise=noise)
        test_image_data = numpy.array(test_image_data)
        test_image_data = test_image_data.astype('float32')
        test_image_data /= 255
        test_image_labels = numpy.array(test_image_labels)

        x_train: ndarray = train_image_data
        x_test: ndarray = test_image_data
        y_train: ndarray = train_image_labels
        y_test: ndarray = test_image_labels

        return x_train, x_test, y_train, y_test

    def get_dicebox_sensory_data(self) -> [ndarray, ndarray, ndarray, ndarray]:
        logging.debug('-' * 80)
        logging.debug('get_dicebox_sensory_data(self)')
        logging.debug('-' * 80)

        noise = self.config.NOISE
        train_batch_size = self.config.TRAIN_BATCH_SIZE
        test_batch_size = self.config.TEST_BATCH_SIZE

        try:
            # train_image_data, train_image_labels = Network.__fsc.get_batch(train_batch_size, noise=noise)
            train_image_data, train_image_labels = self.__ssc.get_batch(train_batch_size, noise=noise)

            logging.debug('-' * 80)
            logging.debug('train_image_data to numpy.array')
            # logging.debug(train_image_data)

            train_image_data = numpy.array(train_image_data)
            # logging.debug(train_image_data)

            logging.debug('train_image_data astype float32')
            train_image_data = train_image_data.astype('float32')
            # logging.debug(train_image_data)

            logging.debug('train_image_data /255')
            train_image_data /= 255
            # logging.debug(train_image_data)

            logging.debug('train_image_labels to numpy.array')
            train_image_labels = numpy.array(train_image_labels)
            # logging.debug(train_image_labels)
            logging.debug('-' * 80)
        except ValueError:
            logging.debug('Caught ValueError when processing training data.')
            logging.debug('failing out..')
            raise ValueError

        try:
            # test_image_data, test_image_labels = Network.__fsc.get_batch(test_batch_size, noise=noise)
            test_image_data, test_image_labels = self.__ssc.get_batch(test_batch_size, noise=noise)

            logging.debug('-' * 80)
            logging.debug('test_image_data to numpy.array')
            # logging.debug(test_image_data)

            test_image_data = numpy.array(test_image_data)
            # logging.debug(test_image_data)

            logging.debug('test_image_data astype float32')
            test_image_data = test_image_data.astype('float32')
            # logging.debug(test_image_data)

            logging.debug('test_image_data /255')
            test_image_data /= 255
            # logging.debug(test_image_data)

            logging.debug('test_image_labels to numpy.array')
            test_image_labels = numpy.array(test_image_labels)
            # logging.debug(test_image_labels)
        except ValueError:
            logging.debug('Caught ValueError when processing test data.')
            logging.debug('failing out..')
            raise ValueError

        x_train: ndarray = train_image_data
        x_test: ndarray = test_image_data
        y_train: ndarray = train_image_labels
        y_test: ndarray = test_image_labels
        return x_train, x_test, y_train, y_test

    ## Network Functions

    def load_network(self, network: Network) -> None:
        self.__network = network

        # reset other items related to a newly loaded network
        self.__accuracy = 0.0

    ## For Evolutionary Optimizer

    def get_optimizer(self) -> Optimizers:
        return self.__network.optimizer

    def get_layer_count(self) -> int:
        return len(self.__network.layers)

    def get_layer(self, layer_index: int) -> Union[DenseLayer, DropoutLayer]:
        return self.__network.get_layer_definition(layer_index)

    def get_config(self) -> DiceboxConfig:
        return self.config
