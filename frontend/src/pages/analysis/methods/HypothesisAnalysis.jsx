import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  Calculator,
  CheckCircle2,
  ClipboardCheck,
  FileText,
  Sparkles,
} from 'lucide-react'

import api
  from '../../../api/api'

import ResultTable
  from '../components/ResultTable'


// ==========================================================
// HELPERS
// ==========================================================

function getErrorMessage(error) {
  const detail =
    error?.response?.data?.detail

  if (
    typeof detail === 'string'
  ) {
    return detail
  }

  return (
    error?.message ||
    'Unable to perform hypothesis test.'
  )
}


function normalizeVariable(
  item
) {
  if (
    typeof item === 'string'
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


// ==========================================================
// COMPONENT
// ==========================================================

export default function HypothesisAnalysis({
  dataset,
}) {
  const datasetId =
    dataset?.id


  const [
    variables,
    setVariables,
  ] = useState([])


  const [
    selectedMetric,
    setSelectedMetric,
  ] = useState([])


  const [
    selectedCategorical,
    setSelectedCategorical,
  ] = useState([])


  const [
    family,
    setFamily,
  ] = useState(
    'parametric'
  )


  const [
    alternative,
    setAlternative,
  ] = useState(
    'two-sided'
  )


  const [
    testValue,
    setTestValue,
  ] = useState('0')


  const [
    alpha,
    setAlpha,
  ] = useState('0.05')


  const [
    loadingVariables,
    setLoadingVariables,
  ] = useState(false)


  const [
    calculating,
    setCalculating,
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
    showAssumptions,
    setShowAssumptions,
  ] = useState(false)


  const [
    showExplanation,
    setShowExplanation,
  ] = useState(true)


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


      const load =
        async () => {
          setLoadingVariables(
            true
          )

          setError('')

          setResult(null)


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
            setVariables(
              (
                dataset
                  ?.columns ||
                []
              ).map(
                (column) => ({
                  name: column,
                  measurement_level:
                    'nominal',
                })
              )
            )

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


      load()

    },

    [
      datasetId,
    ]
  )


  // ========================================================
  // VARIABLE GROUPS
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
  // SELECTION
  // ========================================================

  const toggleMetric =
    (name) => {
      setSelectedMetric(
        (previous) =>
          previous.includes(
            name
          )
            ? previous.filter(
                (item) =>
                  item !== name
              )
            : [
                ...previous,
                name,
              ]
      )

      setResult(null)
    }


  const toggleCategorical =
    (name) => {
      setSelectedCategorical(
        (previous) =>
          previous.includes(
            name
          )
            ? previous.filter(
                (item) =>
                  item !== name
              )
            : [
                ...previous,
                name,
              ]
      )

      setResult(null)
    }


  // ========================================================
  // PREDICT TEST NAME
  // ========================================================

  const predictedTest =
    useMemo(
      () => {
        const metricCount =
          selectedMetric.length

        const categoricalCount =
          selectedCategorical.length


        if (
          metricCount === 1 &&
          categoricalCount === 0
        ) {
          return (
            family ===
            'parametric'
              ? 'One-Sample t-Test'
              : (
                  'One-Sample Wilcoxon '
                  + 'Signed-Rank Test'
                )
          )
        }


        if (
          metricCount === 2 &&
          categoricalCount === 0
        ) {
          return (
            family ===
            'parametric'
              ? (
                  'Paired Samples '
                  + 't-Test'
                )
              : (
                  'Wilcoxon '
                  + 'Signed-Rank Test'
                )
          )
        }


        if (
          metricCount === 1 &&
          categoricalCount === 1
        ) {
          return (
            family ===
            'parametric'
              ? (
                  'Independent t-Test '
                  + 'or One-Way ANOVA'
                )
              : (
                  'Mann-Whitney U '
                  + 'or Kruskal-Wallis'
                )
          )
        }


        if (
          metricCount === 0 &&
          categoricalCount === 2
        ) {
          return (
            'Chi-Square Test '
            + 'of Independence'
          )
        }


        return (
          'Select variables to '
          + 'determine test'
        )
      },

      [
        selectedMetric,
        selectedCategorical,
        family,
      ]
    )


  const isOneSample =
    selectedMetric.length === 1 &&
    selectedCategorical.length === 0


  // ========================================================
  // CALCULATE
  // ========================================================

  const calculate =
    async () => {
      if (!datasetId) {
        setError(
          'Select a dataset first.'
        )

        return
      }


      setCalculating(true)

      setError('')

      setResult(null)


      try {
        const response =
          await api.post(
            `/statistics/hypothesis/${datasetId}`,
            {
              family,

              metric_variables:
                selectedMetric,

              categorical_variables:
                selectedCategorical,

              test_value:
                Number(
                  testValue
                ),

              alternative,

              alpha:
                Number(alpha),
            }
          )


        setResult(
          response.data
        )

        setShowExplanation(
          true
        )

        setShowAssumptions(
          false
        )

        setShowAPA(
          false
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
  // VARIABLE GROUP
  // ========================================================

  const renderMetricGroup =
    (
      title,
      items
    ) => (
      <div className="analysis-variable-group">

        <h4>
          {title}
        </h4>


        <div className="analysis-variable-list">

          {items.map(
            (variable) => (
              <label
                key={
                  variable.name
                }
              >
                <input
                  type="checkbox"

                  checked={
                    selectedMetric
                      .includes(
                        variable.name
                      )
                  }

                  onChange={() =>
                    toggleMetric(
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
    )


  const renderCategoricalGroup =
    (
      title,
      items
    ) => (
      <div className="analysis-variable-group">

        <h4>
          {title}
        </h4>


        <div className="analysis-variable-list">

          {items.map(
            (variable) => (
              <label
                key={
                  variable.name
                }
              >
                <input
                  type="checkbox"

                  checked={
                    selectedCategorical
                      .includes(
                        variable.name
                      )
                  }

                  onChange={() =>
                    toggleCategorical(
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
    )


  // ========================================================
  // RENDER
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


  return (
    <div className="hypothesis-analysis">


      {/* ==================================================
          VARIABLE SELECTION
      ================================================== */}

      <section className="analysis-configuration">

        <div className="analysis-section-label">
          Configuration
        </div>


        <div className="analysis-variable-grid">

          {renderMetricGroup(
            'Metric Variables',
            metricVariables
          )}


          {renderCategoricalGroup(
            'Ordinal Variables',
            ordinalVariables
          )}


          {renderCategoricalGroup(
            'Nominal Variables',
            nominalVariables
          )}

        </div>


        {/* ==================================================
            TEST FAMILY
        ================================================== */}

        <div className="hypothesis-config-block">

          <h4>
            Calculate
          </h4>


          <div className="hypothesis-radio-row">

            <label>

              <input
                type="radio"

                name="test-family"

                value="parametric"

                checked={
                  family ===
                  'parametric'
                }

                onChange={() =>
                  setFamily(
                    'parametric'
                  )
                }
              />

              Parametric test

            </label>


            <label>

              <input
                type="radio"

                name="test-family"

                value="nonparametric"

                checked={
                  family ===
                  'nonparametric'
                }

                onChange={() =>
                  setFamily(
                    'nonparametric'
                  )
                }
              />

              Nonparametric test

            </label>

          </div>

        </div>


        {/* ==================================================
            AUTO-SELECTED TEST
        ================================================== */}

        <div className="hypothesis-test-preview">

          <span>
            SSAS selected test
          </span>

          <strong>
            {predictedTest}
          </strong>

        </div>


        {/* ==================================================
            ALTERNATIVE
        ================================================== */}

        <div className="hypothesis-config-block">

          <h4>
            Alternative hypothesis
          </h4>


          <div className="hypothesis-radio-column">

            <label>

              <input
                type="radio"
                name="alternative"
                value="two-sided"

                checked={
                  alternative ===
                  'two-sided'
                }

                onChange={() =>
                  setAlternative(
                    'two-sided'
                  )
                }
              />

              Population ≠ Test value

            </label>


            <label>

              <input
                type="radio"
                name="alternative"
                value="greater"

                checked={
                  alternative ===
                  'greater'
                }

                onChange={() =>
                  setAlternative(
                    'greater'
                  )
                }
              />

              Population &gt; Test value

            </label>


            <label>

              <input
                type="radio"
                name="alternative"
                value="less"

                checked={
                  alternative ===
                  'less'
                }

                onChange={() =>
                  setAlternative(
                    'less'
                  )
                }
              />

              Population &lt; Test value

            </label>

          </div>

        </div>


        {/* ==================================================
            TEST VALUE
        ================================================== */}

        {isOneSample && (
          <div className="hypothesis-field">

            <label>
              Test value
            </label>

            <input
              type="number"
              step="any"

              value={
                testValue
              }

              onChange={(event) =>
                setTestValue(
                  event.target.value
                )
              }
            />

          </div>
        )}


        {/* ==================================================
            ALPHA
        ================================================== */}

        <div className="hypothesis-field">

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


      {/* ==================================================
          RESULT
      ================================================== */}

      {result && (

        <section className="analysis-results-container">


          {/* TEST TITLE */}

          <div className="hypothesis-result-title">

            <h2>
              {result.test_name}
            </h2>


            <div className="hypothesis-result-tools">

              <button
                type="button"
                onClick={() =>
                  setShowAssumptions(
                    !showAssumptions
                  )
                }
              >
                <ClipboardCheck
                  size={14}
                />

                Test assumptions
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

            </div>

          </div>


          {/* ================================================
              HYPOTHESES TABLE
          ================================================ */}

          <ResultTable
            title="Hypotheses"

            columns={[
              'Null hypothesis',
              'Alternative hypothesis',
            ]}

            rows={[
              {
                'Null hypothesis':
                  result
                    .hypotheses
                    .null,

                'Alternative hypothesis':
                  result
                    .hypotheses
                    .alternative,
              },
            ]}
          />


          {/* ================================================
              ALL STATISTICAL TABLES
          ================================================ */}

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


          {/* ================================================
              DECISION TABLE
          ================================================ */}

          <ResultTable
            title="Statistical Decision"

            columns={[
              'Alpha',
              'Significant',
              'Decision',
            ]}

            rows={[
              {
                Alpha:
                  result
                    .decision
                    .alpha,

                Significant:
                  result
                    .decision
                    .significant
                    ? 'Yes'
                    : 'No',

                Decision:
                  result
                    .decision
                    .decision,
              },
            ]}
          />


          {/* ================================================
              ASSUMPTIONS
          ================================================ */}

          {showAssumptions &&
            result.assumptions
              ?.length > 0 && (

            <ResultTable
              title="Test Assumptions"

              columns={[
                'Assumption',
                'Check',
                'Statistic',
                'p-value',
                'Status',
              ]}

              rows={
                result.assumptions
              }
            />

          )}


          {/* ================================================
              INTERPRETATION
          ================================================ */}

          {showExplanation && (
            <div className="analysis-interpretation">

              <h4>
                Interpretation
              </h4>

              <p>
                {
                  result
                    .interpretation
                }
              </p>

            </div>
          )}


          {/* ================================================
              APA
          ================================================ */}

          {showAPA && (
            <div className="analysis-apa-result">

              <div>

                <CheckCircle2
                  size={16}
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
