import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  Database,
  History,
  LoaderCircle,
  Play,
  RefreshCw,
  Sparkles,
  Target,
} from 'lucide-react'

import api from '../../api/api'
import AppShell from '../../components/AppShell'


const TASKS = {
  regression: {
    label: 'Regression',
    algorithms: [
      {
        value: 'linear_regression',
        label: 'Linear Regression',
      },
      {
        value: 'random_forest_regression',
        label: 'Random Forest Regression',
      },
    ],
  },

  classification: {
    label: 'Classification',
    algorithms: [
      {
        value: 'logistic_regression',
        label: 'Logistic Regression',
      },
      {
        value: 'random_forest_classification',
        label: 'Random Forest Classification',
      },
    ],
  },

  clustering: {
    label: 'Clustering',
    algorithms: [
      {
        value: 'kmeans',
        label: 'K-Means Clustering',
      },
    ],
  },
}


export default function MLPage() {
  const [datasets, setDatasets] =
    useState([])

  const [models, setModels] =
    useState([])

  const [selectedDatasetId, setSelectedDatasetId] =
    useState('')

  const [task, setTask] =
    useState('regression')

  const [algorithm, setAlgorithm] =
    useState('linear_regression')

  const [features, setFeatures] =
    useState([])

  const [target, setTarget] =
    useState('')

  const [testSize, setTestSize] =
    useState('0.4')

  const [randomState, setRandomState] =
    useState('42')

  const [nClusters, setNClusters] =
    useState('2')

  const [trainingResult, setTrainingResult] =
    useState(null)

  const [selectedModel, setSelectedModel] =
    useState(null)

  const [predictionValues, setPredictionValues] =
    useState({})

  const [predictionResult, setPredictionResult] =
    useState(null)

  const [loading, setLoading] =
    useState(true)

  const [training, setTraining] =
    useState(false)

  const [predicting, setPredicting] =
    useState(false)

  const [error, setError] =
    useState('')


  const selectedDataset =
    useMemo(
      () =>
        datasets.find(
          (dataset) =>
            dataset.id ===
            selectedDatasetId
        ),
      [
        datasets,
        selectedDatasetId,
      ]
    )


  const datasetModels =
    useMemo(
      () =>
        models.filter(
          (model) =>
            model.dataset_id ===
            selectedDatasetId
        ),
      [
        models,
        selectedDatasetId,
      ]
    )


  const loadData = async () => {
    setLoading(true)
    setError('')

    try {
      const [
        datasetsResponse,
        modelsResponse,
      ] = await Promise.all([
        api.get('/datasets'),
        api.get('/ml/models'),
      ])

      const datasetItems =
        datasetsResponse.data.datasets || []

      setDatasets(datasetItems)

      setModels(
        modelsResponse.data.models || []
      )

      if (
        datasetItems.length > 0 &&
        !selectedDatasetId
      ) {
        setSelectedDatasetId(
          datasetItems[0].id
        )
      }

    } catch (err) {
      setError(
        getErrorMessage(
          err,
          'Unable to load ML data.'
        )
      )

    } finally {
      setLoading(false)
    }
  }


  useEffect(() => {
    loadData()
  }, [])


  useEffect(() => {
    const firstAlgorithm =
      TASKS[task]
        .algorithms[0]
        .value

    setAlgorithm(firstAlgorithm)
    setFeatures([])
    setTarget('')
    setTrainingResult(null)
    setPredictionResult(null)

  }, [task])


  useEffect(() => {
    setFeatures([])
    setTarget('')
    setTrainingResult(null)
    setSelectedModel(null)
    setPredictionResult(null)
  }, [selectedDatasetId])


  const toggleFeature = (
    column
  ) => {
    setFeatures(
      (previous) => {

        if (
          previous.includes(column)
        ) {
          return previous.filter(
            (item) =>
              item !== column
          )
        }

        return [
          ...previous,
          column,
        ]
      }
    )
  }


  const trainModel =
    async () => {

      setError('')
      setTrainingResult(null)

      if (!selectedDatasetId) {
        setError(
          'Please select a dataset.'
        )
        return
      }

      if (
        features.length === 0
      ) {
        setError(
          'Select at least one feature.'
        )
        return
      }

      if (
        task !== 'clustering' &&
        !target
      ) {
        setError(
          'Please select a target variable.'
        )
        return
      }

      if (
        task !== 'clustering' &&
        features.includes(target)
      ) {
        setError(
          'The target variable cannot also be used as a feature.'
        )
        return
      }

      const parsedRandomState =
        Number(randomState)

      if (
        !Number.isInteger(
          parsedRandomState
        )
      ) {
        setError(
          'Random state must be an integer.'
        )
        return
      }

      setTraining(true)

      try {
        let response

        if (
          task === 'regression'
        ) {
          response =
            await api.post(
              `/ml/train/regression/${selectedDatasetId}`,
              {
                target,
                features,
                algorithm,
                test_size:
                  Number(testSize),
                random_state:
                  parsedRandomState,
              }
            )
        }


        if (
          task === 'classification'
        ) {
          response =
            await api.post(
              `/ml/train/classification/${selectedDatasetId}`,
              {
                target,
                features,
                algorithm,
                test_size:
                  Number(testSize),
                random_state:
                  parsedRandomState,
              }
            )
        }


        if (
          task === 'clustering'
        ) {
          response =
            await api.post(
              `/ml/train/clustering/${selectedDatasetId}`,
              {
                features,
                algorithm: 'kmeans',
                n_clusters:
                  Number(nClusters),
                random_state:
                  parsedRandomState,
              }
            )
        }


        setTrainingResult(
          response.data
        )

        const modelsResponse =
          await api.get(
            '/ml/models'
          )

        setModels(
          modelsResponse
            .data
            .models || []
        )

      } catch (err) {
        setError(
          getErrorMessage(
            err,
            'Model training failed.'
          )
        )

      } finally {
        setTraining(false)
      }
    }


  const openModel =
    async (modelId) => {

      setError('')
      setPredictionResult(null)

      try {
        const response =
          await api.get(
            `/ml/models/${modelId}`
          )

        const model =
          response.data

        setSelectedModel(model)

        const fields = {}

        for (
          const feature
          of model.features || []
        ) {
          fields[feature] = ''
        }

        setPredictionValues(
          fields
        )

      } catch (err) {
        setError(
          getErrorMessage(
            err,
            'Unable to load model details.'
          )
        )
      }
    }


  const makePrediction =
    async () => {

      if (
        !selectedModel
      ) {
        return
      }

      const row = {}

      for (
        const feature
        of selectedModel.features || []
      ) {
        const value =
          predictionValues[
            feature
          ]

        if (
          value === '' ||
          value === undefined
        ) {
          setError(
            `Enter a value for ${feature}.`
          )
          return
        }

        row[feature] =
          parseInputValue(
            value
          )
      }

      setPredicting(true)
      setError('')
      setPredictionResult(null)

      try {
        const response =
          await api.post(
            `/ml/predict/${selectedModel.model_id}`,
            {
              rows: [
                row,
              ],
            }
          )

        setPredictionResult(
          response.data
        )

      } catch (err) {
        setError(
          getErrorMessage(
            err,
            'Prediction failed.'
          )
        )

      } finally {
        setPredicting(false)
      }
    }


  return (
    <AppShell>

      <header className="ml-header">

        <div>
          <span className="eyebrow dark">
            ARTIFICIAL INTELLIGENCE
          </span>

          <h1>
            AI / Machine Learning
          </h1>

          <p>
            Train regression,
            classification and
            clustering models using
            your SSAS datasets.
          </p>
        </div>

        <div className="ml-header-icon">
          <BrainCircuit size={30} />
        </div>

      </header>


      {error && (
        <div className="alert error">
          {error}
        </div>
      )}


      {loading ? (

        <div className="ml-loading">
          <LoaderCircle
            size={30}
            className="spin-icon"
          />

          Loading machine learning
          workspace...
        </div>

      ) : (

        <>
          <section className="ml-grid">

            <div className="ml-config-card">

              <div className="ml-card-heading">

                <Database size={20} />

                <div>
                  <strong>
                    Dataset
                  </strong>

                  <span>
                    Select training data
                  </span>
                </div>

              </div>


              <label className="ml-label">
                Dataset
              </label>

              <div className="select-wrapper">

                <select
                  value={
                    selectedDatasetId
                  }
                  onChange={(event) =>
                    setSelectedDatasetId(
                      event.target.value
                    )
                  }
                >
                  {datasets.map(
                    (dataset) => (
                      <option
                        key={dataset.id}
                        value={dataset.id}
                      >
                        {
                          dataset
                            .original_filename
                        }
                      </option>
                    )
                  )}
                </select>

                <ChevronDown
                  size={16}
                />

              </div>


              {selectedDataset && (

                <div className="ml-dataset-info">

                  <strong>
                    {
                      selectedDataset
                        .original_filename
                    }
                  </strong>

                  <span>
                    {
                      selectedDataset
                        .row_count
                    } rows · {
                      selectedDataset
                        .column_count
                    } columns
                  </span>

                </div>

              )}


              <div className="ml-divider" />


              <div className="ml-card-heading">

                <BrainCircuit size={20} />

                <div>
                  <strong>
                    Learning Task
                  </strong>

                  <span>
                    Choose model type
                  </span>
                </div>

              </div>


              <label className="ml-label">
                Task
              </label>

              <select
                className="analysis-select"
                value={task}
                onChange={(event) =>
                  setTask(
                    event.target.value
                  )
                }
              >
                <option value="regression">
                  Regression
                </option>

                <option value="classification">
                  Classification
                </option>

                <option value="clustering">
                  Clustering
                </option>
              </select>


              <label className="ml-label">
                Algorithm
              </label>

              <select
                className="analysis-select"
                value={algorithm}
                onChange={(event) =>
                  setAlgorithm(
                    event.target.value
                  )
                }
              >
                {
                  TASKS[
                    task
                  ].algorithms.map(
                    (item) => (
                      <option
                        key={
                          item.value
                        }
                        value={
                          item.value
                        }
                      >
                        {
                          item.label
                        }
                      </option>
                    )
                  )
                }
              </select>


              <button
                className="ml-refresh-button"
                onClick={loadData}
              >
                <RefreshCw size={16} />
                Refresh
              </button>

            </div>


            <div className="ml-training-card">

              <div className="ml-section-header">

                <div>
                  <span className="eyebrow dark">
                    MODEL CONFIGURATION
                  </span>

                  <h2>
                    Train Model
                  </h2>
                </div>

                <Sparkles size={23} />

              </div>


              {task !==
                'clustering' && (

                <>
                  <label className="ml-label">
                    Target Variable
                  </label>

                  <select
                    className="analysis-select"
                    value={target}
                    onChange={(event) =>
                      setTarget(
                        event.target.value
                      )
                    }
                  >
                    <option value="">
                      Select target...
                    </option>

                    {
                      selectedDataset
                        ?.columns
                        ?.map(
                          (column) => (
                            <option
                              key={
                                column
                              }
                              value={
                                column
                              }
                            >
                              {column}
                            </option>
                          )
                        )
                    }
                  </select>
                </>
              )}


              <label className="ml-label">
                Features
              </label>

              <p className="ml-help">
                Select the variables
                that should be used as
                model inputs.
              </p>


              <div className="ml-feature-grid">

                {
                  selectedDataset
                    ?.columns
                    ?.map(
                      (column) => (

                        <label
                          key={column}
                          className={
                            features
                              .includes(
                                column
                              )
                              ? 'ml-feature selected'
                              : 'ml-feature'
                          }
                        >

                          <input
                            type="checkbox"
                            checked={
                              features
                                .includes(
                                  column
                                )
                            }
                            disabled={
                              task !==
                                'clustering' &&
                              target ===
                                column
                            }
                            onChange={() =>
                              toggleFeature(
                                column
                              )
                            }
                          />

                          <span>
                            {column}
                          </span>

                        </label>

                      )
                    )
                }

              </div>


              <div className="ml-options-grid">

                {task !==
                  'clustering' && (

                  <div>
                    <label className="ml-label">
                      Test Size
                    </label>

                    <select
                      className="analysis-select"
                      value={testSize}
                      onChange={(event) =>
                        setTestSize(
                          event.target.value
                        )
                      }
                    >
                      <option value="0.2">
                        20%
                      </option>

                      <option value="0.3">
                        30%
                      </option>

                      <option value="0.4">
                        40%
                      </option>
                    </select>
                  </div>

                )}


                {task ===
                  'clustering' && (

                  <div>
                    <label className="ml-label">
                      Number of Clusters
                    </label>

                    <input
                      className="analysis-input"
                      type="number"
                      min="2"
                      value={nClusters}
                      onChange={(event) =>
                        setNClusters(
                          event.target.value
                        )
                      }
                    />
                  </div>

                )}


                <div>
                  <label className="ml-label">
                    Random State
                  </label>

                  <input
                    className="analysis-input"
                    type="number"
                    value={randomState}
                    onChange={(event) =>
                      setRandomState(
                        event.target.value
                      )
                    }
                  />
                </div>

              </div>


              <button
                className="ml-train-button"
                onClick={trainModel}
                disabled={
                  training
                }
              >

                {training ? (
                  <>
                    <LoaderCircle
                      size={18}
                      className="spin-icon"
                    />

                    Training Model...
                  </>
                ) : (
                  <>
                    <Play size={18} />
                    Train Model
                  </>
                )}

              </button>

            </div>

          </section>


          <section className="ml-results-grid">

            <div className="ml-result-card">

              <div className="ml-section-header">

                <div>
                  <span className="eyebrow dark">
                    PERFORMANCE
                  </span>

                  <h2>
                    Training Result
                  </h2>
                </div>

                {trainingResult && (
                  <CheckCircle2
                    size={24}
                    className="ml-success"
                  />
                )}

              </div>


              {!trainingResult ? (

                <div className="ml-empty">

                  <BrainCircuit
                    size={44}
                  />

                  <h3>
                    No new model trained
                  </h3>

                  <p>
                    Configure the model
                    above and click
                    Train Model.
                  </p>

                </div>

              ) : (

                <DynamicResult
                  value={
                    trainingResult
                  }
                />

              )}

            </div>


            <div className="ml-result-card">

              <div className="ml-section-header">

                <div>
                  <span className="eyebrow dark">
                    MODEL HISTORY
                  </span>

                  <h2>
                    Existing Models
                  </h2>
                </div>

                <History size={23} />

              </div>


              <div className="ml-model-list">

                {datasetModels.length ===
                  0 ? (

                  <div className="ml-empty small">

                    <p>
                      No trained models
                      for this dataset.
                    </p>

                  </div>

                ) : (

                  datasetModels.map(
                    (model) => (

                      <button
                        key={
                          model.model_id
                        }
                        className="ml-model-item"
                        onClick={() =>
                          openModel(
                            model.model_id
                          )
                        }
                      >

                        <div className="ml-model-icon">
                          <BrainCircuit
                            size={18}
                          />
                        </div>

                        <div className="ml-model-copy">

                          <strong>
                            {
                              humanize(
                                model
                                  .algorithm
                              )
                            }
                          </strong>

                          <span>
                            {
                              humanize(
                                model.task
                              )
                            }
                            {' · '}
                            {
                              model
                                .features
                                .length
                            } feature(s)
                          </span>

                        </div>

                        <div className="ml-model-date">
                          {
                            formatDate(
                              model.created_at
                            )
                          }
                        </div>

                      </button>

                    )
                  )
                )}

              </div>

            </div>

          </section>


          {selectedModel && (

            <section className="ml-prediction-card">

              <div className="ml-section-header">

                <div>
                  <span className="eyebrow dark">
                    PREDICTION
                  </span>

                  <h2>
                    Use Trained Model
                  </h2>

                  <p>
                    {
                      humanize(
                        selectedModel
                          .algorithm
                      )
                    }
                  </p>
                </div>

                <Target size={24} />

              </div>


              <div className="ml-model-metrics">

                <DynamicResult
                  value={
                    selectedModel
                      .metrics || {}
                  }
                />

              </div>


              <div className="ml-divider" />


              <h3>
                Prediction Inputs
              </h3>


              <div className="ml-prediction-fields">

                {
                  selectedModel
                    .features
                    ?.map(
                      (feature) => (

                        <div key={feature}>

                          <label className="ml-label">
                            {humanize(feature)}
                          </label>

                          <input
                            className="analysis-input"
                            value={
                              predictionValues[
                                feature
                              ] ?? ''
                            }
                            onChange={(event) =>
                              setPredictionValues(
                                (previous) => ({
                                  ...previous,

                                  [feature]:
                                    event
                                      .target
                                      .value,
                                })
                              )
                            }
                            placeholder={
                              `Enter ${feature}`
                            }
                          />

                        </div>

                      )
                    )
                }

              </div>


              <button
                className="ml-predict-button"
                onClick={makePrediction}
                disabled={predicting}
              >

                {predicting ? (
                  <>
                    <LoaderCircle
                      size={18}
                      className="spin-icon"
                    />

                    Predicting...
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    Make Prediction
                  </>
                )}

              </button>


              {predictionResult && (

                <div className="ml-prediction-result">

                  <span className="eyebrow dark">
                    PREDICTION RESULT
                  </span>

                  <DynamicResult
                    value={
                      predictionResult
                    }
                  />

                </div>

              )}

            </section>

          )}

        </>
      )}

    </AppShell>
  )
}


function DynamicResult({
  value,
  name,
}) {

  if (
    value === null ||
    value === undefined
  ) {
    return (
      <MetricCard
        label={
          name || 'Value'
        }
        value="-"
      />
    )
  }


  if (
    typeof value !==
    'object'
  ) {
    return (
      <MetricCard
        label={
          name
            ? humanize(name)
            : 'Value'
        }
        value={
          formatValue(value)
        }
      />
    )
  }


  if (
    Array.isArray(value)
  ) {
    return (
      <div className="ml-array">

        {name && (
          <h4>
            {humanize(name)}
          </h4>
        )}

        {value.map(
          (
            item,
            index
          ) => (
            <DynamicResult
              key={index}
              name={
                typeof item ===
                'object'
                  ? `Item ${
                      index + 1
                    }`
                  : `${index + 1}`
              }
              value={item}
            />
          )
        )}

      </div>
    )
  }


  return (
    <div className="ml-dynamic">

      {name && (
        <h4>
          {humanize(name)}
        </h4>
      )}

      <div className="ml-metric-grid">

        {
          Object.entries(
            value
          ).map(
            ([key, item]) => (

              <DynamicResult
                key={key}
                name={key}
                value={item}
              />

            )
          )
        }

      </div>

    </div>
  )
}


function MetricCard({
  label,
  value,
}) {
  return (
    <div className="ml-metric">

      <span>
        {label}
      </span>

      <strong>
        {String(value)}
      </strong>

    </div>
  )
}


function formatValue(
  value
) {
  if (
    typeof value ===
    'number'
  ) {
    if (
      Number.isInteger(value)
    ) {
      return value
    }

    return Number(
      value.toFixed(5)
    )
  }

  if (
    typeof value ===
    'boolean'
  ) {
    return value
      ? 'Yes'
      : 'No'
  }

  return value
}


function humanize(
  value
) {
  return String(value)
    .replaceAll('_', ' ')
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase()
    )
}


function formatDate(
  value
) {
  if (!value) {
    return '-'
  }

  return new Date(
    value
  ).toLocaleDateString()
}


function parseInputValue(
  value
) {
  const trimmed =
    String(value).trim()

  if (
    trimmed === ''
  ) {
    return ''
  }

  const numeric =
    Number(trimmed)

  if (
    !Number.isNaN(numeric)
  ) {
    return numeric
  }

  return trimmed
}


function getErrorMessage(
  error,
  fallback
) {
  const detail =
    error.response
      ?.data
      ?.detail

  if (
    typeof detail ===
    'string'
  ) {
    return detail
  }

  if (
    Array.isArray(detail)
  ) {
    return detail
      .map(
        (item) =>
          item.msg ||
          JSON.stringify(item)
      )
      .join(' ')
  }

  return (
    error.message ||
    fallback
  )
}
