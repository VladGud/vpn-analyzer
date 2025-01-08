import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from .outliners import OutlierDetector, DBSCANWrapper

class OutlierPipeline:
    def __init__(self, zscore_model=None, lof_pipeline=None, dbscan_pipeline=None):
        """
        Инициализация пайплайна для последовательного предсказания выбросов.

        Parameters:
        - zscore_model: Модель Z-Score для определения выбросов.
        - lof_pipeline: Модель Local Outlier Factor (LOF).
        - dbscan_pipeline: DBSCAN пайплайн (обучение и предсказание).
        """
        self.zscore_model = zscore_model
        self.lof_pipeline = lof_pipeline
        self.dbscan_pipeline = dbscan_pipeline

    def predict(self, dataframe):
        """
        Предсказать выбросы с использованием всех моделей по очереди.

        Parameters:
        - dataframe (pd.DataFrame): Входной DataFrame.

        Returns:
        - pd.Series: Булевый массив (True - выброс, False - нормальная строка).
        """
        # Инициализация результата
        outliers = pd.Series(False, index=dataframe.index)

        # 1. Прогноз Z-Score модели
        if self.zscore_model:
            zscore_outliers = self.zscore_model.predict(dataframe)
            outliers |= zscore_outliers

        # Оставшиеся данные после Z-Score
        remaining_data = dataframe[~outliers]

        # 2. Прогноз LOF модели
        if self.lof_pipeline and not remaining_data.empty:
            remaining_data = remaining_data[self.lof_pipeline.feature_names_in_]
            lof_outliers = pd.Series(self.lof_pipeline.predict(remaining_data) == -1, index=remaining_data.index)
            outliers |= lof_outliers

        # Оставшиеся данные после LOF
        remaining_data = dataframe[~outliers]

        # 3. Прогноз DBSCAN пайплайна
        if self.dbscan_pipeline and not remaining_data.empty:
            remaining_data = remaining_data[self.dbscan_pipeline.feature_names_in_]
            dbscan_labels = self.dbscan_pipeline.predict(remaining_data)
            dbscan_outliers = pd.Series(dbscan_labels == -1, index=remaining_data.index)
            outliers |= dbscan_outliers

        return outliers