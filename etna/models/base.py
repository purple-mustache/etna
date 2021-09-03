from abc import ABC
from abc import abstractmethod
from copy import deepcopy
from typing import List
from typing import Union

import pandas as pd

from etna.datasets.tsdataset import TSDataset


class Model(ABC):
    """Class for holding specific models - autoregression and simple regressions."""

    def __init__(self):
        self._models = None

    @abstractmethod
    def fit(self, ts: TSDataset) -> "Model":
        """Fit model.

        Parameters
        ----------
        ts:
            Dataframe with features
        Returns
        -------
        """
        pass

    @abstractmethod
    def forecast(self, ts: TSDataset) -> TSDataset:
        """Make predictions.

        Parameters
        ----------
        ts:
            Dataframe with features
        Returns
        -------
        DataFrame
            Models result
        """
        pass

    @staticmethod
    def _forecast_segment(model, segment: Union[str, List[str]], ts: TSDataset) -> pd.DataFrame:
        segment_features = ts[:, segment, :]
        segment_features = segment_features.droplevel("segment", axis=1)
        segment_features = segment_features.reset_index()
        dates = segment_features["timestamp"]
        dates.reset_index(drop=True, inplace=True)
        segment_predict = model.predict(df=segment_features)
        segment_predict = pd.DataFrame({"target": segment_predict})
        segment_predict["segment"] = segment
        segment_predict["timestamp"] = dates
        return segment_predict


class PerSegmentModel(Model):
    """Class for holding specific models for persegment prediction."""

    def __init__(self, base_model):
        super(PerSegmentModel, self).__init__()
        self._base_model = base_model
        self._segments = None

    def fit(self, ts: TSDataset) -> "PerSegmentModel":
        """Fit model."""
        self._segments = ts.segments
        self._build_models()

        for segment in self._segments:
            model = self._models[segment]
            segment_features = ts[:, segment, :]
            segment_features = segment_features.dropna()
            segment_features = segment_features.droplevel("segment", axis=1)
            segment_features = segment_features.reset_index()
            model.fit(df=segment_features)
        return self

    def forecast(self, ts: TSDataset) -> TSDataset:
        """Make predictions.

        Parameters
        ----------
        ts:
            Dataframe with features
        Returns
        -------
        DataFrame
            Models result
        """
        """df = dataset.to_pandas(flatten=True)
        df = df[df["target"].isna()]
        if any(df.drop(columns="target").isna().any()):
            raise ValueError("Dataset contains NaN values on the forecast side", df.columns[df.isna().any()].tolist())
        df.sort_values(by=["segment", "timestamp"], inplace=True)"""

        result_list = list()
        for segment in self._segments:
            model = self._models[segment]

            segment_predict = self._forecast_segment(model, segment, ts)
            result_list.append(segment_predict)

        # need real case to test
        result_df = pd.concat(result_list, ignore_index=True)
        result_df = result_df.set_index(["timestamp", "segment"])
        df = ts.to_pandas(flatten=True)
        df = df.set_index(["timestamp", "segment"])
        df = df.combine_first(result_df).reset_index()

        df = TSDataset.to_dataset(df)
        ts.df = df
        ts.inverse_transform()
        return ts

    def _build_models(self):
        """Create a dict with models for each segment (if required)."""
        self._models = {}
        for segment in self._segments:
            self._models[segment] = deepcopy(self._base_model)
