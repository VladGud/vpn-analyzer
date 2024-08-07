import time
import pickle
from sklearn.decomposition import FastICA
from sklearn.preprocessing import PowerTransformer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

# TODO: Create normal pipeline
# TODO: Add discarding of unnecessary features inside this class
# TODO: Add a model download from the config
class ModelPipeline():
    def __init__(self, clf=None, n_components=8, ica=None, power_transformer=None):
        self.clf_model = clf
        self.ica_model = ica if ica else FastICA(n_components=n_components, algorithm='deflation', fun='exp', whiten='unit-variance')
        self.power_transformer = power_transformer if power_transformer else PowerTransformer()
        self.time_spent = 0
        self.predict_counter = 0

    @staticmethod
    def load_models(power_transformer_model_path, ica_model_path, clf_model_path):
        with open(str(clf_model_path), "rb") as f:
            clf_model = pickle.load(f)

        with open(str(power_transformer_model_path), "rb") as f:
            power_transformer = pickle.load(f)

        with open(str(ica_model_path), "rb") as f:
            ica_model = pickle.load(f)

        return ModelPipeline(clf=clf_model, power_transformer=power_transformer, ica=ica_model)

    def save_models(self, power_transformer_model_path, ica_model_path, clf_model_path):
        with open(str(clf_model_path), "wb") as f:
            pickle.dump(self.clf_model, f)

        with open(str(power_transformer_model_path), "wb") as f:
            pickle.dump(self.power_transformer, f)

        with open(str(ica_model_path), "wb") as f:
            pickle.dump(self.ica_model, f)

    def fit(self, X, y=None):
        self.power_transformer.fit(X)
        scaled_X = self.power_transformer.transform(X)

        self.ica_model.fit(scaled_X)
        X_ica = self.ica_model.transform(scaled_X)

        if y is not None:
            self.clf_model.fit(X_ica, y)
        else:
            self.clf_model.fit(X_ica)

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
        return self.time_spent / self.predict_counter

    @time_count_decorator
    def predict(self, X):
        useful_X = X[self.power_transformer.feature_names_in_]
        scaled_X = self.power_transformer.transform(useful_X)
        X_ica = self.ica_model.transform(scaled_X)
        return self.clf_model.predict(X_ica)