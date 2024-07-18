# Проект обнаружение VPN соединений

## Актуальные версия моделей
Наиболее [актуальные](./models/interval-27-30-reality-0_915) версии моделей поддерживает детекцию протокола [xtls-reality](https://github.com/XTLS/Xray-core)

## Предподготовка
Для запуска скриптов требуется наличие `Python` версии `3.11`. Для установки требуемой версии можно воспользоваться утилитой [pyenv](https://github.com/pyenv/pyenv).

Скрипты запускаются в виртуальном окружении `pipenv`.

Установка `pipenv`:

```
pip install pipenv
```

или

```
pip3 install pipenv
```

Создание виртуального окружения (запуск из текущей директории):

```
pipenv install
```

Подключение к виртуальному окружению (запуск из текущей директории):

```
pipenv shell
```

## Описание текущих исследований
[Данные](./vpn-data) были извлечены из реального трафика собранного приложениями: [xray-windows/xray-linux](https://github.com/XTLS/Xray-core/releases), [v2rayng-android](https://github.com/2dust/v2rayNG/releases), [FoXray](https://foxray.org/)

Подробнее ознакомится с фичами можно из исходного [кода](./core/feature)

ModelPipeline:
1) Скейлинг данных и нормализация данных (приведение к нормальному распределению) -- yeo-johnson PowerTransformer поскольку имеются нулевые значения признаков.
2) Декомпозиция данных -- FastICA был взять за основу, поскольку данный метод не зацикливается на линейности и многомерной нормальности исходных признаков. Признаки даже после применения PowerTransformer() не всегда соотвествуют нормальному распределению.
3) Классификация данных -- RandomForest и GradientBoosting показывают наиболее лучшие результаты с FastICA

Рассматривались также:
- StandardScaler, но показал хуже результаты с FastICA и PCA (поскольку данные были не нормализованы)
- PCA не пременим в нашем случае в чистом виде, поскольку исходные данные не подразумевают многомерной нормальности, а преобразование PowerTransformer не решает полностью проблему многомерной нормальности
- PCA + FastICA комбинация также не применима, поскольку фильтрация признаков относительно их корреляции отбрасывает информацию о незовисимости компонент, тем самым ухудшая результаты классификации

Одна из преимущественных идей использовать FastICA -- эта возможность разложения мультиплексированных VPN потоков по независимым компонентам и тем самым повышая точность детектирования.

[Notebook](./model-analyzer.ipynb) содержит часть проведенных исследований и может быть полезен для понимания

## Описание демо-приложения
Демо-приложение может быть полезно для тестирования собственных предобученных моделей в реальном времени. Данное дополнение выводит различную статистику о детектированных потоках и текущем количестве обрабатываемых потоков.
```
usage: vpn_detect.py [-h] -p MODELS_PATH [-s START_THRESHOLD] [-e END_THRESHOLD] [-f FLOW_STORAGE_SIZE]

options:
  -h, --help            show this help message and exit
  -p MODELS_PATH, --models_path MODELS_PATH
                        Directory with datasets (default: None)
  -s START_THRESHOLD, --start_threshold START_THRESHOLD
                        Starting from which package to detect (default: 27)
  -e END_THRESHOLD, --end_threshold END_THRESHOLD
                        After flow has processed a given number of packets, delete it from the processing queue. (default: 30)
  -f FLOW_STORAGE_SIZE, --flow_storage_size FLOW_STORAGE_SIZE
                        Set the maximum allowed number of threads to be processed. If exceeded, the oldest flow will be destroyed (default: 100)
```

Пример запуска:
```shell
$ python3 vpn_detect.py -p models/interval-27-30-reality-0_915 -f 100
```


## TODO
- [ ] Реализовать пайплайн моделей детекции (классификация сразу нескольких протоколов)
- [ ] Отрефакторить ModelPipeline: фильтрация входных фреймов на этапе predict и добавить возможность создавать любое количество трансформеров
- [ ] Рассмотреть повышение точности предсказания на основе двунаправленных LSTM
- [ ] Рассмотреть возможность добавление направленных признаков
- [ ] Рассмотреть сдвиг данных и нормализация данных box-cox
- [ ] Рассмотреть возможность добавить определение типа контента передаваемого в рамках потока
- [ ] Рассмотреть возможность добавить определение типа протокола использованного для организации VPN
- [ ] Проверить идею про разложение мультеплексированного трафика VPN
