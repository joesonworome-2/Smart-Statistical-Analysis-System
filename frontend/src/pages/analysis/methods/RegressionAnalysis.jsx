import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  Calculator,
  Check,
  ClipboardCheck,
  FileText,
  Save,
  Sparkles,
} from 'lucide-react'

import api
  from '../../../api/api'

import ResultTable
  from '../components/ResultTable'

import DetailedExplanation
  from '../components/DetailedExplanation'


function getErrorMessage(error) {
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
    'Unable to perform regression analysis.'
  )
}


function normalizeVariable(
  item
) {
  if (
    typeof item ===
    'string'
  ) {
    return {
      name: item,
      measurement_level:
        'nominal',
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
  }
}


function normalizeVariables(
  data
) {
  const raw =
    data?.variables ||
    data?.columns ||
    (
      Array.isArray(
        data
      )
        ? data
        : []
    )

  return raw
    .map(
      normalizeVariable
    )
    .filter(
      (item) =>
        item.name
    )
}


export default function RegressionAnalysis({
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
    alpha,
    setAlpha,
  ] = useState('0.05')


  const [
    confidenceLevel,
    setConfidenceLevel,
  ] = useState('0.95')


  const [
    includeIntercept,
    setIncludeIntercept,
  ] = useState(true)


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
    result,
    setResult,
  ] = useState(null)


  const [
    savedResult,
    setSavedResult,
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
    showDiagnostics,
    setShowDiagnostics,
  ] = useState(false)


  const [
    showExplanation,
    setShowExplanation,
  ] = useState(false)


  const [
    showAPA,
    setShowAPA,
  ] = useState(false)


  // ========================================================
  // LOAD VARIABLES
  // ========================================================

  useEffect(
    () => {
      if (!datasetId) {
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


          try {
            const response =
              await api.get(
                `/datasets/${datasetId}/variables`
              )

            setVariables(
              normalizeVariables(
                response.data
              )
            )

          } catch (err) {
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
  // NUMERIC ELIGIBLE VARIABLES
  // ========================================================

  const eligibleVariables =
    useMemo(
      () =>
        variables.filter(
          (variable) =>
            (
              variable
                .measurement_level ===
              'metric'
            )
            ||
            (
              variable
                .measurement_level ===
              'ordinal'
            )
        ),

      [
        variables,
      ]
    )


  const nominalVariables =
    useMemo(
      () =>
        variables.filter(
          (variable) =>
            variable
              .measurement_level ===
            'nominal'
        ),

      [
        variables,
      ]
    )


  // ========================================================
  // PREDICTOR TOGGLE
  // ========================================================

  const togglePredictor =
    (
      variable
    ) => {
      if (
        variable ===
        dependentVariable
      ) {
        return
      }


      setPredictors(
        (previous) =>
          previous.includes(
            variable
          )
            ? previous.filter(
                (item) =>
                  item !==
                  variable
              )
            : [
                ...previous,
                variable,
              ]
      )


      setResult(null)
      setSavedResult(null)
      setSuccess('')
    }


  // ========================================================
  // DEPENDENT VARIABLE
  // ========================================================

  const selectDependent =
    (
      variable
    ) => {
      setDependentVariable(
        variable
      )

      setPredictors(
        (previous) =>
          previous.filter(
            (item) =>
              item !==
              variable
          )
      )

      setResult(null)
      setSavedResult(null)
      setSuccess('')
    }


  // ========================================================
  // CALCULATE
  // ========================================================

  const calculate =
    async () => {
      if (
        !dependentVariable
      ) {
        setError(
          'Select a dependent variable.'
        )

        return
      }


      if (
        predictors.length === 0
      ) {
        setError(
          'Select at least one predictor.'
        )

        return
      }


      setCalculating(
        true
      )

      setError('')
      setSuccess('')
      setResult(null)
      setSavedResult(null)


      try {
        const response =
          await api.post(
            `/statistics/regression-analysis/${datasetId}`,
            {
              dependent_variable:
                dependentVariable,

              predictors,

              alpha:
                Number(
                  alpha
                ),

              confidence_level:
                Number(
                  confidenceLevel
                ),

              include_intercept:
                includeIntercept,
            }
          )


        setResult(
          response.data
        )

      } catch (err) {
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
  // SAVE
  // ========================================================

  const saveResult =
    async () => {
      if (!result) {
        return
      }


      setSaving(true)
      setError('')
      setSuccess('')


      try {
        const response =
          await api.post(
            '/statistics/results',
            {
              dataset_id:
                datasetId,

              dataset_name:
                dataset
                  ?.original_filename,

              method:
                'regression',

              title:
                result
                  .test_name,

              configuration:
                result
                  .configuration,

              tables:
                result.tables,

              assumptions:
                result
                  .diagnostics,

              interpretation:
                result
                  .interpretation,

              detailed_explanation:
                result
                  .detailed_explanation,

              apa:
                result.apa,

              metadata: {
                dependent_variable:
                  dependentVariable,

                predictors,
              },
            }
          )


        setSavedResult(
          response.data
        )

        setSuccess(
          'Regression result saved successfully.'
        )

      } catch (err) {
        setError(
          getErrorMessage(
            err
          )
        )

      } finally {
        setSaving(false)
      }
    }


  if (
    loadingVariables
  ) {
    return (
      <div className="analysis-method-loading">
        Loading variables...
      </div>
    )
  }


  return (
    <div className="regression-analysis">


      {/* CONFIGURATION */}

      <section className="analysis-configuration">

        <div className="analysis-section-label">
          Configuration
        </div>


        <div className="regression-variable-layout">


          {/* DEPENDENT */}

          <div className="regression-variable-panel">

            <h3>
              Dependent Variable
            </h3>

            <p>
              Select one outcome variable.
            </p>


            <div className="analysis-variable-list">

              {eligibleVariables.map(
                (variable) => (
                  <label
                    key={
                      variable.name
                    }
                  >

                    <input
                      type="radio"

                      name="dependent-variable"

                      checked={
                        dependentVariable ===
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
              Select one or more predictors.
            </p>


            <div className="analysis-variable-list">

              {eligibleVariables.map(
                (variable) => (
                  <label
                    key={
                      variable.name
                    }

                    className={
                      dependentVariable ===
                      variable.name
                        ? 'regression-variable-disabled'
                        : ''
                    }
                  >

                    <input
                      type="checkbox"

                      disabled={
                        dependentVariable ===
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


          {/* NOMINAL */}

          <div className="regression-variable-panel">

            <h3>
              Nominal Variables
            </h3>

            <p>
              Categorical encoding will be added later.
            </p>


            <div className="analysis-variable-list">

              {nominalVariables.map(
                (variable) => (
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


        {/* OPTIONS */}

        <div className="regression-options">


          <div>

            <label>
              Significance Level (α)
            </label>

            <select
              value={
                alpha
              }

              onChange={(event) =>
                setAlpha(
                  event.target.value
                )
              }
            >
              <option value="0.10">
                0.10
              </option>

              <option value="0.05">
                0.05
              </option>

              <option value="0.01">
                0.01
              </option>
            </select>

          </div>


          <div>

            <label>
              Confidence Level
            </label>

            <select
              value={
                confidenceLevel
              }

              onChange={(event) =>
                setConfidenceLevel(
                  event.target.value
                )
              }
            >
              <option value="0.90">
                90%
              </option>

              <option value="0.95">
                95%
              </option>

              <option value="0.99">
                99%
              </option>
            </select>

          </div>


          <label className="regression-intercept-option">

            <input
              type="checkbox"

              checked={
                includeIntercept
              }

              onChange={(event) =>
                setIncludeIntercept(
                  event.target.checked
                )
              }
            />

            Include intercept

          </label>

        </div>


        {/* CURRENT MODEL */}

        <div className="regression-current-model">

          <span>
            Current Model
          </span>


          <strong>
            {
              dependentVariable ||
              'Outcome'
            }

            {' = '}

            {
              predictors.length
                ? predictors.join(
                    ' + '
                  )
                : 'Predictor(s)'
            }
          </strong>

        </div>


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
              ? 'Calculating...'
              : 'Calculate'
          }

        </button>

      </section>


      {error && (
        <div className="analysis-error">
          {error}
        </div>
      )}


      {success && (
        <div className="correlation-success">

          <Check
            size={14}
          />

          {success}

        </div>
      )}


      {/* RESULTS */}

      {result && (

        <section className="analysis-results-container">


          <div className="correlation-result-title">


            <div>

              <span>
                REGRESSION RESULT
              </span>


              <h2>
                {
                  result
                    .test_name
                }
              </h2>


              <p>
                Outcome:
                {' '}

                <strong>
                  {
                    result
                      .configuration
                      ?.dependent_variable
                  }
                </strong>
              </p>

            </div>


            <div className="correlation-result-tools">


              <button
                type="button"

                onClick={() =>
                  setShowDiagnostics(
                    !showDiagnostics
                  )
                }
              >
                <ClipboardCheck
                  size={14}
                />

                Diagnostics
              </button>


              <button
                type="button"

                onClick={() =>
                  setShowExplanation(
                    !showExplanation
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
                    !showAPA
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
                  saving ||
                  Boolean(
                    savedResult
                  )
                }

                onClick={
                  saveResult
                }
              >

                {savedResult ? (
                  <Check
                    size={14}
                  />
                ) : (
                  <Save
                    size={14}
                  />
                )}


                {
                  saving
                    ? 'Saving...'
                    : savedResult
                      ? 'Saved'
                      : 'Save Result'
                }

              </button>

            </div>

          </div>


          {/* TABLES */}

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


          {/* DIAGNOSTICS */}

          {showDiagnostics &&
            result.diagnostics && (

            <ResultTable
              title={
                result
                  .diagnostics
                  .title
              }

              columns={
                result
                  .diagnostics
                  .columns
              }

              rows={
                result
                  .diagnostics
                  .rows
              }
            />
          )}


          {/* EXPLAIN */}

          {showExplanation && (

            result
              .detailed_explanation ? (

              <DetailedExplanation
                explanation={
                  result
                    .detailed_explanation
                }
              />

            ) : (

              <div className="analysis-error">
                Detailed explanation was
                not returned by the
                Statistics Service.
              </div>

            )

          )}


          {/* APA */}

          {showAPA &&
            result.apa && (

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
                {result.apa}
              </p>

            </div>
          )}

        </section>
      )}

    </div>
  )
}
