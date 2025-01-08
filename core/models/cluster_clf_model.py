import numpy as np
from collections import defaultdict
from sklearn.cluster import KMeans

class ClusterClf:
    def __init__(self, cluster_model):
        self._cluster_model = cluster_model
        self._cluster_to_class_dict = None

    @staticmethod
    def assign_clusters_to_classes(clusters, class_labels):
        cluster_to_class_count = defaultdict(lambda: defaultdict(int))
        for cluster, class_label in zip(clusters, class_labels):
            cluster_to_class_count[cluster][class_label] += 1
        cluster_to_class_dict_temp = {}
        for cluster, class_count in cluster_to_class_count.items():
            most_common_class = max(class_count, key=class_count.get)
            cluster_to_class_dict_temp[cluster] = most_common_class
        class_to_clusters_dict = defaultdict(list)
        for cluster, class_label in cluster_to_class_dict_temp.items():
            class_to_clusters_dict[class_label].append(cluster)
    
        return dict(class_to_clusters_dict)

    def encode_cluster_to_class(self, labels, cluster_to_class_dict):
        if (self._cluster_to_class_dict is None):
            print("ClusterClf was not trainned")
            return []
        
        labels_copy = labels.copy()
        for label_class, clusters in cluster_to_class_dict.items():
            mask = np.isin(labels, clusters)
            labels_copy[mask] = label_class
        return labels_copy

    def fit(self, X, y):
        clusters = self._cluster_model.fit_predict(X)
        self._cluster_to_class_dict = self.assign_clusters_to_classes(clusters, y)

    def predict(self, X):
        clusters = self._cluster_model.predict(X)
        return self.encode_cluster_to_class(clusters, self._cluster_to_class_dict)