import pickle
import json
import time
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, PowerTransformer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.decomposition import FastICA, KernelPCA
from .cluster_clf_model import ClusterClf
from .nn_model import NNModel
from .model_filter import OutlierPipeline

# TODO: Add discarding of unnecessary features inside this class
class ModelPipeline:
    def __init__(self, steps=None, model_filter=None):
        """
        Initializes the model pipeline.

        Parameters:
        - steps (list): List of (name, transformer/model) tuples representing the pipeline stages.
        """
        if steps is None:
            steps = [
                ('scaler', PowerTransformer()),
                ('classifier', GradientBoostingClassifier())
            ]
        
        self.pipeline = Pipeline(steps)
        self.time_spent = 0
        self.predict_counter = 0
        self.frozen_steps = set()  # To track frozen steps
        self.model_filter= model_filter

    @staticmethod
    def from_config(config_path_str):
        """
        Loads the pipeline from a configuration file.

        Parameters:
        - config_path_str (str): Path to the JSON configuration file.

        Returns:
        - ModelPipeline instance.
        """
        with open(config_path_str, 'r') as json_file:
            config = json.load(json_file)

        config_path = Path(config_path_str)
        config_dir = config_path.parent.absolute()

        steps = []
        for name, path in config['steps'].items():
            with open(config_dir.joinpath(path), 'rb') as f:
                steps.append((name, pickle.load(f)))
                print(f"load from {path}")

        model_filter = None
        if 'model_filter' in config.keys():
            with open(config_dir.joinpath(config['model_filter']), 'rb') as f:
                model_filter = pickle.load(f)

        return ModelPipeline(steps, model_filter)

    def save_to_config(self, base_path_str):
        """
        Saves the pipeline to individual files and generates a JSON description of the pipeline.

        Parameters:
        - base_path_str (str): Base path to save the pipeline components.

        Returns:
        - Path to the generated JSON configuration file.
        """
        pipeline_structure = {}

        base_path = Path(base_path_str)

        for name, step in self.pipeline.named_steps.items():
            step_path_str = f"{name}.pkl"
            with open(base_path.joinpath(step_path_str), 'wb') as f:
                pickle.dump(step, f)
            pipeline_structure[name] = step_path_str

        config_js = {'steps': pipeline_structure}
        if self.model_filter is None:
            model_filter_path_str = "model_filter.pkl"
            model_filter_path = base_path.joinpath(model_filter_path_str)
            with open(model_filter_path, 'wb') as f:
                pickle.dump(self.model_filter, f)
            config_js['model_filter'] = model_filter_path_str

        config_path = base_path.joinpath(f"pipeline_config.json")
        with open(config_path, 'w') as json_file:
            json.dump(config_js, json_file, indent=4)

        return config_path

    def fit(self, X, y=None):
        """
        Fits the pipeline to the data.

        Parameters:
        - X (array-like): Input features.
        - y (array-like, optional): Target labels.
        """
        for name, step in self.pipeline.named_steps.items():
            if name not in self.frozen_steps:
                if hasattr(step, 'fit'):
                    if y is not None:
                        step.fit(X, y)
                    else:
                        step.fit(X)
            if hasattr(step, 'transform'):
                X = step.transform(X)

    def freeze_step(self, step_name):
        """
        Freezes a specific step in the pipeline (prevents it from being re-trained).

        Parameters:
        - step_name (str): Name of the step to freeze.
        """
        if step_name in self.pipeline.named_steps:
            self.frozen_steps.add(step_name)
        else:
            raise ValueError(f"Step {step_name} not found in the pipeline.")

    def unfreeze_step(self, step_name):
        """
        Unfreezes a specific step in the pipeline (allows it to be re-trained).

        Parameters:
        - step_name (str): Name of the step to unfreeze.
        """
        self.frozen_steps.discard(step_name)

    def time_count_decorator(func):
        def wrapper(self, *args, **kwargs):
            if self.predict_counter > 300:
                self.time_spent = 0
                self.predict_counter = 0

            start_time = time.time()
            ret = func(self, *args, **kwargs)
            self.time_spent += time.time() - start_time
            self.predict_counter += 1
            return ret
        return wrapper

    def get_average_time_spent(self):
        """Returns the average prediction time."""
        return self.time_spent / max(self.predict_counter, 1)

    @time_count_decorator
    def predict(self, X):
        """
        Predicts using the pipeline.

        Parameters:
        - X (array-like): Input features.

        Returns:
        - Predictions from the pipeline's final stage.
        """
        X = X[self.pipeline.feature_names_in_]
        for name, step in self.pipeline.named_steps.items():
            if hasattr(step, 'transform'):
                X = step.transform(X)
        return self.pipeline.named_steps['classifier'].predict(X)

    def filter(self, X):
        return self.model_filter.predict(X)


if __name__ == "__main__":
    # Example config for saving/loading pipeline
    base_path = 'model_pipeline'

    # Initialize and train a pipeline
    pipeline = ModelPipeline()
    X_train, y_train = [[1, 2, 3], [1, 2, 3], [1, 2, 3]], [1, 0, 1]   # Load your training data here
    pipeline.fit(X_train, y_train)

    # Freeze the scaler step
    pipeline.freeze_step('scaler')

    # Save the pipeline components and structure
    config_path = pipeline.save_to_config(base_path)
    print(f"Pipeline configuration saved to {config_path}")

    # Load the pipeline components
    loaded_pipeline = ModelPipeline.from_config(config_path)

    # Make predictions
    X_test = [[1, 2, 3]]  # Load your test data here
    predictions = loaded_pipeline.predict(X_test)
    print(predictions)