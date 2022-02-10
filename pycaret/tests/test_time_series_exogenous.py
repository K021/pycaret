"""Module to test time_series forecasting - univariate with exogenous variables
"""
import pytest
import numpy as np  # type: ignore
import pandas as pd  # type: ignore

from pycaret.datasets import get_data
from pycaret.internal.pycaret_experiment import TimeSeriesExperiment


pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


##############################
#### Functions Start Here ####
##############################


############################
#### Functions End Here ####
############################


##########################
#### Tests Start Here ####
##########################


def test_create_tune_predict_finalize_model(load_uni_exo_data_target):
    """test create_model, tune_model, predict_model and finalize_model
    functionality using exogenous variables
    """
    data, target = load_uni_exo_data_target

    fh = 12
    data_for_modeling = data.iloc[:-12]
    future_data = data.iloc[-12:]
    future_exog = future_data.drop(columns=target)

    exp = TimeSeriesExperiment()
    exp.setup(
        data=data_for_modeling, target=target, fh=fh, seasonal_period=4, session_id=42
    )

    #######################
    ## Test Create Model ##
    #######################
    model = exp.create_model("arima")

    #########################
    #### Expected Values ####
    #########################
    expected_period_index = data_for_modeling.iloc[-fh:].index
    final_expected_period_index = future_exog.index

    ########################
    ## Test Predict Model ##
    ########################
    # Default prediction
    y_pred = exp.predict_model(model)
    assert isinstance(y_pred, pd.Series)
    assert np.all(y_pred.index == expected_period_index)

    #####################
    ## Test Tune Model ##
    #####################
    tuned_model = exp.tune_model(model)

    ########################
    ## Test Predict Model ##
    ########################
    # Default prediction
    y_pred = exp.predict_model(tuned_model)
    assert isinstance(y_pred, pd.Series)
    assert np.all(y_pred.index == expected_period_index)

    #########################
    ## Test Finalize Model ##
    #########################

    final_model = exp.finalize_model(tuned_model)
    y_pred = exp.predict_model(final_model, X=future_exog)

    assert np.all(y_pred.index == final_expected_period_index)


def test_blend_models(load_uni_exo_data_target, load_models_uni_mix_exo_noexo):
    """test blending functionality"""
    data, target = load_uni_exo_data_target

    fh = 12
    data_for_modeling = data.iloc[:-12]
    future_data = data.iloc[-12:]
    future_exog = future_data.drop(columns=target)

    #########################
    #### Expected Values ####
    #########################
    expected_period_index = data_for_modeling.iloc[-fh:].index
    final_expected_period_index = future_exog.index

    exp = TimeSeriesExperiment()
    exp.setup(
        data=data_for_modeling, target=target, fh=fh, seasonal_period=4, session_id=42
    )

    models_to_include = load_models_uni_mix_exo_noexo
    best_models = exp.compare_models(include=models_to_include, n_select=3)

    blender = exp.blend_models(best_models)
    y_pred = exp.predict_model(blender)
    assert isinstance(y_pred, pd.Series)
    assert np.all(y_pred.index == expected_period_index)

    #########################
    ## Test Finalize Model ##
    #########################

    final_model = exp.finalize_model(blender)
    y_pred = exp.predict_model(final_model, X=future_exog)

    assert np.all(y_pred.index == final_expected_period_index)


def test_setup():
    """Test the setup with exogenous variables"""
    length = 100
    data = pd.DataFrame(np.random.rand(length, 7))
    data.columns = "A B C D E F G".split()
    data["B"] = pd.date_range("20130101", periods=length)
    target = "A"
    index = "B"  # NOTE: When index is provided we do not need to pass seasonal_period

    exp = TimeSeriesExperiment()

    ######################################
    #### Univariate without exogenous ####
    ######################################
    forecasting_type = "Univariate without Exogenous Variables"

    #### Case 1: pd.Series ----
    exp.setup(data=data[target], seasonal_period=1)
    assert exp.forecasting_type == forecasting_type
    assert exp.target_param == target
    assert exp.exogenous_variables == []

    #### Case 2: pd.DataFrame with 1 column ----
    exp.setup(data=pd.DataFrame(data[target]), seasonal_period=1)
    assert exp.forecasting_type == forecasting_type
    assert exp.target_param == target
    assert exp.exogenous_variables == []

    #### Case 3: # Target specified & correct ----
    exp.setup(data=data[target], target=target, seasonal_period=1)
    assert exp.forecasting_type == forecasting_type
    assert exp.target_param == target
    assert exp.exogenous_variables == []

    ###################################
    #### Univariate with exogenous ####
    ###################################
    forecasting_type = "Univariate with Exogenous Variables"

    #### Case 1: `target` provided, `index` not provided, `ignore_features` not provided ----
    exp.setup(data=data, target=target, seasonal_period=1)
    assert exp.forecasting_type == forecasting_type
    assert exp.target_param == target
    assert exp.exogenous_variables == ["B", "C", "D", "E", "F", "G"]

    #### Case 2: `target` provided, `index` provided, `ignore_features` not provided ----
    exp.setup(data=data, target=target, index=index)
    assert exp.forecasting_type == forecasting_type
    assert exp.target_param == target
    assert exp.exogenous_variables == ["C", "D", "E", "F", "G"]
    # TODO: Add check for index values

    #### Case 3: `target` provided, `index` provided, `ignore_features` provided ----
    exp.setup(data=data, target=target, index=index, ignore_features=["C", "E"])
    assert exp.forecasting_type == forecasting_type
    assert exp.target_param == target
    assert exp.exogenous_variables == ["D", "F", "G"]
    # TODO: Add check for index values

    #### Case 4: `target` provided, `index` not provided, `ignore_features` provided ----
    exp.setup(data=data, target=target, ignore_features=["C", "E"], seasonal_period=1)
    assert exp.forecasting_type == forecasting_type
    assert exp.target_param == target
    assert exp.exogenous_variables == ["B", "D", "F", "G"]


def test_setup_raises():
    """Test the setup with exogenous variables when it raises errors"""
    length = 100
    data = pd.DataFrame(np.random.rand(length, 7))
    data.columns = "A B C D E F G".split()

    exp = TimeSeriesExperiment()

    ##############################
    #### Target Not Specified ####
    ##############################
    with pytest.raises(ValueError) as errmsg:
        exp.setup(data=data, seasonal_period=1)

    exceptionmsg = errmsg.value.args[0]

    assert (
        exceptionmsg
        == f"Data has {len(data.columns)} columns, but the target has not been specified."
    )

    ################################
    #### Wrong Target Specified ####
    ################################

    target = "WRONG"

    #### Case 1: Without exogenous ----
    column = "A"
    with pytest.raises(ValueError) as errmsg:
        exp.setup(data=data[column], target=target, seasonal_period=1)

    exceptionmsg = errmsg.value.args[0]

    assert (
        exceptionmsg == f"Target = '{target}', but data only has '{column}'. "
        "If you are passing a series (or a dataframe with 1 column) "
        "to setup, you can leave `target=None`"
    )

    #### Case 2: With exogenous ----
    with pytest.raises(ValueError) as errmsg:
        exp.setup(data=data, target=target, seasonal_period=1)

    exceptionmsg = errmsg.value.args[0]
    assert exceptionmsg == f"Target Column '{target}' is not present in the data."
