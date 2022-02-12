# -*- coding: utf-8 -*-
"""Testing utility for easy generation of conditional fixtures in pytest_generate_tests.

Exports create_conditional_fixtures_and_names utility
"""

__author__ = ["fkiraly"]

__all__ = ["create_conditional_fixtures_and_names"]

from copy import deepcopy
from itertools import starmap, tee
from typing import Callable, Dict, List

import numpy as np


class FixtureGenerationError(Exception):
    """Raised when a fixture fails to generate."""

    def __init__(self, fixture_name=""):
        self.fixture_name = fixture_name
        fixture_name = fixture_name + " "
        super().__init__(f"fixture {fixture_name}failed to generate")


def create_conditional_fixtures_and_names(
    test_name: str,
    fixture_vars: List[str],
    generator_dict: Dict[str, Callable],
    fixture_sequence: List[str] = None,
):
    """Create conditional fixtures for pytest_generate_tests.

    Creates arguments for pytest.fixture.parameterize,
        using conditional fixture generation functions in generator_dict.

    Example: we want to loop over two fixture variables, "number" and "multiples"
        "number" are integers from 1 to 10,
        "multiples" are multiples of "number" up to "number"-squared
        we then write a generator_dict with two entries
        generator_dict["number"] is a function (test_name, **kwargs) -> list
            that returns [1, 2, ..., 10]
        generator_dict["multiples"] is a function (test_name, number, **kwargs) -> list
            that returns [number, 2* number, ..., number*number]

    This function automatically creates the inputs for pytest.mark.parameterize
        fixture_param_str = "number,multiples"
        fixture_prod = [(1, 1), (2, 2), (2, 4), (3, 3), (3, 6), ...]
        fixture_names = ["1-1", "2-2", "2-4", "3-3", "3-6", ...]

    Parameters
    ----------
    test_name : str, name of the test, from pytest_generate_tests
    fixture_vars : list of str
        fixture variable names used in parameterization of tests
    generator_dict : dict of generator functions
        keys are possible str in fixture_vars, expected signature is
            (test_name: str, **kwargs) -> fixtures: Listof[object], or
                (returning only fixtures)
            (test_name: str, **kwargs) -> fixtures, fixture_names: Listof[object]
                (returning fixture names as well as fixtures)
        generator_dict[my_variable] can take arguments with names
            in fixture_sequence to the left of my_variable
            it should return a list of fixtures for my_variable
            under the assumption that arguments have given values
    fixture_sequence : list of str, optional, default = None
        used in prioritizing conditional generators, sequentially (see above)

    Returns
    -------
    fixture_param_str : str, string to use in pytest.fixture.parameterize
        this is strings in "fixture_vars" concatenated, separated by ","
    fixture_prod : list of tuples, fixtures to use in pytest.fixture.parameterize
        fixture tuples, generated according to the following conditional rule:
            let fixture_vars = [fixture_var1, fixture_var2, ..., fixture_varN]
            all fixtures are obtained as following:
                for i in 1 to N
                    pick fixture[i] any element of generator_dict[fixture_vari](
                        test_name,
                        fixture_var1 = fixture[1], ...,
                        fixture_var(i-1) = fixture[i-1],
                    )
            return (fixture[1], fixture[2], ..., fixture[N])
    fixture_names : list of str, fixture ids to use in pytest.fixture.parameterize
        fixture names, generated according to the following conditional rule:
            let fixture_vars = [fixture_var1, fixture_var2, ..., fixture_varN]
            all fixtures names are obtained as following:
                for i in 1 to N
                    pick fixture_str_pt[i] any element of generator_dict[fixture_vari](
                        test_name,
                        fixture_var1 = fixture[1], ...,
                        fixture_var(i-1) = fixture[i-1],
                    ), second return is exists; otherwise str(first return)
            return "fixture_str_pt[1]-fixture_str_pt[2]-...-fixture_str_pt[N]"
        fixture names correspond to fixtures with the same indices at picks (from lists)
    """
    fixture_vars = _check_list_of_str(fixture_vars, name="fixture_vars")
    fixture_vars = [var for var in fixture_vars if var in generator_dict.keys()]

    # order fixture_vars according to fixture_sequence if provided
    if fixture_sequence is not None:
        fixture_sequence = _check_list_of_str(fixture_sequence, name="fixture_sequence")
        ordered_fixture_vars = []
        for fixture_var_name in fixture_sequence:
            if fixture_var_name in fixture_vars:
                ordered_fixture_vars += [fixture_var_name]
        fixture_vars = ordered_fixture_vars

    def get_fixtures(fixture_var, **kwargs):
        """Call fixture generator from generator_dict, return fixture list.

        Light wrapper around calls to generator_dict[key] functions that generate
            conditional fixtures. get_fixtures adds default string names to the return
            if generator_dict[key] does not return them.

        Parameters
        ----------
        fixture_var : str, name of fixture variable
        kwargs : key-value pairs, keys = names of previous fixture variables
        test_name : str, from local scope
            name of test for which fixtures are generated

        Returns
        -------
        fixture_prod : list of objects or one-element list with FixtureGenerationError
            fixtures for fixture_var for test_name, conditional on fixtures in kwargs
            if call to generator_dict[fixture_var] fails, returns list with error
        fixture_names : list of string, same length as fixture_prod
            i-th element is a string name for i-th element of fixture_prod
            if 2nd arg is returned by generator_dict, then 1:1 copy of that argument
            if no 2nd arg is returned by generator_dict, then str(fixture_prod[i])
            if fixture_prod is list with error, then string is Error:fixture_var
        """
        try:
            res = generator_dict[fixture_var](test_name, **kwargs)
            if isinstance(res, tuple) and len(res) == 2:
                fixture_prod = res[0]
                fixture_names = res[1]
            elif isinstance(res, list):
                fixture_prod = res
                fixture_names = [str(x) for x in res]
            else:
                fixture_prod = starmap(lambda x, y: x, res)
                fixture_names = starmap(lambda x, y: y, res)
        except Exception:
            error = FixtureGenerationError(fixture_name=fixture_var)
            fixture_prod = [error]
            fixture_names = [f"Error:{fixture_var}"]

        return fixture_prod, fixture_names

    def one_fixture_prod(
        fixture_prod,
        old_fixture_vars,
        fixture_var: List[str],
    ):

        for fixture, fixture_name in fixture_prod:
            if len(old_fixture_vars) == 0:
                kwargs = dict()
            else:
                kwargs = dict(zip(old_fixture_vars, fixture))

            new_fixtures, new_fixture_names = get_fixtures(fixture_var, **kwargs)
            for new_fixture, new_fixture_name in zip(new_fixtures, new_fixture_names):
                prod_fixture = deepcopy(fixture) + (deepcopy(new_fixture),)
                prod_name = fixture_name + [new_fixture_name]
                yield prod_fixture, prod_name

    fixture_prods_and_names = [((), [])]

    # we loop over fixture_vars, incrementally going through conditionals
    for i, fixture_var in enumerate(fixture_vars):
        old_fixture_vars = fixture_vars[0:i]
        fixture_prods_and_names = one_fixture_prod(
            fixture_prods_and_names, old_fixture_vars, fixture_var
        )

    def make_fixture_prod(fixture_prod, fixture_name):
        # we need to remove the tuple bracket from singleton
        #   in pytest convention, only multiple variables (2 or more) are tuples
        return _remove_single(fixture_prod)

    def make_fixture_name(fixture_prod, fixture_name):
        name = [x for x in fixture_name if x != ""]
        return "-".join(name)

    fixture_prods_and_names1, fixture_prods_and_names2 = tee(fixture_prods_and_names)

    # apply selection and final modifications to fixture tuples and names
    fixture_prod = starmap(make_fixture_prod, fixture_prods_and_names1)
    fixture_names = starmap(make_fixture_name, fixture_prods_and_names2)

    # in pytest convention, variable strings are separated by comma
    fixture_param_str = ",".join(fixture_vars)

    return fixture_param_str, fixture_prod, fixture_names


def _check_list_of_str(obj, name="obj"):
    """Check whether obj is a list of str.

    Parameters
    ----------
    obj : any object, check whether is list of str
    name : str, default="obj", name of obj to display in error message

    Returns
    -------
    obj, unaltered

    Raises
    ------
    TypeError if obj is not list of str
    """
    if not isinstance(obj, list) or not np.all(isinstance(x, str) for x in obj):
        raise TypeError(f"{name} must be a list of str")
    return obj


def _remove_single(x):
    """Remove tuple wrapping from singleton.

    Parameters
    ----------
    x : tuple

    Returns
    -------
    x[0] if x is a singleton, otherwise x
    """
    if len(x) == 1:
        return x[0]
    else:
        return x
