from typing import List, Union, Any

from tensorflow.python.keras.layers import Dropout, Dense
from tensorflow.python.keras.models import Sequential

from .layer import DenseLayer, DropoutLayer, LayerType, ActivationFunction
from .network_config import NetworkConfig
from .optimizers import Optimizers
from ..config.dicebox_config import DiceboxConfig
from ..factories.layer_factory import LayerFactory


class Network(LayerFactory):
    def __init__(self, config: DiceboxConfig, network_config: Union[NetworkConfig, None]):
        super().__init__(config=config)

        # allow a null startup state
        if network_config is not None:
            self.__input_shape: int = network_config.input_shape
            self.__output_size: int = network_config.output_size
            self.__optimizer: Optimizers = network_config.optimizer

            self.__layers: List[Union[DenseLayer, DropoutLayer]] = network_config.layers
            self.model = None
            self.compile()

    def add_layer(self, layer: Union[DropoutLayer, DenseLayer]) -> None:
        self.__layers.append(layer)

    def __clear_model(self):
        if self.model:
            del self.model
        self.model = None

    def compile(self) -> None:
        self.__clear_model()

        # early exist for empty layers
        if len(self.__layers) < 1:
            return

        model = Sequential()

        first_layer: bool = True
        for layer in self.__layers:
            # build and add layer
            if layer.layer_type == LayerType.DROPOUT:
                # handle dropout
                model.add(Dropout(layer.rate))
            elif layer.layer_type == LayerType.DENSE:
                neurons: int = layer.size
                activation: ActivationFunction = layer.activation
                if first_layer is True:
                    first_layer = False
                    model.add(Dense(neurons, activation=activation.value, input_shape=self.__input_shape))
                else:
                    model.add(Dense(neurons, activation=activation.value))
            else:
                raise
        # add final output layer.
        model.add(Dense(self.__output_size,
                        activation='softmax'))  # TODO: Make it possible to define with from the enum...
        model.compile(loss='categorical_crossentropy', optimizer=self.__optimizer.value, metrics=['accuracy'])

        # return model
        self.model = model

    def get_layer(self, layer_index: int) -> Union[DenseLayer, DropoutLayer]:
        return self.__layers[layer_index]

    def get_layers(self) -> List[Union[DenseLayer, DropoutLayer]]:
        return self.__layers

    def get_optimizer(self) -> Optimizers:
        return self.__optimizer

    def get_input_shape(self) -> int:
        return self.__input_shape

    def get_output_size(self) -> int:
        return self.__output_size

    def decompile(self) -> Any:
        definition = {
            'input_shape': self.__input_shape,
            'output_size': self.__output_size,
            'optimizer': self.__optimizer.value,
            'layers': []
        }

        for i in range(0, len(self.__layers)):
            layer = self.decompile_layer(self.__layers[i])
            definition['layers'].append(layer)

        return definition

