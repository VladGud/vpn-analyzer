import pickle
from sklearn.decomposition import FastICA
from sklearn.preprocessing import PowerTransformer

class ModelPipeline:
    def __init__(self, clf):
        self.clf_model = clf
        self.ica_model = FastICA(n_components=8, algorithm='deflation', fun='exp', whiten='unit-variance')
        self.power_transformer = PowerTransformer()

    def load_models(self, power_transformer_model_path, ica_model_path, clf_model_path):
        with open(clf_model_path, "rb") as f:
            self.clf_model = pickle.load(f)

        with open(power_transformer_model_path, "rb") as f:
            self.power_transformer = pickle.load(f)

        with open(ica_model_path, "rb") as f:
            self.ica_model = pickle.load(f)

    def save_models(self, power_transformer_model_path, ica_model_path, clf_model_path):
        with open(clf_model_path, "wb") as f:
            pickle.dump(self.clf_model, f)

        with open(power_transformer_model_path, "wb") as f:
            pickle.dump(self.power_transformer, f)

        with open(ica_model_path, "wb") as f:
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

    def predict(self, X):
        scaled_X = self.power_transformer.transform(X)
        X_ica = self.ica_model.transform(scaled_X)
        return self.clf_model.predict(X_ica)