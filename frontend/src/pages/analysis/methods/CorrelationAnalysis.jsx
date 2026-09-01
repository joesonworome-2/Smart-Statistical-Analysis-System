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
    'Unable to perform correlation analysis.'
  )
}


function normalizeVariable(item) {
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
  responseData,
  dataset
) {
  const raw =
    responseData?.variables ||
    responseData?.columns ||
    (
      Array.isArray(
        responseData
      )
        ? responseData
        : []
    )


  if (
    Array.isArray(raw) &&
    raw.length
  ) {
    return raw
      .map(
        normalizeVariable
      )
      .filter(
        (variable) =>
          variable.name
      )
  }


  return (
    dataset?.columns ||
    []
  ).map(
    (column) => ({
      name: column,
      measurement_level:
        'nominal',
    })
  )
}


export default function CorrelationAnalysis({
  dataset,
}) {
  const datasetId =
    dataset?.id


  const [
    variables,
    setVariables,
  ] = useState([])


  const [
    selectedVariables,
    setSelectedVariables,
  ] = useState([])


  const [
    method,
    setMethod,
  ] = useState('auto')


  const [
    alpha,
    setAlpha,
  ] = useState('0.05')


  const [
    confidenceLevel,
    setConfidenceLevel,
  ] = useState('0.95')


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
          setSuccess('')
          setResult(null)
          setSavedResult(null)
          setSelectedVariables([])


          try {
            const response =
              await api.get(
                `/datasets/${datasetId}/variables`
              )

            setVariables(
              normalizeVariables(
                response.data,
                dataset
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
  // MEASUREMENT LEVELS
  // ========================================================

  const metricVariables =
    useMemo(
      () =>
        variables.filter(
          (variable) =>
            variable
              .measurement_level ===
            'metric'
        ),

      [variables]
    )


  const ordinalVariables =
    useMemo(
      () =>
        variables.filter(
          (variable) =>
            variable
              .measurement_level ===
            'ordinal'
        ),

      [variables]
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

      [variables]
    )


  // ========================================================
  // VARIABLE SELECTION
  // ========================================================

  const toggleVariable =
    (name) => {
      setSelectedVariables(
        (previous) =>
          previous.includes(
            name
          )
            ? previous.filter(
                (variable) =>
                  variable !== name
              )
            : [
                ...previous,
                name,
              ]
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
        selectedVariables.length
        < 2
      ) {
        setError(
          'Select at least two metric or ordinal variables.'
        )

        return
      }


      setCalculating(true)

      setError('')
      setSuccess('')
      setResult(null)
      setSavedResult(null)


      try {
        const response =
          await api.post(
            `/statistics/correlation-analysis/${datasetId}`,
            {
              variables:
                selectedVariables,

              method,

              alpha:
                Number(alpha),

              confidence_level:
                Number(
                  confidenceLevel
                ),
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
  // SAVE RESULT
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
                'correlation',

              title:
                'Correlation Analysis',

              configuration:
                result
                  .configuration,

              tables:
                result.tables,

              assumptions:
                result
                  .assumptions,

              interpretation:
                result
                  .interpretation,

              detailed_explanation:
                result
                  .detailed_explanation,

              apa:
                result.apa,

              metadata: {
                requested_method:
                  result
                    .requested_method,

                selected_method:
                  result
                    .selected_method,

                recommendation:
                  result
                    .recommendation,
              },
            }
          )


        setSavedResult(
          response.data
        )

        setSuccess(
          'Correlation result saved successfully.'
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


  // ========================================================
  // VARIABLE GROUP
  // ========================================================

  const renderVariableGroup =
    (
      title,
      items,
      selectable = true
    ) => (
      <div className="analysis-variable-group">

        <h4>
          {title}
        </h4>


        {items.length ? (

          <div className="analysis-variable-list">

            {items.map(
              (variable) => (
                <label
                  key={
                    variable.name
                  }

                  className={
                    selectable
                      ? ''
                      : 'correlation-variable-disabled'
                  }
                >

                  <input
                    type="checkbox"

                    disabled={
                      !selectable
                    }

                    checked={
                      selectable &&
                      selectedVariables
                        .includes(
                          variable.name
                        )
                    }

                    onChange={() =>
                      toggleVariable(
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

        ) : (

          <span className="analysis-empty-variable-group">
            No variables
          </span>

        )}

      </div>
    )


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
    <div className="correlation-analysis">


      {/* CONFIGURATION */}

      <section className="analysis-configuration">

        <div className="analysis-section-label">
          Configuration
        </div>


        <div className="analysis-variable-grid">

          {renderVariableGroup(
            'Metric Variables',
            metricVariables
          )}


          {renderVariableGroup(
            'Ordinal Variables',
            ordinalVariables
          )}


          {renderVariableGroup(
            'Nominal Variables',
            nominalVariables,
            false
          )}

        </div>


        <div className="correlation-config-grid">


          <div className="correlation-field">

            <label>
              Correlation Method
            </label>

            <select
              value={method}

              onChange={(event) =>
                setMethod(
                  event.target.value
                )
              }
            >
              <option value="auto">
                Auto Recommend
              </option>

              <option value="pearson">
                Pearson
              </option>

              <option value="spearman">
                Spearman
              </option>

              <option value="kendall">
                Kendall
              </option>
            </select>

          </div>


          <div className="correlation-field">

            <label>
              Significance Level (α)
            </label>

            <select
              value={alpha}

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


          <div className="correlation-field">

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

        </div>


        <div className="correlation-selected-box">

          <span>
            Selected Variables
          </span>

          <strong>
            {
              selectedVariables.length
            }
          </strong>


          <div className="correlation-selected-list">

            {selectedVariables.map(
              (variable) => (
                <span
                  key={
                    variable
                  }
                >
                  {variable}
                </span>
              )
            )}

          </div>

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

          {calculating
            ? 'Calculating...'
            : 'Calculate'}
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
                CORRELATION RESULT
              </span>

              <h2>
                Correlation Analysis
              </h2>

              <p>
                Method:
                {' '}

                <strong>
                  {
                    result
                      .selected_method
                      ?.toUpperCase()
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

                {saving
                  ? 'Saving...'
                  : savedResult
                    ? 'Saved'
                    : 'Save Result'}
              </button>

            </div>

          </div>


          {/* RECOMMENDATION */}

          {result.recommendation && (

            <div className="correlation-recommendation">

              <Sparkles
                size={17}
              />

              <div>

                <span>
                  SSAS Recommendation
                </span>

                <strong>
                  {
                    result
                      .recommendation
                      .method
                      ?.toUpperCase()
                  }
                </strong>

                <p>
                  {
                    result
                      .recommendation
                      .reason
                  }
                </p>

              </div>

            </div>
          )}


          {/* RESULT TABLES */}

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
            result.assumptions && (

            <ResultTable
              title={
                result
                  .assumptions
                  .title
              }

              columns={
                result
                  .assumptions
                  .columns
              }

              rows={
                result
                  .assumptions
                  .rows
              }
            />
          )}


          {/* DETAILED EXPLAIN */}

          {showExplanation && (

            <DetailedExplanation
              explanation={
                result
                  .detailed_explanation
              }
            />

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
