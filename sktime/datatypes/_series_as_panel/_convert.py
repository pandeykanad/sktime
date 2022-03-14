# -*- coding: utf-8 -*-
"""Machine type converters for Series to Panel.

Exports conversion functions for conversions between Series and Panel:

convert_Series_to_Panel(obj, store=None)
    converts obj of Series mtype to "adjacent" Panel mtype (e.g., numpy to numpy)
convert_Panel_to_Series(obj, store=None)
    converts obj of Panel mtype to "adjacent" Series mtype (e.g., numpy to numpy)
"""

__author__ = ["fkiraly"]

__all__ = ["convert_Series_to_Panel", "convert_Panel_to_Series"]

import numpy as np
import pandas as pd

from sktime.datatypes import convert_to, mtype, mtype_to_scitype


def convert_Series_to_Panel(obj, store=None):
    """Convert series to a single-series panel.

    Assumes input is conformant with one of the three Series mtypes.
    This method does not perform full mtype checks, use mtype or check_is_mtype for
    checks.

    Parameters
    ----------
    obj: an object of scitype Series, of mtype pd.DataFrame, pd.Series, or np.ndarray.

    Returns
    -------
    if obj was pd.Series or pd.DataFrame, returns a panel of mtype df-list
        this is done by possibly converting to pd.DataFrame, and adding a list nesting
    if obj was np.ndarray, returns a panel of mtype numpy3D, by adding one axis at end
    """
    if isinstance(obj, pd.Series):
        obj = pd.DataFrame(obj)

    if isinstance(obj, pd.DataFrame):
        return [obj]

    if isinstance(obj, np.ndarray):
        if len(obj.shape) == 2:
            obj = np.expand_dims(obj, 2)
        elif len(obj.shape) == 1:
            obj = np.expand_dims(obj, (1, 2))
        else:
            raise ValueError("if obj is np.ndarray, must be of dim 1 or 2")

    return obj


def convert_Panel_to_Series(obj, store=None):
    """Convert single-series panel to a series.

    Assumes input is conformant with one of three main panel mtypes.
    This method does not perform full mtype checks, use mtype or check_is_mtype for
    checks.

    Parameters
    ----------
    obj: an object of scitype Panel, of mtype pd-multiindex, numpy3d, or df-list.

    Returns
    -------
    if obj df-list or pd-multiindex, returns a series of type pd.DataFrame
    if obj was numpy3D, returns a panel mtype np.ndarray
    """
    if isinstance(obj, list):
        if len(obj) == 1:
            return obj[0]
        else:
            raise ValueError("obj must be of length 1")

    if isinstance(obj, pd.DataFrame):
        obj.index = obj.index.droplevel(level=0)

    if isinstance(obj, np.ndarray):
        if obj.ndim != 3 or obj.shape[0] != 1:
            raise ValueError("if obj is np.ndarray, must be of dim 3, with shape[0]=1")
        obj = np.reshape(obj, (obj.shape[1], obj.shape[2]))

    return obj


def convert_Series_to_Hierarchical(obj, store=None):
    """Convert series to a single-series hierarchical object.

    Assumes input is conformant with one of the three Series mtypes.
    This method does not perform full mtype checks, use mtype or check_is_mtype for
    checks.

    Parameters
    ----------
    obj: an object of scitype Series, of mtype pd.DataFrame, pd.Series, or np.ndarray.

    Returns
    -------
    returns a data container of mtype pd_multiindex_hier
    """
    obj_df = convert_to(obj, to_type="pd.DataFrame", as_scitype="Series")
    obj_df = obj_df.copy()
    obj_df["__level1"] = 0
    obj_df["__level2"] = 0
    obj_df = obj_df.set_index(["__level1", "__level2"], append=True)
    obj_df = obj_df.reorder_levels([1, 2, 0])
    return obj_df


def convert_Hierarchical_to_Series(obj, store=None):
    """Convert single-series hierarchical object to a series.

    Assumes input is conformant with Hierarchical mtype.
    This method does not perform full mtype checks, use mtype or check_is_mtype for
    checks.

    Parameters
    ----------
    obj: an object of scitype Hierarchical.

    Returns
    -------
    returns a data container of mtype pd.DataFrame, of scitype Series
    """
    obj_df = convert_to(obj, to_type="pd_multiindex_hier", as_scitype="Hierarchical")
    obj_df = obj_df.copy()
    obj_df.index = obj_df.index.get_level_values(-1)
    return obj_df


def convert_Panel_to_Hierarchical(obj, store=None):
    """Convert panel to a single-panel hierarchical object.

    Assumes input is conformant with one of the Panel mtypes.
    This method does not perform full mtype checks, use mtype or check_is_mtype for
    checks.

    Parameters
    ----------
    obj: an object of scitype Panel.

    Returns
    -------
    returns a data container of mtype pd_multiindex_hier
    """
    obj_df = convert_to(obj, to_type="pd-multiindex", as_scitype="Panel")
    obj_df = obj_df.copy()
    obj_df["__level2"] = 0
    obj_df = obj_df.set_index(["__level2"], append=True)
    obj_df = obj_df.reorder_levels([2, 0, 1])
    return obj_df


def convert_Hierarchical_to_Panel(obj, store=None):
    """Convert single-series hierarchical object to a series.

    Assumes input is conformant with Hierarchical mtype.
    This method does not perform full mtype checks, use mtype or check_is_mtype for
    checks.

    Parameters
    ----------
    obj: an object of scitype Hierarchical.

    Returns
    -------
    returns a data container of mtype pd-multiindex, of scitype Panel
    """
    obj_df = convert_to(obj, to_type="pd_multiindex_hier", as_scitype="Hierarchical")
    obj_df = obj_df.copy()
    obj_df.index = obj_df.index.get_level_values([-2, -1])
    return obj_df


def convert_to_scitype(obj, to_scitype, from_scitype=None, store=None):
    """Convert single-series or single-panel between mtypes.

    Assumes input is conformant with one of the mtypes
        for one of the scitypes Series, Panel, Hierarchical.
    This method does not perform full mtype checks, use mtype or check_is_mtype for
    checks.

    Parameters
    ----------
    obj : an object of scitype Series, Panel, or Hierarchical.
    to_scitype : str, scitype that obj should be converted to
    from_scitype : str, optional. Default = inferred from obj
        scitype that obj is of, and being converted from
        if avoided, function will skip type inference from obj
    store : dict, optional. Converter store for back-conversion.

    Returns
    -------
    obj of scitype to_scitype
        if converted to or from Hierarchical, the mtype will always be one of
            pd.DataFrame (Series), pd-multiindex (Panel), or pd_multiindex_hier
        if converted to or from Panel, mtype will attempt to keep python type
            e.g., np.ndarray (Series) converted to numpy3D (Panel) or back
            if not possible, will be one of the mtypes with pd.DataFrame python type
    """
    if from_scitype is None:
        obj_mtype = mtype(obj, as_scitype=["Series", "Panel", "Hierarchical"])
        from_scitype = mtype_to_scitype(obj_mtype)

    if to_scitype == from_scitype:
        return obj

    func_name = f"convert_{from_scitype}_to_{to_scitype}"
    func = eval(func_name)

    return func(obj, store=store)
