import numpy as np

def filter_outliners(array):
    array = np.array(array)
    q1, q3 = np.percentile(array, [25, 75])
    iqr = q3 - q1
    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)
    return array[(array >= lower_bound) & (array <= upper_bound)]