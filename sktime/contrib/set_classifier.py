
from sklearn.ensemble import RandomForestClassifier
from sktime.classification.dictionary_based import (
    MUSE,
    WEASEL,
    BOSSEnsemble,
    ContractableBOSS,
    TemporalDictionaryEnsemble,
)
from sktime.classification.distance_based import (
    ElasticEnsemble,
    KNeighborsTimeSeriesClassifier,
    ProximityForest,
    ProximityStump,
    ProximityTree,
    ShapeDTW,
)
from sktime.classification.feature_based import (
    Catch22Classifier,
    MatrixProfileClassifier,
    SignatureClassifier,
    TSFreshClassifier,
)
from sktime.classification.hybrid import HIVECOTEV1, HIVECOTEV2
from sktime.classification.interval_based import (
    CanonicalIntervalForest,
    DrCIF,
    RandomIntervalSpectralForest,
    SupervisedTimeSeriesForest,
    TimeSeriesForestClassifier,
)
from sktime.classification.kernel_based import Arsenal, ROCKETClassifier
from sktime.classification.shapelet_based import ShapeletTransformClassifier


def set_classifier(cls, resample_id=None, train_file=False):
    """Construct a classifier.

    Basic way of creating the classifier to build using the default settings. This
    set up is to help with batch jobs for multiple problems to facilitate easy
    reproducibility for use with load_and_run_classification_experiment. You can pass a
    classifier object instead to run_classification_experiment.

    Parameters
    ----------
    cls : str
        String indicating which classifier you want.
    resample_id : int or None, default=None
        Classifier random seed.
    train_file : bool, default=False
        Whether a train file is being produced.

    Return
    ------
    classifier : A BaseClassifier.
        The classifier matching the input classifier name.
    """
    name = cls.lower()
    # Dictionary based
    if name == "boss" or name == "bossensemble":
        return BOSSEnsemble(random_state=resample_id)
    elif name == "cboss" or name == "contractableboss":
        return ContractableBOSS(random_state=resample_id)
    elif name == "tde" or name == "temporaldictionaryensemble":
        return TemporalDictionaryEnsemble(
            random_state=resample_id, save_train_predictions=train_file
        )
    elif name == "weasel":
        return WEASEL(random_state=resample_id)
    elif name == "muse":
        return MUSE(random_state=resample_id)
    # Distance based
    elif name == "pf" or name == "proximityforest":
        return ProximityForest(random_state=resample_id)
    elif name == "pt" or name == "proximitytree":
        return ProximityTree(random_state=resample_id)
    elif name == "ps" or name == "proximityStump":
        return ProximityStump(random_state=resample_id)
    elif name == "dtwcv" or name == "kneighborstimeseriesclassifier":
        return KNeighborsTimeSeriesClassifier(distance="dtwcv")
    elif name == "dtw" or name == "1nn-dtw":
        return KNeighborsTimeSeriesClassifier(distance="dtw")
    elif name == "msm" or name == "1nn-msm":
        return KNeighborsTimeSeriesClassifier(distance="msm")
    elif name == "ee" or name == "elasticensemble":
        return ElasticEnsemble(random_state=resample_id)
    elif name == "shapedtw":
        return ShapeDTW()
    # Feature based
    elif name == "catch22":
        return Catch22Classifier(
            random_state=resample_id, estimator=RandomForestClassifier(n_estimators=500)
        )
    elif name == "matrixprofile":
        return MatrixProfileClassifier(random_state=resample_id)
    elif name == "signature":
        return SignatureClassifier(
            random_state=resample_id,
            classifier=RandomForestClassifier(n_estimators=500),
        )
    elif name == "tsfresh":
        return TSFreshClassifier(
            random_state=resample_id, estimator=RandomForestClassifier(n_estimators=500)
        )
    elif name == "tsfresh-r":
        return TSFreshClassifier(
            random_state=resample_id,
            estimator=RandomForestClassifier(n_estimators=500),
            relevant_feature_extractor=True,
        )
    # Hybrid
    elif name == "hc1" or name == "hivecotev1":
        return HIVECOTEV1(random_state=resample_id)
    elif name == "hc2" or name == "hivecotev2":
        return HIVECOTEV2(random_state=resample_id)
    # Interval based
    elif name == "rise" or name == "randomintervalspectralforest":
        return RandomIntervalSpectralForest(random_state=resample_id, n_estimators=500)
    elif name == "tsf" or name == "timeseriesforestclassifier":
        return TimeSeriesForestClassifier(random_state=resample_id, n_estimators=500)
    elif name == "cif" or name == "canonicalintervalforest":
        return CanonicalIntervalForest(random_state=resample_id, n_estimators=500)
    elif name == "stsf" or name == "supervisedtimeseriesforest":
        return SupervisedTimeSeriesForest(random_state=resample_id, n_estimators=500)
    elif name == "drcif":
        return DrCIF(
            random_state=resample_id, n_estimators=500, save_transformed_data=train_file
        )
    # Kernel based
    elif name == "rocket":
        return ROCKETClassifier(random_state=resample_id)
    elif name == "arsenal":
        return Arsenal(random_state=resample_id, save_transformed_data=train_file)
    # Shapelet based
    elif name == "stc" or name == "shapelettransformclassifier":
        return ShapeletTransformClassifier(
            random_state=resample_id, save_transformed_data=train_file
        )
    else:
        raise Exception("UNKNOWN CLASSIFIER")