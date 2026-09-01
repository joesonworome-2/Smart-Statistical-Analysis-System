import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  Calculator,
  Check,
  FileText,
  Save,
  ShieldCheck,
  Sparkles,
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


  if (
    Array.isArray(
      detail
    )
  ) {
    return detail
      .map(
        (
          item
        ) =>
          item?.msg ||
          String(
            item
          )
      )
      .join(
        ', '
      )
  }


  return (
    error?.message ||
    'Unable to perform reliability analysis.'
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
      String(
        item.measurement_level ||
        item.inferred_measurement_level ||
        'nominal'
      )
        .trim()
        .toLowerCase(),

    data_type:
      String(
        item.data_type ||
        item.dtype ||
        item.type ||
        ''
      )
        .trim()
        .toLowerCase(),
  }
}


// ==========================================================
// EXCLUDE UNSUITABLE VARIABLES
// ==========================================================

function isExcludedVariable(
  variable
) {
  const name =
    String(
      variable?.name ||
      ''
    )
      .trim()
      .toLowerCase()
      .replace(
        /[\s_-]/g,
        ''
      )


  const type =
    String(
      variable?.data_type ||
      ''
    )
      .trim()
      .toLowerCase()


  return (
    name === 'date'
    ||
    name === 'datetime'
    ||
    name === 'timestamp'
    ||
    name.endsWith(
      'date'
    )
    ||
    name.endsWith(
      'id'
    )
    ||
    name.includes(
      'trackingnumber'
    )
    ||
    name.includes(
      'address'
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
  ).toFixed(
    digits
  )
}


// ==========================================================
// MAIN COMPONENT
// ==========================================================

export default function ReliabilityAnalysis({
  dataset,
}) {
  const datasetId =
    dataset?.id


  // --------------------------------------------------------
  // VARIABLES
  // --------------------------------------------------------

  const [
    variables,
    setVariables,
  ] = useState([])


  const [
    selectedVariables,
    setSelectedVariables,
  ] = useState([])


  // --------------------------------------------------------
  // OPTIONS
  // --------------------------------------------------------

  const [
    itemTotalThreshold,
    setItemTotalThreshold,
  ] = useState('0.30')


  // --------------------------------------------------------
  // UI STATE
  // --------------------------------------------------------

  const [
    loading,
    setLoading,
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
  // CLEAR RESULT
  // ========================================================

  const clearResult =
    () => {

      setResult(
        null
      )

      setError(
        ''
      )

      setSuccess(
        ''
      )

      setSaved(
        false
      )

      setShowExplanation(
        false
      )

      setShowAPA(
        false
      )
    }


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

          setLoading(
            true
          )

          setVariables(
            []
          )

          setSelectedVariables(
            []
          )

          clearResult()


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

          } catch (
            err
          ) {

            setError(
              getErrorMessage(
                err
              )
            )

          } finally {

            setLoading(
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
  // ELIGIBLE VARIABLES
  // ========================================================

  const eligibleVariables =
    useMemo(
      () =>
        variables.filter(
          (
            variable
          ) =>
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
            &&
            !isExcludedVariable(
              variable
            )
        ),

      [
        variables,
      ]
    )


  // ========================================================
  // TOGGLE VARIABLE
  // ========================================================

  const toggleVariable =
    (
      name
    ) => {

      setSelectedVariables(
        (
          previous
        ) => {

          if (
            previous.includes(
              name
            )
          ) {
            return previous.filter(
              (
                item
              ) =>
                item !==
                name
            )
          }


          return [
            ...previous,
            name,
          ]
        }
      )


      clearResult()
    }


  // ========================================================
  // SELECT ALL
  // ========================================================

  const selectAll =
    () => {

      setSelectedVariables(
        eligibleVariables.map(
          (
            variable
          ) =>
            variable.name
        )
      )


      clearResult()
    }


  // ========================================================
  // CLEAR ALL
  // ========================================================

  const clearAll =
    () => {

      setSelectedVariables(
        []
      )


      clearResult()
    }


  // ========================================================
  // CALCULATE RELIABILITY
  // ========================================================

  const calculate =
    async () => {

      if (
        selectedVariables.length
        <
        2
      ) {
        setError(
          'Select at least two scale items.'
        )

        return
      }


      setCalculating(
        true
      )

      setError(
        ''
      )

      setSuccess(
        ''
      )

      setResult(
        null
      )

      setSaved(
        false
      )

      setShowExplanation(
        false
      )

      setShowAPA(
        false
      )


      try {

        const response =
          await api.post(
            `/statistics/reliability-analysis/${datasetId}`,
            {
              variables:
                selectedVariables,

              alpha:
                0.05,

              item_total_threshold:
                Number(
                  itemTotalThreshold
                ),
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

      setError(
        ''
      )

      setSuccess(
        ''
      )


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
                ?.filename
              ||
              'Dataset',

            method:
              'reliability',

            title:
              'Reliability Analysis',

            configuration:
              result
                .configuration,

            tables:
              result
                .tables,

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
              result
                .apa,

            metadata:
              result
                .metadata,
          }
        )


        setSaved(
          true
        )


        setSuccess(
          'Reliability analysis result saved successfully.'
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
  // NO DATASET
  // ========================================================

  if (
    !datasetId
  ) {
    return (
      <div className="analysis-error">

        Select a dataset before performing
        reliability analysis.

      </div>
    )
  }


  // ========================================================
  // LOADING
  // ========================================================

  if (
    loading
  ) {
    return (

      <div className="analysis-method-loading">

        Loading reliability variables...

      </div>

    )
  }


  const summary =
    result?.summary
    ||
    {}


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <div className="reliability-analysis">


      {/* ==================================================
          CONFIGURATION
          ================================================== */}

      <section className="analysis-configuration">


        <div className="analysis-section-label">

          Reliability Analysis Configuration

        </div>


        {/* INFORMATION */}

        <div className="reliability-information">

          <ShieldCheck
            size={18}
          />


          <div>

            <strong>
              Internal Consistency Reliability
            </strong>


            <p>
              Evaluate whether a set of questionnaire
              or scale items consistently measures
              the same underlying construct.
            </p>

          </div>

        </div>


        {/* SCALE ITEMS */}

        <div className="reliability-item-section">


          <div className="reliability-item-heading">


            <div>

              <h3>
                Scale Items
              </h3>


              <p>
                Select metric or ordinal variables
                belonging to the same scale.
              </p>

            </div>


            <div className="reliability-selection-actions">

              <button
                type="button"

                onClick={
                  selectAll
                }
              >
                Select All
              </button>


              <button
                type="button"

                onClick={
                  clearAll
                }
              >
                Clear
              </button>

            </div>

          </div>


          <div className="analysis-variable-list">

            {
              eligibleVariables.length > 0
                ?
                (

                  eligibleVariables.map(
                    (
                      variable
                    ) => (

                      <label
                        key={
                          variable.name
                        }
                      >

                        <input
                          type="checkbox"

                          checked={
                            selectedVariables.includes(
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
                          {
                            variable.name
                          }
                        </span>

                      </label>

                    )
                  )

                )
                :
                (

                  <span className="analysis-empty-variable-group">

                    No suitable metric or ordinal
                    variables were found.

                  </span>

                )
            }

          </div>

        </div>


        {/* OPTIONS */}

        <div className="reliability-options">


          <div>

            <label>
              Item-Total Review Threshold
            </label>


            <select
              value={
                itemTotalThreshold
              }

              onChange={
                (
                  event
                ) => {

                  setItemTotalThreshold(
                    event
                      .target
                      .value
                  )

                  clearResult()
                }
              }
            >

              <option value="0.20">
                0.20
              </option>

              <option value="0.30">
                0.30
              </option>

              <option value="0.40">
                0.40
              </option>

              <option value="0.50">
                0.50
              </option>

            </select>

          </div>


          <div className="reliability-method-indicator">

            <span>
              Primary Method
            </span>

            <strong>
              Cronbach&apos;s Alpha
            </strong>

          </div>

        </div>


        {/* CURRENT SCALE */}

        <div className="regression-current-model">

          <span>
            Reliability Scale
          </span>


          <strong>

            Cronbach α [

            {
              selectedVariables.length
                ?
                selectedVariables.join(
                  ', '
                )
                :
                'Select scale items'
            }

            ]

          </strong>

        </div>


        {/* CALCULATE BUTTON */}

        <button
          type="button"

          className="analysis-calculate-button"

          disabled={
            calculating
            ||
            selectedVariables.length
            <
            2
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
              'Calculating reliability...'
              :
              'Calculate Reliability'
          }

        </button>

      </section>


      {/* ==================================================
          ERROR
          ================================================== */}

      {error && (

        <div className="analysis-error">

          {error}

        </div>

      )}


      {/* ==================================================
          SUCCESS
          ================================================== */}

      {success && (

        <div className="correlation-success">

          <Check
            size={14}
          />

          {success}

        </div>

      )}


      {/* ==================================================
          RESULTS
          ================================================== */}

      {result && (

        <section className="analysis-results-container">


          {/* RESULT HEADER */}

          <div className="correlation-result-title">


            <div>

              <span>
                RELIABILITY RESULT
              </span>


              <h2>
                Internal Consistency Reliability
              </h2>


              <p>

                Cronbach&apos;s alpha for

                {' '}

                <strong>
                  {
                    summary.items
                  }
                </strong>

                {' '}

                selected scale item(s).

              </p>

            </div>


            {/* RESULT ACTIONS */}

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

          <div className="reliability-summary-grid">


            <div>

              <span>
                Observations
              </span>

              <strong>
                {
                  summary.n
                  ??
                  '—'
                }
              </strong>

            </div>


            <div>

              <span>
                Items
              </span>

              <strong>
                {
                  summary.items
                  ??
                  '—'
                }
              </strong>

            </div>


            <div className="reliability-alpha-card">

              <span>
                Cronbach&apos;s Alpha
              </span>

              <strong>
                {
                  formatNumber(
                    summary
                      .cronbach_alpha,
                    3
                  )
                }
              </strong>

            </div>


            <div>

              <span>
                Standardized Alpha
              </span>

              <strong>
                {
                  formatNumber(
                    summary
                      .standardized_alpha,
                    3
                  )
                }
              </strong>

            </div>


            <div>

              <span>
                Assessment
              </span>

              <strong>
                {
                  summary.assessment
                  ||
                  '—'
                }
              </strong>

            </div>


            <div>

              <span>
                Mean Inter-Item r
              </span>

              <strong>
                {
                  formatNumber(
                    summary
                      .average_inter_item_correlation,
                    3
                  )
                }
              </strong>

            </div>

          </div>


          {/* ==================================================
              RESULT TABLES
              ================================================== */}

          {
            result.tables?.map(
              (
                table,
                index
              ) => (

                <ResultTable
                  key={
                    `${
                      table.title
                    }-${
                      index
                    }`
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
            )
          }


          {/* ==================================================
              INTERPRETATION
              ================================================== */}

          {result.interpretation && (

            <div className="analysis-interpretation">

              <h4>
                Reliability Interpretation
              </h4>


              <p>

                {
                  result
                    .interpretation
                }

              </p>

            </div>

          )}


          {/* ==================================================
              DETAILED EXPLANATION
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

                  Detailed reliability explanation
                  was not returned.

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
