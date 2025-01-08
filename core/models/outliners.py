import pandas as pd
import numpy as np
import scipy as sp
from sklearn.cluster import DBSCAN

class DBSCANWrapper(DBSCAN):
    def predict(self, X_new):
        y_new = np.ones(shape=len(X_new), dtype=int)*-1 
        for j, x_new in enumerate(X_new):
            for i, x_core in enumerate(self.components_): 
                if sp.spatial.distance.cosine(x_new, x_core) < self.eps:
                    y_new[j] = self.labels_[self.core_sample_indices_[i]]
                    break
        return y_new

class OutlierDetector:
    def __init__(self, group_column, feature_columns, z_score_threshold=3):
        """
        Инициализация детектора выбросов.

        Parameters:
        - group_column (str): Колонка для группировки данных.
        - feature_columns (list): Список фичей для проверки на выбросы.
        - z_score_threshold (float): Порог для определения выбросов.
        """
        self.group_column = group_column
        self.feature_columns = feature_columns
        self.z_score_threshold = z_score_threshold
        self.stats_ = {}  # Хранение mean и std для каждой группы

    def fit(self, dataframe):
        """
        Вычисляет статистики (mean и std) для каждой группы и фичи.

        Parameters:
        - dataframe (pd.DataFrame): Входной DataFrame.
        """
        self.stats_ = {
            feature: dataframe.groupby(self.group_column)[feature].agg(['mean', 'std']).to_dict('index')
            for feature in self.feature_columns
        }

    def predict(self, dataframe):
        """
        Предсказывает, является ли каждая строка выбросом.

        Parameters:
        - dataframe (pd.DataFrame): Входной DataFrame.

        Returns:
        - pd.Series: Булевый массив, где True - выброс, False - нормальная строка.
        """
        is_outlier = pd.Series(False, index=dataframe.index)

        # Обходим все фичи и вычисляем выбросы
        for feature in self.feature_columns:
            group_stats = self.stats_.get(feature, {})

            # Преобразуем статистики в DataFrame
            stats_df = pd.DataFrame(group_stats).T.rename_axis(self.group_column)

            # Соединяем исходный DataFrame с рассчитанными статистиками
            merged = dataframe.merge(stats_df, on=self.group_column, how='left', suffixes=('', '_stats'))

            # Вычисляем z-скор
            z_scores = (merged[feature] - merged['mean']) / merged['std']

            # Выбросы: проверка по порогу
            feature_outliers = z_scores.abs() > self.z_score_threshold

            # Обновляем итоговый результат
            is_outlier |= feature_outliers.fillna(False)  # NaN (группы без данных) трактуем как False

        return is_outlier

    def fit_predict(self, dataframe):
        """
        Обучается на данных и предсказывает выбросы.

        Parameters:
        - dataframe (pd.DataFrame): Входной DataFrame.

        Returns:
        - pd.Series: Булевый массив, где True - выброс, False - нормальная строка.
        """
        self.fit(dataframe)
        return self.predict(dataframe)
