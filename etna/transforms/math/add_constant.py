import warnings
from typing import Optional

import pandas as pd

from etna.transforms.base import Transform
from etna.transforms.utils import match_target_quantiles


class AddConstTransform(Transform):
    """AddConstTransform add constant for given series."""

    def __init__(self, in_column: str, value: float, inplace: bool = True, out_column: Optional[str] = None):
        """
        Init AddConstTransform.

        Parameters
        ----------
        in_column:
            column to apply transform
        value:
            value that should be added to the series
        inplace:

            * if True, apply add constant transformation inplace to in_column,

            * if False, add transformed column to dataset

        out_column:
            name of added column. If not given, use ``self.__repr__()``
        """
        self.in_column = in_column
        self.value = value
        self.inplace = inplace
        self.out_column = out_column

        if self.inplace and out_column:
            warnings.warn("Transformation will be applied inplace, out_column param will be ignored")

    def _get_column_name(self) -> str:
        if self.inplace:
            return self.in_column
        elif self.out_column:
            return self.out_column
        else:
            return self.__repr__()

    def fit(self, df: pd.DataFrame) -> "AddConstTransform":
        """Fit method does nothing and is kept for compatibility.

        Parameters
        ----------
        df:
            dataframe with data.

        Returns
        -------
        result: AddConstTransform
        """
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply adding constant to the dataset.

        Parameters
        ----------
        df:
            dataframe with data to transform.

        Returns
        -------
        result: pd.Dataframe
            transformed dataframe
        """
        segments = sorted(set(df.columns.get_level_values("segment")))

        result = df.copy()
        features = df.loc[:, pd.IndexSlice[segments, self.in_column]]
        transformed_features = features + self.value
        if self.inplace:
            result.loc[:, pd.IndexSlice[segments, self.in_column]] = transformed_features
        else:
            column_name = self._get_column_name()
            transformed_features.columns = pd.MultiIndex.from_product([segments, [column_name]])
            result = pd.concat((result, transformed_features), axis=1)
            result = result.sort_index(axis=1)
        return result

    def inverse_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply inverse transformation to the dataset.

        Parameters
        ----------
        df:
            dataframe with data to transform.

        Returns
        -------
        result: pd.DataFrame
            transformed series
        """
        result = df.copy()
        if self.inplace:
            segments = sorted(set(df.columns.get_level_values("segment")))
            features = df.loc[:, pd.IndexSlice[segments, self.in_column]]
            transformed_features = features - self.value
            result.loc[:, pd.IndexSlice[segments, self.in_column]] = transformed_features
            if self.in_column == "target":
                segment_columns = result.columns.get_level_values("feature").tolist()
                quantiles = match_target_quantiles(set(segment_columns))
                for quantile_column_nm in quantiles:
                    features = df.loc[:, pd.IndexSlice[segments, quantile_column_nm]]
                    transformed_features = features - self.value
                    result.loc[:, pd.IndexSlice[segments, quantile_column_nm]] = transformed_features

        return result


__all__ = ["AddConstTransform"]
