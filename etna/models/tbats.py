from typing import List

import pandas as pd
import tbats

from etna.models.base import BaseAdapter
from etna.models.base import PerSegmentPredictionIntervalModel


class _TBATSAdapter(BaseAdapter):
    def __init__(self, model):
        self.model = model
        self.fitted_model = None

    def fit(self, df: pd.DataFrame, regressors: List[str]):
        target = df["target"]
        self.fitted_model = self.model.fit(target)
        return self

    def predict(self, df: pd.DataFrame, prediction_interval, quantiles) -> pd.DataFrame:
        y_pred = pd.DataFrame()
        if prediction_interval:
            for quantile in quantiles:
                pred, confidence_intervals = self.fitted_model.forecast(steps=df.shape[0], confidence_level=quantile)
                y_pred["target"] = pred
                if quantile < 1 / 2:
                    y_pred[f"target_{quantile:.4g}"] = confidence_intervals["lower_bound"]
                else:
                    y_pred[f"target_{quantile:.4g}"] = confidence_intervals["upper_bound"]
        else:
            pred = self.fitted_model.forecast(steps=df.shape[0])
            y_pred["target"] = pred
        return y_pred

    def get_model(self):
        return self.model


class _TBATSPerSegmentModel(PerSegmentPredictionIntervalModel):
    def __int__(self, model):
        super().__init__(base_model=model)


class BATSPerSegmentModel(_TBATSPerSegmentModel):
    """
    Class for holding per segment interval BATS model for
    """
    def __init__(self, **kwargs):
        """
        Parameters
        ----------
        kwargs
            Parameters for BATS model
        """
        self.kwargs = kwargs
        self.model = tbats.BATS(**kwargs)
        super().__init__(_TBATSAdapter(self.model))


class TBATSPerSegmentModel(_TBATSPerSegmentModel):
    """
        Class for holding per segment interval TBATS model for
    """
    def __init__(self, **kwargs):
        """
        Parameters
        ----------
        kwargs
            Parameters for TBATS model
        """
        self.kwargs = kwargs
        self.model = tbats.TBATS(**kwargs)
        super().__init__(_TBATSAdapter(self.model))
