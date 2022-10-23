from numpy.testing import assert_allclose
import numpy as np
from pycalphad import Workspace, variables as v
from pycalphad.property_framework import as_property, ComputableProperty, T0, IsolatedPhase, DormantPhase
from pycalphad.property_framework.units import Q_
from pycalphad.tests.fixtures import load_database, select_database
import pytest

@pytest.mark.solver
@select_database("alzn_mey.tdb")
def test_workspace_creation(load_database):
    dbf = load_database()
    wks = Workspace(dbf=dbf, comps=['AL', 'ZN', 'VA'], phases=['FCC_A1', 'HCP_A3', 'LIQUID'],
                    conditions={v.N: 1, v.P: 1e5, v.T: (300, 1000, 10), v.X('ZN'): 0.3})
    wks2 = Workspace(dbf, ['AL', 'ZN', 'VA'], ['FCC_A1', 'HCP_A3', 'LIQUID'],
                     {v.N: 1, v.P: 1e5, v.T: (300, 1000, 10), v.X('ZN'): 0.3})
    assert_allclose(wks.eq.GM, wks2.eq.GM)

@select_database("alzn_mey.tdb")
def test_workspace_conditions_change_clear_result(load_database):
    dbf = load_database()
    wks = Workspace(dbf, ['AL', 'ZN', 'VA'], ['FCC_A1', 'HCP_A3', 'LIQUID'],
                    {v.N: 1, v.P: 1e5, v.T: (300, 1000, 100), v.X('ZN'): 0.3})
    assert wks._eq is None
    # Attribute access will trigger calculation
    assert wks.eq is not None
    assert wks._eq is wks.eq
    assert len(wks.eq.coords['T']) == 7
    # Conditions change should clear previous result
    wks.conditions[v.T] = 600
    # Check private member so that calculation is not triggered again
    assert wks._eq is None
    # New calculation result will have different shape
    assert len(wks.eq.coords['T']) == 1

@select_database("alzn_mey.tdb")
def test_meta_property_creation(load_database):
    dbf = load_database()
    wks = Workspace(dbf=dbf, comps=['AL', 'ZN', 'VA'], phases=['FCC_A1', 'HCP_A3', 'LIQUID'],
                    conditions={v.N: 1, v.P: 1e5, v.T: (300, 1000, 10), v.X('ZN'): 0.3})
    my_tzero = T0('FCC_A1', 'HCP_A3', wks=wks)
    assert isinstance(my_tzero, ComputableProperty)

@select_database("alzn_mey.tdb")
def test_tzero_property(load_database):
    dbf = load_database()
    wks = Workspace(dbf=dbf, comps=['AL', 'ZN', 'VA'], phases=['FCC_A1', 'HCP_A3', 'LIQUID'],
                    conditions={v.N: 1, v.P: 1e5, v.T: 600, v.X('ZN'): (0.01,1-0.01,0.01)})
    my_tzero = T0('FCC_A1', 'HCP_A3', wks=wks)
    assert isinstance(my_tzero, ComputableProperty)
    assert my_tzero.property_to_optimize == v.T
    t0_values, = wks.get(my_tzero)
    assert_allclose(np.nanmax(t0_values.magnitude), 2952.90443)
    wks.conditions[v.X('ZN')] = 0.3
    my_tzero.property_to_optimize = v.X('ZN')
    my_tzero.minimum_value = 0.0
    my_tzero.maximum_value = 1.0
    t0_composition, = wks.get(my_tzero)
    assert_allclose(t0_composition[0].magnitude, Q_(0.86119, 'fraction').magnitude, atol=my_tzero.residual_tol)

@select_database("alzn_mey.tdb")
def test_dot_derivative_binary_temperature(load_database):
    dbf = load_database()
    wks = Workspace(dbf=dbf, comps=['AL', 'ZN', 'VA'], phases=['FCC_A1', 'HCP_A3', 'LIQUID'],
                    conditions={v.N: 1, v.P: 1e5, v.T: 300, v.X('ZN'): 0.3})
    x, y_dot = wks.get('T', 'MU(AL).T')
    # Checked by finite difference
    assert_allclose(y_dot.magnitude, -28.775364)

@select_database("alzn_mey.tdb")
def test_dot_derivative_binary_composition(load_database):
    dbf = load_database()
    wks = Workspace(dbf=dbf, comps=['AL', 'ZN', 'VA'], phases=['FCC_A1', 'HCP_A3', 'LIQUID'],
                    conditions={v.N: 1, v.P: 1e5, v.T: 600, v.X('ZN'): 0.1})
    x, y_dot = wks.get('X(ZN)', 'MU(AL).X(ZN)')
    # Checked by finite difference
    assert_allclose(y_dot.magnitude, -2806.93592)
