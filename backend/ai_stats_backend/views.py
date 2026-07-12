import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import DBSCAN, KMeans
from sklearn.linear_model import LinearRegression, LogisticRegression, Lasso, Ridge
from sklearn.metrics import (accuracy_score, f1_score, mean_squared_error, precision_score,
                             recall_score, r2_score)
from sklearn.model_selection import train_test_split
from django.conf import settings
from mongoengine.connection import get_db
from pymongo.errors import PyMongoError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health_check(request):
    try:
        db = get_db(alias=settings.MONGODB_ALIAS)
        db.command("ping")
    except PyMongoError as exc:
        return Response(
            {
                "status": "error",
                "mongodb": {
                    "connected": False,
                    "database": settings.MONGODB_NAME,
                    "error": str(exc),
                },
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return Response(
        {
            "status": "ok",
            "mongodb": {
                "connected": True,
                "database": db.name,
            },
        }
    )


def _load_uploaded_dataset(uploaded_file):
    uploaded_file.seek(0)
    raw_bytes = uploaded_file.read()
    file_buffer = io.BytesIO(raw_bytes)
    extension = Path(uploaded_file.name).suffix.lower()

    if extension in {".csv", ".txt"}:
        return pd.read_csv(file_buffer, engine="python")
    if extension == ".tsv":
        return pd.read_csv(file_buffer, sep="\t", engine="python")
    if extension in {".xls", ".xlsx"}:
        return pd.read_excel(file_buffer)
    if extension == ".json":
        return pd.read_json(file_buffer)
    if extension == ".parquet":
        return pd.read_parquet(file_buffer)
    if extension in {".html", ".htm"}:
        tables = pd.read_html(file_buffer)
        if not tables:
            raise ValueError("No HTML table found in the uploaded file.")
        return tables[0]
    if extension == ".xml":
        return pd.read_xml(file_buffer)
    if extension == ".feather":
        return pd.read_feather(file_buffer)
    if extension == ".sas7bdat":
        return pd.read_sas(file_buffer)
    if extension == ".dta":
        return pd.read_stata(file_buffer)
    if extension == ".sav":
        return pd.read_spss(file_buffer)

    # Fallback: try common text-based formats first, then Excel.
    file_buffer.seek(0)
    try:
        return pd.read_csv(file_buffer, engine="python")
    except Exception:
        file_buffer.seek(0)
        try:
            return pd.read_excel(file_buffer)
        except Exception as exc:
            raise ValueError(
                "Unsupported dataset file format or malformed file."
            ) from exc


@api_view(["POST"])
def upload_dataset(request):
    uploaded_file = request.FILES.get("dataset")
    if uploaded_file is None:
        return Response(
            {"status": "error", "message": "No dataset file uploaded."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        dataframe = _load_uploaded_dataset(uploaded_file)
    except Exception as exc:
        return Response(
            {
                "status": "error",
                "message": str(exc),
                "filename": uploaded_file.name,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = {
        "status": "success",
        "filename": uploaded_file.name,
        "rows": int(len(dataframe)),
        "columns": int(len(dataframe.columns)),
        "column_names": list(map(str, dataframe.columns)),
        "missing_values": dataframe.isnull().sum().to_dict(),
        "summary_statistics": dataframe.describe(include="all").to_dict(),
    }

    return Response(result, status=status.HTTP_200_OK)


def _load_json_dataset(data):
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, dict) and 'rows' in data and 'columns' in data:
        return pd.DataFrame(data['rows'], columns=data['columns'])
    if isinstance(data, dict):
        return pd.DataFrame(data)
    if isinstance(data, list):
        return pd.DataFrame(data)
    raise ValueError('Invalid JSON dataset format.')


def _coerce_numeric_columns(dataframe):
    df = dataframe.copy()
    numeric_columns = []
    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            numeric_columns.append(column)
            continue
        converted = pd.to_numeric(df[column], errors='coerce')
        if converted.notna().any():
            df[column] = converted
            numeric_columns.append(column)
    return df, numeric_columns


def _data_quality_summary(df):
    missing = df.isnull().sum().sum()
    duplicates = df.duplicated().sum()
    total = df.shape[0] * df.shape[1]
    completeness = 100 - round(missing / total * 100, 1) if total else 0
    return missing, duplicates, completeness


def _outlier_summary(series):
    values = pd.to_numeric(series.dropna(), errors='coerce')
    values = values[~values.isna()]
    if values.size < 4:
        return 0
    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1
    return int(((values < (q1 - 1.5 * iqr)) | (values > (q3 + 1.5 * iqr))).sum())


def _prepare_dataframe(request):
    if request.FILES.get('dataset') is not None:
        dataframe = _load_uploaded_dataset(request.FILES['dataset'])
    elif request.data.get('data') is not None:
        dataframe = _load_json_dataset(request.data.get('data'))
    else:
        raise ValueError('No dataset provided for analysis.')

    dataframe = dataframe.dropna(axis=1, how='all')
    dataframe = dataframe.dropna(axis=0, how='all')
    return dataframe


def _summary_statistics(df, columns):
    rows = []
    for column in columns[:6]:
        series = pd.to_numeric(df[column], errors='coerce')
        rows.append({
            'title': column,
            'body': (
                f'Count {int(series.count())}, mean {round(series.mean(), 2)}, median {round(series.median(), 2)}, '
                f'mode {series.mode().iloc[0] if not series.mode().empty else "N/A"}, min {round(series.min(), 2)}, '
                f'max {round(series.max(), 2)}, range {round(series.max() - series.min(), 2)}, '
                f'variance {round(series.var(ddof=0), 2)}, std dev {round(series.std(ddof=0), 2)}, '
                f'skewness {round(series.skew(), 2)}, kurtosis {round(series.kurtosis(), 2)}'
            ),
            'meta': 'Descriptive statistics'
        })
    return rows


def _inferential_statistics(df, target, confidence):
    if target not in df.columns:
        raise ValueError('Target column not found for inferential statistics.')
    series = pd.to_numeric(df[target], errors='coerce').dropna()
    if len(series) < 2:
        raise ValueError('Not enough numeric data for inferential statistics.')
    mean_value = series.mean()
    sem = series.std(ddof=1) / (len(series) ** 0.5)
    t_value = stats.t.ppf(1 - (1 - confidence) / 2, df=len(series) - 1)
    lower = mean_value - t_value * sem
    upper = mean_value + t_value * sem
    return [
        {'title': 'Confidence Interval', 'body': f'{round(lower, 4)} to {round(upper, 4)}', 'meta': f'{int(confidence * 100)}% confidence'},
        {'title': 'Margin of Error', 'body': round(t_value * sem, 4), 'meta': 'Sampling uncertainty'},
        {'title': 'Sample mean', 'body': round(mean_value, 4), 'meta': 'Estimated population mean'},
        {'title': 'Standard error', 'body': round(sem, 4), 'meta': 'Precision of the mean'}
    ]


def _correlation_analysis(df, numeric_columns, target):
    target = target if target in df.columns else (numeric_columns[0] if numeric_columns else None)
    if not target or target not in df.columns:
        return [{'title': 'Correlation analysis', 'body': 'No valid target column available.', 'meta': ''}]
    rows = []
    for column in [c for c in numeric_columns if c != target][:6]:
        x = pd.to_numeric(df[column], errors='coerce')
        y = pd.to_numeric(df[target], errors='coerce')
        pair = df[[column, target]].dropna()
        if pair.shape[0] < 2:
            continue
        pearson_r = pair[column].corr(pair[target])
        spearman_r = pair[column].corr(pair[target], method='spearman')
        rows.append({
            'title': f'{column} vs {target}',
            'body': f'Pearson {round(pearson_r, 4)}, Spearman {round(spearman_r, 4)}',
            'meta': 'Correlation analysis'
        })
    if not rows:
        rows.append({'title': 'Correlation analysis', 'body': 'No numeric pairs available for correlation.', 'meta': ''})
    return rows


def _regression_analysis(df, numeric_columns, target):
    if target not in df.columns or target not in numeric_columns:
        return [{'title': 'Regression analysis', 'body': 'Target must be numeric for regression.', 'meta': ''}]
    features = [c for c in numeric_columns if c != target]
    if not features:
        return [{'title': 'Regression analysis', 'body': 'At least one numeric feature is required.', 'meta': ''}]
    data = df[features + [target]].dropna()
    if data.shape[0] < 2:
        return [{'title': 'Regression analysis', 'body': 'Not enough rows to fit a regression model.', 'meta': ''}]
    X = data[features].to_numpy()
    y = data[target].to_numpy()
    model = LinearRegression().fit(X, y)
    predictions = model.predict(X)
    return [
        {'title': 'Regression model', 'body': 'Linear regression trained with ' + str(len(features)) + ' features.', 'meta': ''},
        {'title': 'Coefficients', 'body': ', '.join([f'{feat}:{round(coef,4)}' for feat, coef in zip(features, model.coef_)]), 'meta': ''},
        {'title': 'Intercept', 'body': round(model.intercept_, 4), 'meta': ''},
        {'title': 'R-squared', 'body': round(model.score(X, y), 4), 'meta': ''},
        {'title': 'RMSE', 'body': round(mean_squared_error(y, predictions, squared=False), 4), 'meta': ''}
    ]


def _hypothesis_analysis(df, numeric_columns, target):
    results = []
    if target in numeric_columns:
        series = pd.to_numeric(df[target], errors='coerce').dropna()
        if len(series) >= 2:
            t_stat, p_value = stats.ttest_1samp(series, 0)
            results.append({'title': 'One-sample t-test', 'body': f't={round(t_stat,4)}, p={round(p_value,4)}', 'meta': 'Null mean = 0'})
    if len(numeric_columns) >= 2:
        x = pd.to_numeric(df[numeric_columns[0]], errors='coerce')
        y = pd.to_numeric(df[numeric_columns[1]], errors='coerce')
        paired = df[[numeric_columns[0], numeric_columns[1]]].dropna()
        if paired.shape[0] >= 2:
            t_stat, p_value = stats.ttest_rel(paired[numeric_columns[0]], paired[numeric_columns[1]])
            results.append({'title': 'Paired t-test', 'body': f't={round(t_stat,4)}, p={round(p_value,4)}', 'meta': 'Related samples'})
    if not results:
        results.append({'title': 'Hypothesis tests', 'body': 'Not enough data for hypothesis testing.', 'meta': ''})
    return results


def _time_series_analysis(df, numeric_columns, target):
    if target not in df.columns or target not in numeric_columns:
        return [{'title': 'Time series analysis', 'body': 'Target must be numeric for time series analysis.', 'meta': ''}]
    data = pd.to_numeric(df[target], errors='coerce').dropna()
    if data.size < 3:
        return [{'title': 'Time series analysis', 'body': 'Not enough values for time series.', 'meta': ''}]
    moving_avg = data.rolling(window=min(3, len(data))).mean().iloc[-1]
    trend = pd.Series(range(len(data))).corr(data)
    forecast = data.iloc[-1]
    return [
        {'title': 'Trend analysis', 'body': f'Linear trend score {round(trend,4)}', 'meta': ''},
        {'title': 'Moving average', 'body': round(float(moving_avg), 4), 'meta': '3-point moving average'},
        {'title': 'Forecast', 'body': round(float(forecast), 4), 'meta': 'Naive next-step forecast'},
        {'title': 'ARIMA support', 'body': 'ARIMA modeling can be added using statsmodels.', 'meta': ''}
    ]


def _distribution_analysis(df, numeric_columns, target):
    if target not in df.columns or target not in numeric_columns:
        return [{'title': 'Distribution analysis', 'body': 'Target must be numeric for distribution analysis.', 'meta': ''}]
    series = pd.to_numeric(df[target], errors='coerce').dropna()
    if series.size < 3:
        return [{'title': 'Distribution analysis', 'body': 'Not enough numeric values for distribution analysis.', 'meta': ''}]
    normal_p = stats.normaltest(series).pvalue if len(series) >= 8 else None
    return [
        {'title': 'Normal distribution', 'body': f'Mean {round(series.mean(),4)}, std {round(series.std(ddof=0),4)}', 'meta': ''},
        {'title': 'Skewness', 'body': round(series.skew(),4), 'meta': ''},
        {'title': 'Kurtosis', 'body': round(series.kurtosis(),4), 'meta': ''},
        {'title': 'Normality test', 'body': f'p-value {round(normal_p,4)}' if normal_p is not None else 'Sample too small for normality test', 'meta': ''}
    ]


def _data_quality_analysis(df):
    missing, duplicates, completeness = _data_quality_summary(df)
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    total_outliers = sum(_outlier_summary(df[column]) for column in numeric_columns)
    return [
        {'title': 'Missing values', 'body': f'{missing} missing cells', 'meta': ''},
        {'title': 'Duplicate records', 'body': f'{duplicates} duplicates', 'meta': ''},
        {'title': 'Completeness', 'body': f'{completeness}%', 'meta': ''},
        {'title': 'Outliers', 'body': f'{total_outliers} outlying cells', 'meta': ''}
    ]


def _ai_recommendation_analysis(df, numeric_columns, categorical_columns):
    if len(numeric_columns) == 1 and len(categorical_columns) == 1:
        return [{'title': 'Recommended test', 'body': 'Independent T-Test', 'meta': 'One numeric and one categorical variable detected.'}]
    if len(numeric_columns) >= 2:
        return [{'title': 'Recommended test', 'body': 'Multiple Linear Regression', 'meta': 'Multiple numeric predictors available.'}]
    if len(categorical_columns) >= 1:
        return [{'title': 'Recommended test', 'body': 'Chi-Square Test', 'meta': 'Categorical frequencies are available.'}]
    return [{'title': 'Recommended test', 'body': 'Descriptive Statistics', 'meta': 'Use descriptive statistics first.'}]


def _classification_analysis(df, numeric_columns, categorical_columns, target):
    if target not in df.columns or target not in categorical_columns:
        return [{'title': 'Classification', 'body': 'Select a categorical target for classification.', 'meta': ''}]
    if not numeric_columns:
        return [{'title': 'Classification', 'body': 'No numeric predictors available.', 'meta': ''}]
    data = df[numeric_columns + [target]].dropna()
    if data.shape[0] < 5 or data[target].nunique() < 2:
        return [{'title': 'Classification', 'body': 'Not enough data for classification.', 'meta': ''}]
    X = data[numeric_columns].to_numpy()
    y = data[target].astype('category').cat.codes.to_numpy()
    try:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        model = LogisticRegression(max_iter=500).fit(X_train, y_train)
        preds = model.predict(X_test)
        return [
            {'title': 'Classification model', 'body': 'Logistic Regression trained on numeric predictors.', 'meta': ''},
            {'title': 'Accuracy', 'body': round(accuracy_score(y_test, preds), 4), 'meta': ''},
            {'title': 'Precision', 'body': round(precision_score(y_test, preds, average='weighted', zero_division=0), 4), 'meta': ''},
            {'title': 'Recall', 'body': round(recall_score(y_test, preds, average='weighted', zero_division=0), 4), 'meta': ''},
            {'title': 'F1 score', 'body': round(f1_score(y_test, preds, average='weighted', zero_division=0), 4), 'meta': ''}
        ]
    except Exception as exc:
        return [{'title': 'Classification', 'body': f'Classification error: {str(exc)}', 'meta': ''}]


def _ml_regression_analysis(df, numeric_columns, target):
    if target not in df.columns or target not in numeric_columns:
        return [{'title': 'Regression ML', 'body': 'Select a numeric target for regression.', 'meta': ''}]
    features = [c for c in numeric_columns if c != target]
    if not features:
        return [{'title': 'Regression ML', 'body': 'At least one numeric predictor required.', 'meta': ''}]
    data = df[features + [target]].dropna()
    if data.shape[0] < 5:
        return [{'title': 'Regression ML', 'body': 'Not enough data for regression modeling.', 'meta': ''}]
    X = data[features].to_numpy()
    y = data[target].to_numpy()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    models = {
        'Linear Regression': LinearRegression(),
        'Ridge Regression': Ridge(alpha=1.0),
        'Lasso Regression': Lasso(alpha=0.1)
    }
    results = []
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        results.append({
            'title': name,
            'body': f'RMSE {round(mean_squared_error(y_test, preds, squared=False), 4)}, R2 {round(r2_score(y_test, preds), 4)}',
            'meta': ''
        })
    return results


def _clustering_analysis(df, numeric_columns):
    if len(numeric_columns) < 2:
        return [{'title': 'Clustering', 'body': 'At least two numeric features required for clustering.', 'meta': ''}]
    data = df[numeric_columns].dropna()
    X = data.to_numpy()
    results = []
    try:
        kmeans = KMeans(n_clusters=min(3, X.shape[0]), random_state=42).fit(X)
        counts = np.bincount(kmeans.labels_)
        results.append({'title': 'K-Means', 'body': 'Cluster sizes: ' + ', '.join(map(str, counts)), 'meta': ''})
    except Exception as exc:
        results.append({'title': 'K-Means', 'body': f'Error: {str(exc)}', 'meta': ''})
    try:
        dbscan = DBSCAN().fit(X)
        labels = dbscan.labels_
        noise = int((labels == -1).sum())
        results.append({'title': 'DBSCAN', 'body': f'Found {len(set(labels)) - (1 if -1 in labels else 0)} clusters, noise points {noise}', 'meta': ''})
    except Exception as exc:
        results.append({'title': 'DBSCAN', 'body': f'Error: {str(exc)}', 'meta': ''})
    return results


def _model_evaluation_analysis(df, numeric_columns, categorical_columns, target):
    if target in categorical_columns and numeric_columns:
        return _classification_analysis(df, numeric_columns, categorical_columns, target)
    if target in numeric_columns and len(numeric_columns) > 1:
        return _ml_regression_analysis(df, numeric_columns, target)
    return [{'title': 'Model evaluation', 'body': 'Not enough typed columns for evaluation.', 'meta': ''}]


def _feature_importance_analysis(df, numeric_columns, target):
    if target not in df.columns or target not in numeric_columns:
        return [{'title': 'Feature importance', 'body': 'Select a numeric target for importance analysis.', 'meta': ''}]
    if len(numeric_columns) < 2:
        return [{'title': 'Feature importance', 'body': 'At least one additional numeric predictor required.', 'meta': ''}]
    data = df[numeric_columns].dropna()
    correlations = []
    for column in [c for c in numeric_columns if c != target]:
        corr = data[column].corr(data[target])
        correlations.append((column, abs(corr if corr == corr else 0)))
    correlations.sort(key=lambda x: x[1], reverse=True)
    return [{'title': 'Feature importance', 'body': ', '.join([f'{col}:{round(score,4)}' for col, score in correlations[:5]]), 'meta': ''}] 


def _analysis_results(df, analysis_type, target, confidence):
    df, numeric_columns = _coerce_numeric_columns(df)
    categorical_columns = [col for col in df.columns if col not in numeric_columns]
    if target is None:
        target = numeric_columns[0] if numeric_columns else (df.columns[0] if df.columns.size else None)
    if target is None:
        return [{'title': 'Analysis', 'body': 'Dataset contains no columns.', 'meta': ''}]

    analysis_type = analysis_type.lower()
    if analysis_type == 'descriptive':
        return _summary_statistics(df, numeric_columns)
    if analysis_type == 'inferential':
        return _inferential_statistics(df, target, confidence)
    if analysis_type == 'correlation':
        return _correlation_analysis(df, numeric_columns, target)
    if analysis_type == 'regression':
        return _regression_analysis(df, numeric_columns, target)
    if analysis_type == 'hypothesis':
        return _hypothesis_analysis(df, numeric_columns, target)
    if analysis_type == 'time_series':
        return _time_series_analysis(df, numeric_columns, target)
    if analysis_type == 'distribution':
        return _distribution_analysis(df, numeric_columns, target)
    if analysis_type == 'data_quality':
        return _data_quality_analysis(df)
    if analysis_type == 'ai_recommendation':
        return _ai_recommendation_analysis(df, numeric_columns, categorical_columns)
    if analysis_type == 'classification':
        return _classification_analysis(df, numeric_columns, categorical_columns, target)
    if analysis_type == 'ml_regression':
        return _ml_regression_analysis(df, numeric_columns, target)
    if analysis_type == 'clustering':
        return _clustering_analysis(df, numeric_columns)
    if analysis_type == 'model_evaluation':
        return _model_evaluation_analysis(df, numeric_columns, categorical_columns, target)
    if analysis_type == 'feature_importance':
        return _feature_importance_analysis(df, numeric_columns, target)
    return [{'title': 'Analysis', 'body': f'Unsupported analysis type {analysis_type}.', 'meta': ''}]


def _build_analysis_response(df, analysis_type, target, confidence):
    return {
        'status': 'success',
        'analysis_type': analysis_type,
        'target': target,
        'confidence': confidence,
        'results': _analysis_results(df, analysis_type, target, confidence)
    }


@api_view(['POST'])
def analyze_dataset(request):
    try:
        dataframe = _prepare_dataframe(request)
    except Exception as exc:
        return Response({'status': 'error', 'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    analysis_type = request.data.get('analysis_type', 'descriptive')
    target = request.data.get('target')
    confidence = float(request.data.get('confidence', 0.95))

    try:
        response = _build_analysis_response(dataframe, analysis_type, target, confidence)
    except Exception as exc:
        return Response({'status': 'error', 'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(response, status=status.HTTP_200_OK)
