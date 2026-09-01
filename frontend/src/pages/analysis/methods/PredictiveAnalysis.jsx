import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  BrainCircuit,
  Calculator,
  Check,
  FileText,
  Lightbulb,
  Save,
  Sparkles,
  Target,
  TrendingUp,
} from 'lucide-react'

import api
  from '../../../api/api'

import ResultTable
  from '../components/ResultTable'

import DetailedExplanation
  from '../components/DetailedExplanation'


// ==========================================================
// ERROR MESSAGE
// ==========================================================

function getErrorMessage(
  error
) {
  const detail =
    error?.response?.data?.detail

  if (
    typeof detail ===
    'string'
  ) {
    return detail
  }

  return (
    error?.message ||
    'Unable to perform predictive analysis.'
  )
}


// ==========================================================
// NORMALIZE VARIABLE
// ==========================================================

function normalizeVariable(
  item
) {
  if (
    typeof item ===
    'string'
  ) {
    return {
      name:
        item,

      measurement_level:
        'nominal',

      data_type:
        '',
    }
  }


  return {
    ...item,

    name:
      item.column ||
      item.name ||
      item.variable ||
      '',

    measurement_level:
      item.measurement_level ||
      item
        .inferred_measurement_level ||
      'nominal',

    data_type:
      item.data_type ||
      item.dtype ||
      item.type ||
      '',
  }
}


// ==========================================================
// TIME VARIABLE
// ==========================================================

function isTimeVariable(
  variable
) {
  const name =
    String(
      variable?.name ||
      ''
    )
      .trim()
      .toLowerCase()


  const type =
    String(
      variable?.data_type ||
      ''
    )
      .trim()
      .toLowerCase()


  return (
    name ===
    'date'
    ||
    name ===
    'time'
    ||
    name.includes(
      'date'
    )
    ||
    name.includes(
      'timestamp'
    )
    ||
    type.includes(
      'date'
    )
    ||
    type.includes(
      'time'
    )
  )
}


// ==========================================================
// NUMBER FORMAT
// ==========================================================

function formatNumber(
  value,
  digits = 3,
) {
  if (
    value === null
    ||
    value === undefined
    ||
    Number.isNaN(
      Number(
        value
      )
    )
  ) {
    return '—'
  }


  return Number(
    value
  ).toLocaleString(
    undefined,
    {
      maximumFractionDigits:
        digits,
    }
  )
}


// ==========================================================
// COMPONENT
// ==========================================================

export default function PredictiveAnalysis({
  dataset,
}) {
  const datasetId =
    dataset?.id


  const [
    variables,
    setVariables,
  ] = useState([])


  const [
    dependentVariable,
    setDependentVariable,
  ] = useState('')


  const [
    predictors,
    setPredictors,
  ] = useState([])


  const [
    futureValues,
    setFutureValues,
  ] = useState({})


  const [
    testSize,
    setTestSize,
  ] = useState('0.20')


  const [
    cvFolds,
    setCvFolds,
  ] = useState('5')


  const [
    randomSeed,
    setRandomSeed,
  ] = useState('42')


  const [
    timeVariable,
    setTimeVariable,
  ] = useState('')


  const [
    loadingVariables,
    setLoadingVariables,
  ] = useState(false)


  const [
    calculating,
    setCalculating,
  ] = useState(false)


  const [
    saving,
    setSaving,
  ] = useState(false)


  const [
    saved,
    setSaved,
  ] = useState(false)


  const [
    result,
    setResult,
  ] = useState(null)


  const [
    error,
    setError,
  ] = useState('')


  const [
    success,
    setSuccess,
  ] = useState('')


  const [
    showExplanation,
    setShowExplanation,
  ] = useState(false)


  const [
    showAPA,
    setShowAPA,
  ] = useState(false)


  // ========================================================
  // LOAD DATASET VARIABLES
  // ========================================================

  useEffect(
    () => {
      if (
        !datasetId
      ) {
        return
      }


      const loadVariables =
        async () => {

          setLoadingVariables(
            true
          )

          setError('')
          setResult(null)
          setDependentVariable('')
          setPredictors([])
          setFutureValues({})
          setSaved(false)


          try {
            const response =
              await api.get(
                `/datasets/${datasetId}/variables`
              )


            const raw =
              response.data?.variables
              ||
              response.data?.columns
              ||
              (
                Array.isArray(
                  response.data
                )
                  ?
                  response.data
                  :
                  []
              )


            const normalized =
              raw
                .map(
                  normalizeVariable
                )
                .filter(
                  (
                    variable
                  ) =>
                    Boolean(
                      variable.name
                    )
                )


            setVariables(
              normalized
            )


            const detectedTime =
              normalized.find(
                (
                  variable
                ) =>
                  isTimeVariable(
                    variable
                  )
              )


            setTimeVariable(
              detectedTime?.name
              ||
              ''
            )

          } catch (
            err
          ) {
            setError(
              getErrorMessage(
                err
              )
            )

          } finally {
            setLoadingVariables(
              false
            )
          }
        }


      loadVariables()
    },

    [
      datasetId,
    ]
  )


  // ========================================================
  // ELIGIBLE NUMERIC VARIABLES
  // ========================================================

  const eligibleVariables =
    useMemo(
      () =>
        variables.filter(
          (
            variable
          ) =>
            !isTimeVariable(
              variable
            )
            &&
            (
              variable
                .measurement_level
              ===
              'metric'
              ||
              variable
                .measurement_level
              ===
              'ordinal'
            )
        ),

      [
        variables,
      ]
    )


  // ========================================================
  // NOMINAL VARIABLES
  // ========================================================

  const nominalVariables =
    useMemo(
      () =>
        variables.filter(
          (
            variable
          ) =>
            !isTimeVariable(
              variable
            )
            &&
            variable
              .measurement_level
            ===
            'nominal'
        ),

      [
        variables,
      ]
    )


  // ========================================================
  // TIME VARIABLES
  // ========================================================

  const timeVariables =
    useMemo(
      () =>
        variables.filter(
          (
            variable
          ) =>
            isTimeVariable(
              variable
            )
        ),

      [
        variables,
      ]
    )


  // ========================================================
  // SELECT FUTURE OUTCOME
  // ========================================================

  const selectDependent =
    (
      variableName
    ) => {

      setDependentVariable(
        variableName
      )


      setPredictors(
        (
          previous
        ) =>
          previous.filter(
            (
              item
            ) =>
              item !==
              variableName
          )
      )


      setFutureValues(
        (
          previous
        ) => {

          const updated = {
            ...previous,
          }


          delete updated[
            variableName
          ]


          return updated
        }
      )


      setResult(null)
      setSaved(false)
      setSuccess('')
    }


  // ========================================================
  // TOGGLE PREDICTOR
  // ========================================================

  const togglePredictor =
    (
      variableName
    ) => {

      if (
        variableName
        ===
        dependentVariable
      ) {
        return
      }


      if (
        predictors.includes(
          variableName
        )
      ) {

        setPredictors(
          (
            previous
          ) =>
            previous.filter(
              (
                item
              ) =>
                item !==
                variableName
            )
        )


        setFutureValues(
          (
            previous
          ) => {

            const updated = {
              ...previous,
            }


            delete updated[
              variableName
            ]


            return updated
          }
        )

      } else {

        setPredictors(
          (
            previous
          ) => [
            ...previous,
            variableName,
          ]
        )


        setFutureValues(
          (
            previous
          ) => ({
            ...previous,

            [variableName]:
              '',
          })
        )
      }


      setResult(null)
      setSaved(false)
      setSuccess('')
    }


  // ========================================================
  // FUTURE VALUE
  // ========================================================

  const updateFutureValue =
    (
      predictor,
      value
    ) => {

      setFutureValues(
        (
          previous
        ) => ({
          ...previous,

          [predictor]:
            value,
        })
      )
    }


  // ========================================================
  // RUN SMART PREDICTION
  // ========================================================

  const calculate =
    async () => {

      if (
        !dependentVariable
      ) {
        setError(
          'Select a future outcome variable.'
        )

        return
      }


      if (
        predictors.length
        ===
        0
      ) {
        setError(
          'Select at least one predictor variable.'
        )

        return
      }


      const scenario = {}


      predictors.forEach(
        (
          predictor
        ) => {

          const rawValue =
            futureValues[
              predictor
            ]


          if (
            rawValue !== ''
            &&
            rawValue !== null
            &&
            rawValue !== undefined
          ) {

            const numeric =
              Number(
                rawValue
              )


            if (
              Number.isFinite(
                numeric
              )
            ) {
              scenario[
                predictor
              ] = numeric
            }
          }
        }
      )


      setCalculating(
        true
      )

      setError('')
      setSuccess('')
      setResult(null)
      setSaved(false)

      setShowExplanation(
        false
      )

      setShowAPA(
        false
      )


      try {

        const response =
          await api.post(
            `/statistics/predictive-analysis/${datasetId}`,
            {
              dependent_variable:
                dependentVariable,

              predictors:
                predictors,

              test_size:
                Number(
                  testSize
                ),

              random_seed:
                Number(
                  randomSeed
                ),

              cv_folds:
                Number(
                  cvFolds
                ),

              future_values:
                Object.keys(
                  scenario
                ).length
                  ?
                  scenario
                  :
                  null,

              time_variable:
                timeVariable
                ||
                null,
            }
          )


        setResult(
          response.data
        )

      } catch (
        err
      ) {

        setError(
          getErrorMessage(
            err
          )
        )

      } finally {

        setCalculating(
          false
        )
      }
    }


  // ========================================================
  // SAVE RESULT
  // ========================================================

  const saveResult =
    async () => {

      if (
        !result
      ) {
        return
      }


      setSaving(
        true
      )

      setError('')
      setSuccess('')


      try {

        await api.post(
          '/statistics/results',
          {
            dataset_id:
              datasetId,

            dataset_name:
              dataset
                ?.original_filename
              ||
              dataset
                ?.filename,

            method:
              'predictive',

            title:
              (
                `Smart Predictive Analytics — ${
                  result.best_model
                  ||
                  'Best Model'
                }`
              ),

            configuration:
              result
                .configuration,

            tables:
              result
                .tables,

            interpretation:
              result
                .interpretation,

            detailed_explanation:
              result
                .detailed_explanation,

            apa:
              result
                .apa,

            metadata: {
              best_model:
                result
                  .best_model,

              prediction:
                result
                  .prediction,

              metrics:
                result
                  .metrics,

              recommendations:
                result
                  .recommendations,
            },
          }
        )


        setSaved(
          true
        )

        setSuccess(
          'Predictive analysis result saved successfully.'
        )

      } catch (
        err
      ) {

        setError(
          getErrorMessage(
            err
          )
        )

      } finally {

        setSaving(
          false
        )
      }
    }


  // ========================================================
  // LOADING
  // ========================================================

  if (
    loadingVariables
  ) {
    return (
      <div className="analysis-method-loading">

        Loading variables...

      </div>
    )
  }


  const prediction =
    result?.prediction
    ||
    {}


  const metrics =
    result?.metrics
    ||
    {}


  const recommendations =
    result?.recommendations
    ||
    []


  // ========================================================
  // RENDER
  // ========================================================

  return (
    <div className="predictive-analysis">


      {/* ==================================================
          CONFIGURATION
          ================================================== */}

      <section className="analysis-configuration">


        <div className="analysis-section-label">

          Smart Prediction Configuration

        </div>


        {/* AUTOMATIC MODEL SELECTION */}

        <div className="predictive-model-mode">

          <div className="predictive-model-mode-icon">

            <BrainCircuit
              size={18}
            />

          </div>


          <div>

            <strong>
              Automatic Machine Learning Model Selection
            </strong>

            <p>
              SSAS compares Linear Regression,
              Decision Tree, Random Forest and
              Gradient Boosting using cross-validation,
              then automatically selects the strongest
              predictive model.
            </p>

          </div>

        </div>


        {/* VARIABLES */}

        <div className="regression-variable-layout">


          {/* FUTURE OUTCOME */}

          <div className="regression-variable-panel">

            <h3>
              Future Outcome
            </h3>

            <p>
              Select the variable SSAS should predict.
            </p>


            <div className="analysis-variable-list">

              {eligibleVariables.map(
                (
                  variable
                ) => (

                  <label
                    key={
                      variable.name
                    }
                  >

                    <input
                      type="radio"

                      name="predictive-outcome"

                      checked={
                        dependentVariable
                        ===
                        variable.name
                      }

                      onChange={() =>
                        selectDependent(
                          variable.name
                        )
                      }
                    />


                    <span>
                      {variable.name}
                    </span>

                  </label>

                )
              )}

            </div>

          </div>


          {/* PREDICTORS */}

          <div className="regression-variable-panel">

            <h3>
              Predictor Variables
            </h3>

            <p>
              Select variables used to predict the outcome.
            </p>


            <div className="analysis-variable-list">

              {eligibleVariables.map(
                (
                  variable
                ) => (

                  <label
                    key={
                      variable.name
                    }

                    className={
                      dependentVariable
                      ===
                      variable.name
                        ?
                        'regression-variable-disabled'
                        :
                        ''
                    }
                  >

                    <input
                      type="checkbox"

                      disabled={
                        dependentVariable
                        ===
                        variable.name
                      }

                      checked={
                        predictors.includes(
                          variable.name
                        )
                      }

                      onChange={() =>
                        togglePredictor(
                          variable.name
                        )
                      }
                    />


                    <span>
                      {variable.name}
                    </span>

                  </label>

                )
              )}

            </div>

          </div>


          {/* NOMINAL VARIABLES */}

          <div className="regression-variable-panel">

            <h3>
              Nominal Variables
            </h3>

            <p>
              Categorical prediction models will be added separately.
            </p>


            <div className="analysis-variable-list">

              {nominalVariables.map(
                (
                  variable
                ) => (

                  <label
                    key={
                      variable.name
                    }

                    className="regression-variable-disabled"
                  >

                    <input
                      type="checkbox"
                      disabled
                    />


                    <span>
                      {variable.name}
                    </span>

                  </label>

                )
              )}

            </div>

          </div>

        </div>


        {/* ==================================================
            MODEL VALIDATION SETTINGS
            ================================================== */}

        <div className="predictive-settings-section">

          <h3>
            Model Validation
          </h3>


          <div className="predictive-settings-grid">


            <div>

              <label>
                Holdout Test Data
              </label>


              <select
                value={
                  testSize
                }

                onChange={
                  (
                    event
                  ) =>
                    setTestSize(
                      event
                        .target
                        .value
                    )
                }
              >
                <option value="0.10">
                  10%
                </option>

                <option value="0.20">
                  20%
                </option>

                <option value="0.30">
                  30%
                </option>

                <option value="0.40">
                  40%
                </option>
              </select>

            </div>


            <div>

              <label>
                Cross Validation
              </label>


              <select
                value={
                  cvFolds
                }

                onChange={
                  (
                    event
                  ) =>
                    setCvFolds(
                      event
                        .target
                        .value
                    )
                }
              >
                <option value="3">
                  3 folds
                </option>

                <option value="5">
                  5 folds
                </option>

                <option value="10">
                  10 folds
                </option>
              </select>

            </div>


            <div>

              <label>
                Random Seed
              </label>


              <input
                type="number"

                value={
                  randomSeed
                }

                onChange={
                  (
                    event
                  ) =>
                    setRandomSeed(
                      event
                        .target
                        .value
                    )
                }
              />

            </div>


            <div>

              <label>
                Time Variable
              </label>


              <select
                value={
                  timeVariable
                }

                onChange={
                  (
                    event
                  ) =>
                    setTimeVariable(
                      event
                        .target
                        .value
                    )
                }
              >

                <option value="">
                  None
                </option>


                {timeVariables.map(
                  (
                    variable
                  ) => (

                    <option
                      key={
                        variable.name
                      }

                      value={
                        variable.name
                      }
                    >

                      {variable.name}

                    </option>

                  )
                )}

              </select>

            </div>

          </div>

        </div>


        {/* ==================================================
            FUTURE SCENARIO
            ================================================== */}

        <div className="predictive-future-section">

          <div className="predictive-future-heading">

            <div>

              <Target
                size={18}
              />

            </div>


            <div>

              <h3>
                Future Scenario
              </h3>

              <p>
                Enter the expected future values for
                the selected predictors. If a value
                is left blank, SSAS uses the median
                value from the training data.
              </p>

            </div>

          </div>


          {predictors.length > 0 ? (

            <div className="predictive-future-grid">

              {predictors.map(
                (
                  predictor
                ) => (

                  <div
                    key={
                      predictor
                    }
                  >

                    <label>
                      {predictor}
                    </label>


                    <input
                      type="number"

                      step="any"

                      placeholder="Future value"

                      value={
                        futureValues[
                          predictor
                        ]
                        ??
                        ''
                      }

                      onChange={
                        (
                          event
                        ) =>
                          updateFutureValue(
                            predictor,
                            event
                              .target
                              .value
                          )
                      }
                    />

                  </div>

                )
              )}

            </div>

          ) : (

            <div className="predictive-empty-scenario">

              Select predictor variables to
              create a future scenario.

            </div>

          )}

        </div>


        {/* CURRENT TARGET */}

        <div className="regression-current-model">

          <span>
            Prediction Target
          </span>


          <strong>

            {
              dependentVariable
              ||
              'Future Outcome'
            }

            {' ← '}

            {
              predictors.length
                ?
                predictors.join(
                  ' + '
                )
                :
                'Predictor(s)'
            }

          </strong>

        </div>


        {/* CALCULATE */}

        <button
          type="button"

          className="analysis-calculate-button"

          disabled={
            calculating
          }

          onClick={
            calculate
          }
        >

          <Calculator
            size={16}
          />


          {
            calculating
              ?
              'Comparing models...'
              :
              'Predict Future Outcome'
          }

        </button>

      </section>


      {/* ERROR */}

      {error && (

        <div className="analysis-error">

          {error}

        </div>

      )}


      {/* SUCCESS */}

      {success && (

        <div className="correlation-success">

          <Check
            size={14}
          />

          {success}

        </div>

      )}


      {/* ==================================================
          RESULT
          ================================================== */}

      {result && (

        <section className="analysis-results-container">


          {/* RESULT HEADER */}

          <div className="correlation-result-title">

            <div>

              <span>
                SMART PREDICTIVE RESULT
              </span>


              <h2>

                {
                  result.best_model
                }

              </h2>


              <p>

                SSAS automatically selected
                {' '}

                <strong>

                  {
                    result.best_model
                  }

                </strong>

                {' '}
                as the strongest predictive model.

              </p>

            </div>


            <div className="correlation-result-tools">


              <button
                type="button"

                onClick={() =>
                  setShowExplanation(
                    (
                      previous
                    ) =>
                      !previous
                  )
                }
              >

                <Sparkles
                  size={14}
                />

                Explain

              </button>


              <button
                type="button"

                onClick={() =>
                  setShowAPA(
                    (
                      previous
                    ) =>
                      !previous
                  )
                }
              >

                <FileText
                  size={14}
                />

                APA Style

              </button>


              <button
                type="button"

                className="correlation-save-result"

                disabled={
                  saving
                  ||
                  saved
                }

                onClick={
                  saveResult
                }
              >

                {
                  saved
                    ?
                    (
                      <Check
                        size={14}
                      />
                    )
                    :
                    (
                      <Save
                        size={14}
                      />
                    )
                }


                {
                  saving
                    ?
                    'Saving...'
                    :
                    saved
                      ?
                      'Saved'
                      :
                      'Save Result'
                }

              </button>

            </div>

          </div>


          {/* ==================================================
              SUMMARY CARDS
              ================================================== */}

          <div className="predictive-smart-summary">


            <div className="predictive-summary-card">

              <BrainCircuit
                size={16}
              />

              <span>
                Best Model
              </span>

              <strong>
                {
                  result.best_model
                  ||
                  '—'
                }
              </strong>

            </div>


            <div className="predictive-summary-card predictive-summary-primary">

              <TrendingUp
                size={16}
              />

              <span>
                Future Prediction
              </span>

              <strong>
                {
                  formatNumber(
                    prediction
                      .future_prediction,
                    2
                  )
                }
              </strong>

            </div>


            <div className="predictive-summary-card">

              <span>
                Historical Average
              </span>

              <strong>
                {
                  formatNumber(
                    prediction
                      .historical_average,
                    2
                  )
                }
              </strong>

            </div>


            <div className="predictive-summary-card">

              <span>
                Test R²
              </span>

              <strong>
                {
                  formatNumber(
                    metrics[
                      'R²'
                    ],
                    4
                  )
                }
              </strong>

            </div>


            <div className="predictive-summary-card">

              <span>
                RMSE
              </span>

              <strong>
                {
                  formatNumber(
                    metrics
                      .RMSE,
                    3
                  )
                }
              </strong>

            </div>


            <div className="predictive-summary-card">

              <span>
                MAE
              </span>

              <strong>
                {
                  formatNumber(
                    metrics
                      .MAE,
                    3
                  )
                }
              </strong>

            </div>

          </div>


          {/* VALIDATION METHOD */}

          <div className="predictive-validation-banner">

            <strong>
              Validation Method:
            </strong>

            <span>

              {
                prediction
                  .split_method
                ||
                'Holdout validation'
              }

            </span>

          </div>


          {/* ==================================================
              RECOMMENDATIONS
              ================================================== */}

          {recommendations.length > 0 && (

            <div className="predictive-recommendations">

              <div className="predictive-recommendations-heading">

                <Lightbulb
                  size={17}
                />

                <div>

                  <h3>
                    Smart Recommendations
                  </h3>

                  <p>
                    Model-based decision support generated
                    from predictions, feature importance,
                    historical performance and sensitivity analysis.
                  </p>

                </div>

              </div>


              <div className="predictive-recommendation-list">

                {recommendations.map(
                  (
                    recommendation,
                    index
                  ) => (

                    <div
                      className="predictive-recommendation-item"

                      key={
                        `${recommendation.Priority}-${index}`
                      }
                    >

                      <span className="predictive-recommendation-priority">

                        {
                          recommendation
                            .Priority
                        }

                      </span>


                      <p>

                        {
                          recommendation
                            .Recommendation
                        }

                      </p>

                    </div>

                  )
                )}

              </div>

            </div>

          )}


          {/* ==================================================
              TABLES
              ================================================== */}

          {result.tables?.map(
            (
              table,
              index
            ) => (

              <ResultTable
                key={
                  `${table.title}-${index}`
                }

                title={
                  table.title
                }

                columns={
                  table.columns
                }

                rows={
                  table.rows
                }
              />

            )
          )}


          {/* ==================================================
              INTERPRETATION
              ================================================== */}

          {result.interpretation && (

            <div className="predictive-interpretation">

              <strong>
                Predictive Interpretation
              </strong>


              <p>

                {
                  result
                    .interpretation
                }

              </p>

            </div>

          )}


          {/* ==================================================
              EXPLANATION
              ================================================== */}

          {showExplanation && (

            result
              .detailed_explanation
              ?
              (

                <DetailedExplanation
                  explanation={
                    result
                      .detailed_explanation
                  }
                />

              )
              :
              (

                <div className="analysis-error">

                  Detailed explanation was not
                  returned by the Statistics Service.

                </div>

              )

          )}


          {/* ==================================================
              APA RESULT
              ================================================== */}

          {showAPA && result.apa && (

            <div className="analysis-apa-result">

              <div>

                <FileText
                  size={15}
                />


                <strong>
                  APA Style Result
                </strong>

              </div>


              <p>

                {
                  result.apa
                }

              </p>

            </div>

          )}

        </section>

      )}

    </div>
  )
}
