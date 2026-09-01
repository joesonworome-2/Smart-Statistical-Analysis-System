import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  Calculator,
  Check,
  Clock3,
  FileText,
  Info,
  Save,
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
    'Unable to perform survival analysis.'
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
// DATE/TIME VARIABLE CHECK
// ==========================================================

function isDateVariable(
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
    name ===
    'date'
    ||
    name ===
    'datetime'
    ||
    name ===
    'timestamp'
    ||
    name.endsWith(
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
// IDENTIFIER / UNSUITABLE VARIABLE CHECK
// ==========================================================

function isIdentifierVariable(
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


  return (
    name ===
    'id'
    ||
    name ===
    'orderid'
    ||
    name ===
    'customerid'
    ||
    name ===
    'trackingnumber'
    ||
    name ===
    'transactionid'
    ||
    name ===
    'recordid'
    ||
    name ===
    'userid'
    ||
    name.includes(
      'trackingnumber'
    )
    ||
    name.includes(
      'address'
    )
  )
}


// ==========================================================
// SORT UNIQUE EVENT VALUES
// ==========================================================

function sortEventValues(
  values
) {
  return [
    ...values,
  ].sort(
    (
      first,
      second
    ) =>
      String(
        first
      ).localeCompare(
        String(
          second
        ),
        undefined,
        {
          numeric:
            true,

          sensitivity:
            'base',
        }
      )
  )
}


// ==========================================================
// CHOOSE A SENSIBLE DEFAULT EVENT VALUE
// ==========================================================

function chooseDefaultEventValue(
  values
) {
  if (
    !values.length
  ) {
    return ''
  }


  const priorities = [
    '1',
    'yes',
    'true',
    'event',
    'occurred',
    'dead',
    'death',
    'failed',
    'failure',
    'delivered',
    'returned',
    'churned',
  ]


  for (
    const priority
    of priorities
  ) {
    const match =
      values.find(
        (
          value
        ) =>
          String(
            value
          )
            .trim()
            .toLowerCase()
          ===
          priority
      )


    if (
      match !== undefined
    ) {
      return String(
        match
      )
    }
  }


  return String(
    values[
      0
    ]
  )
}


// ==========================================================
// COMPONENT
// ==========================================================

export default function SurvivalAnalysis({
  dataset,
}) {
  const datasetId =
    dataset?.id


  // ========================================================
  // STATE
  // ========================================================

  const [
    variables,
    setVariables,
  ] = useState([])


  const [
    durationVariable,
    setDurationVariable,
  ] = useState('')


  const [
    eventVariable,
    setEventVariable,
  ] = useState('')


  const [
    eventValue,
    setEventValue,
  ] = useState('')


  const [
    eventOptions,
    setEventOptions,
  ] = useState([])


  const [
    loadingEventOptions,
    setLoadingEventOptions,
  ] = useState(false)


  const [
    groupVariable,
    setGroupVariable,
  ] = useState('')


  const [
    alpha,
    setAlpha,
  ] = useState('0.05')


  const [
    confidenceLevel,
    setConfidenceLevel,
  ] = useState('0.95')


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
  // CLEAR CURRENT RESULT
  // ========================================================

  const clearResult =
    () => {
      setResult(
        null
      )

      setSaved(
        false
      )

      setSuccess(
        ''
      )

      setError(
        ''
      )

      setShowExplanation(
        false
      )

      setShowAPA(
        false
      )
    }


  // ========================================================
  // LOAD VARIABLES
  // ========================================================

  useEffect(
    () => {
      if (
        !datasetId
      ) {
        setVariables(
          []
        )

        setDurationVariable(
          ''
        )

        setEventVariable(
          ''
        )

        setEventValue(
          ''
        )

        setEventOptions(
          []
        )

        setGroupVariable(
          ''
        )

        return
      }


      let cancelled =
        false


      const loadVariables =
        async () => {
          setLoading(
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

          setDurationVariable(
            ''
          )

          setEventVariable(
            ''
          )

          setEventValue(
            ''
          )

          setEventOptions(
            []
          )

          setGroupVariable(
            ''
          )

          setSaved(
            false
          )


          try {
            const response =
              await api.get(
                `/datasets/${datasetId}/variables`
              )


            if (
              cancelled
            ) {
              return
            }


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
            if (
              !cancelled
            ) {
              setError(
                getErrorMessage(
                  err
                )
              )
            }

          } finally {
            if (
              !cancelled
            ) {
              setLoading(
                false
              )
            }
          }
        }


      loadVariables()


      return () => {
        cancelled =
          true
      }

    },

    [
      datasetId,
    ]
  )


  // ========================================================
  // AUTOMATICALLY LOAD UNIQUE EVENT VALUES
  // ========================================================

  useEffect(
    () => {
      if (
        !datasetId
        ||
        !eventVariable
      ) {
        setEventOptions(
          []
        )

        setEventValue(
          ''
        )

        return
      }


      let cancelled =
        false


      const loadEventValues =
        async () => {
          setLoadingEventOptions(
            true
          )

          setEventOptions(
            []
          )

          setEventValue(
            ''
          )

          setError(
            ''
          )


          try {
            const uniqueValues =
              new Set()


            let offset =
              0

            const limit =
              5000


            while (
              true
            ) {
              const response =
                await api.get(
                  `/datasets/${datasetId}/data`,
                  {
                    params: {
                      offset:
                        offset,

                      limit:
                        limit,
                    },
                  }
                )


              if (
                cancelled
              ) {
                return
              }


              const payload =
                response.data
                ||
                {}


              const rows =
                payload.rows
                ||
                []


              for (
                const row
                of rows
              ) {
                const value =
                  row?.[
                    eventVariable
                  ]


                if (
                  value === null
                  ||
                  value === undefined
                ) {
                  continue
                }


                const cleaned =
                  String(
                    value
                  ).trim()


                if (
                  cleaned === ''
                ) {
                  continue
                }


                uniqueValues.add(
                  cleaned
                )
              }


              const returned =
                Number(
                  payload.returned_rows
                  ??
                  rows.length
                )


              const hasMore =
                Boolean(
                  payload.has_more
                )


              if (
                returned === 0
                ||
                !hasMore
              ) {
                break
              }


              offset +=
                returned
            }


            if (
              cancelled
            ) {
              return
            }


            const sortedValues =
              sortEventValues(
                Array.from(
                  uniqueValues
                )
              )


            setEventOptions(
              sortedValues
            )


            setEventValue(
              chooseDefaultEventValue(
                sortedValues
              )
            )


            if (
              sortedValues.length
              ===
              0
            ) {
              setError(
                (
                  `No usable values were found in `
                  +
                  `'${eventVariable}'.`
                )
              )
            }

          } catch (
            err
          ) {
            if (
              !cancelled
            ) {
              setEventOptions(
                []
              )

              setEventValue(
                ''
              )

              setError(
                getErrorMessage(
                  err
                )
              )
            }

          } finally {
            if (
              !cancelled
            ) {
              setLoadingEventOptions(
                false
              )
            }
          }
        }


      loadEventValues()


      return () => {
        cancelled =
          true
      }

    },

    [
      datasetId,
      eventVariable,
    ]
  )


  // ========================================================
  // DURATION VARIABLES
  // ========================================================

  const durationVariables =
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
            !isDateVariable(
              variable
            )
            &&
            !isIdentifierVariable(
              variable
            )
        ),

      [
        variables,
      ]
    )


  // ========================================================
  // EVENT INDICATOR VARIABLES
  // ========================================================

  const eventVariables =
    useMemo(
      () =>
        variables.filter(
          (
            variable
          ) =>
            !isDateVariable(
              variable
            )
            &&
            !isIdentifierVariable(
              variable
            )
            &&
            variable.name
            !==
            durationVariable
        ),

      [
        variables,
        durationVariable,
      ]
    )


  // ========================================================
  // GROUP VARIABLES
  // ========================================================

  const groupVariables =
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
              'nominal'
              ||
              variable
                .measurement_level
              ===
              'ordinal'
            )
            &&
            !isDateVariable(
              variable
            )
            &&
            !isIdentifierVariable(
              variable
            )
            &&
            variable.name
            !==
            durationVariable
            &&
            variable.name
            !==
            eventVariable
        ),

      [
        variables,
        durationVariable,
        eventVariable,
      ]
    )


  // ========================================================
  // SELECT DURATION
  // ========================================================

  const selectDuration =
    (
      name
    ) => {
      setDurationVariable(
        name
      )


      if (
        eventVariable
        ===
        name
      ) {
        setEventVariable(
          ''
        )

        setEventValue(
          ''
        )

        setEventOptions(
          []
        )
      }


      if (
        groupVariable
        ===
        name
      ) {
        setGroupVariable(
          ''
        )
      }


      clearResult()
    }


  // ========================================================
  // SELECT EVENT VARIABLE
  // ========================================================

  const selectEventVariable =
    (
      name
    ) => {
      setEventVariable(
        name
      )

      setEventValue(
        ''
      )

      setEventOptions(
        []
      )


      if (
        groupVariable
        ===
        name
      ) {
        setGroupVariable(
          ''
        )
      }


      clearResult()
    }


  // ========================================================
  // SELECT EVENT VALUE
  // ========================================================

  const selectEventValue =
    (
      value
    ) => {
      setEventValue(
        value
      )

      clearResult()
    }


  // ========================================================
  // SELECT GROUP
  // ========================================================

  const selectGroup =
    (
      value
    ) => {
      setGroupVariable(
        value
      )

      clearResult()
    }


  // ========================================================
  // CALCULATE
  // ========================================================

  const calculate =
    async () => {
      if (
        !datasetId
      ) {
        setError(
          'Select a dataset before running survival analysis.'
        )

        return
      }


      if (
        !durationVariable
      ) {
        setError(
          'Select a duration variable.'
        )

        return
      }


      if (
        !eventVariable
      ) {
        setError(
          'Select an event indicator variable.'
        )

        return
      }


      if (
        loadingEventOptions
      ) {
        setError(
          'Wait for the event values to finish loading.'
        )

        return
      }


      if (
        !String(
          eventValue
        ).trim()
      ) {
        setError(
          'Select the value that represents the event.'
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
            `/statistics/survival-analysis/${datasetId}`,
            {
              duration_variable:
                durationVariable,

              event_variable:
                eventVariable,

              event_value:
                String(
                  eventValue
                ),

              group_variable:
                groupVariable
                ||
                null,

              alpha:
                Number(
                  alpha
                ),

              confidence_level:
                Number(
                  confidenceLevel
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
              'survival',

            title:
              'Survival Analysis',

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
          'Survival analysis result saved successfully.'
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
  // LOADING PAGE
  // ========================================================

  if (
    loading
  ) {
    return (
      <div className="analysis-method-loading">

        Loading survival variables...

      </div>
    )
  }


  // ========================================================
  // NO DATASET
  // ========================================================

  if (
    !datasetId
  ) {
    return (
      <div className="analysis-no-dataset">

        <h3>
          Select a dataset
        </h3>

        <p>
          Choose a dataset before configuring
          Survival Analysis.
        </p>

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
    <div className="survival-analysis">


      {/* ==================================================
          CONFIGURATION
          ================================================== */}

      <section className="analysis-configuration">


        <div className="analysis-section-label">

          Survival Analysis Configuration

        </div>


        {/* ==================================================
            INFORMATION
            ================================================== */}

        <div className="survival-information">

          <Clock3
            size={18}
          />


          <div>

            <strong>
              Kaplan-Meier Survival Analysis
            </strong>


            <p>
              Analyse time until an event while
              correctly accounting for censored
              observations.
            </p>

          </div>

        </div>


        {/* ==================================================
            GUIDANCE
            ================================================== */}

        <div className="survival-guidance">

          <Info
            size={15}
          />


          <p>
            The duration variable must represent elapsed
            time such as days, weeks, months, hours or
            years. Do not use a calendar date directly
            as survival duration.
          </p>

        </div>


        {/* ==================================================
            VARIABLE SELECTION
            ================================================== */}

        <div className="survival-variable-layout">


          {/* ==================================================
              DURATION VARIABLE
              ================================================== */}

          <div className="survival-variable-panel">

            <h3>
              Duration Variable
            </h3>


            <p>
              Time until event or censoring.
            </p>


            <div className="analysis-variable-list">

              {durationVariables.length > 0 ? (

                durationVariables.map(
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

                        name="survival-duration"

                        checked={
                          durationVariable
                          ===
                          variable.name
                        }

                        onChange={() =>
                          selectDuration(
                            variable.name
                          )
                        }
                      />


                      <span>
                        {variable.name}
                      </span>

                    </label>

                  )
                )

              ) : (

                <span className="analysis-empty-variable-group">

                  No suitable numeric duration
                  variables found.

                </span>

              )}

            </div>

          </div>


          {/* ==================================================
              EVENT INDICATOR
              ================================================== */}

          <div className="survival-variable-panel">

            <h3>
              Event Indicator
            </h3>


            <p>
              Variable showing whether the event occurred.
            </p>


            <div className="analysis-variable-list">

              {eventVariables.length > 0 ? (

                eventVariables.map(
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

                        name="survival-event"

                        checked={
                          eventVariable
                          ===
                          variable.name
                        }

                        onChange={() =>
                          selectEventVariable(
                            variable.name
                          )
                        }
                      />


                      <span>
                        {variable.name}
                      </span>

                    </label>

                  )
                )

              ) : (

                <span className="analysis-empty-variable-group">

                  No suitable event variables found.

                </span>

              )}

            </div>

          </div>


          {/* ==================================================
              GROUP VARIABLE
              ================================================== */}

          <div className="survival-variable-panel">

            <h3>
              Group Variable
            </h3>


            <p>
              Optional comparison between groups.
            </p>


            <select
              className="survival-group-select"

              value={
                groupVariable
              }

              onChange={
                (
                  event
                ) =>
                  selectGroup(
                    event
                      .target
                      .value
                  )
              }
            >

              <option value="">
                Overall survival only
              </option>


              {groupVariables.map(
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


        {/* ==================================================
            EVENT AND ANALYSIS OPTIONS
            ================================================== */}

        <div className="survival-options">


          {/* ==================================================
              EVENT VALUE — AUTOMATIC DROPDOWN
              ================================================== */}

          <div>

            <label>
              Event Value
            </label>


            <select
              value={
                eventValue
              }

              disabled={
                !eventVariable
                ||
                loadingEventOptions
                ||
                eventOptions.length
                ===
                0
              }

              onChange={
                (
                  event
                ) =>
                  selectEventValue(
                    event
                      .target
                      .value
                  )
              }
            >

              {!eventVariable && (

                <option value="">

                  Select event indicator first

                </option>

              )}


              {eventVariable
                &&
                loadingEventOptions
                && (

                  <option value="">

                    Loading event values...

                  </option>

                )}


              {eventVariable
                &&
                !loadingEventOptions
                &&
                eventOptions.length
                ===
                0
                && (

                  <option value="">

                    No event values found

                  </option>

                )}


              {eventOptions.map(
                (
                  option
                ) => (

                  <option
                    key={
                      option
                    }

                    value={
                      option
                    }
                  >

                    {option}

                  </option>

                )
              )}

            </select>


            {eventVariable
              &&
              !loadingEventOptions
              &&
              eventOptions.length
              >
              0
              && (

                <span className="survival-event-options-note">

                  {
                    eventOptions.length
                  }

                  {' '}

                  unique value

                  {
                    eventOptions.length
                    ===
                    1
                      ?
                      ''
                      :
                      's'
                  }

                  {' '}

                  found in

                  {' '}

                  <strong>
                    {eventVariable}
                  </strong>

                </span>

              )}

          </div>


          {/* ==================================================
              SIGNIFICANCE LEVEL
              ================================================== */}

          <div>

            <label>
              Significance Level
            </label>


            <select
              value={
                alpha
              }

              onChange={
                (
                  event
                ) => {
                  setAlpha(
                    event
                      .target
                      .value
                  )

                  clearResult()
                }
              }
            >

              <option value="0.01">
                α = 0.01
              </option>

              <option value="0.05">
                α = 0.05
              </option>

              <option value="0.10">
                α = 0.10
              </option>

            </select>

          </div>


          {/* ==================================================
              CONFIDENCE LEVEL
              ================================================== */}

          <div>

            <label>
              Confidence Level
            </label>


            <select
              value={
                confidenceLevel
              }

              onChange={
                (
                  event
                ) => {
                  setConfidenceLevel(
                    event
                      .target
                      .value
                  )

                  clearResult()
                }
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


        {/* ==================================================
            CURRENT SURVIVAL MODEL
            ================================================== */}

        <div className="regression-current-model">

          <span>
            Survival Model
          </span>


          <strong>

            Survival(

            {
              durationVariable
              ||
              'Duration'
            }

            ,

            {' '}

            {
              eventVariable
              ||
              'Event'
            }

            =

            {
              eventValue
              ||
              '?'
            }

            )

            {
              groupVariable
                ?
                ` ~ ${groupVariable}`
                :
                ' ~ Overall'
            }

          </strong>

        </div>


        {/* ==================================================
            CALCULATE
            ================================================== */}

        <button
          type="button"

          className="analysis-calculate-button"

          disabled={
            calculating
            ||
            loadingEventOptions
            ||
            !durationVariable
            ||
            !eventVariable
            ||
            !String(
              eventValue
            ).trim()
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
              'Calculating survival...'
              :
              loadingEventOptions
                ?
                'Loading event values...'
                :
                'Calculate Survival Analysis'
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


          {/* ==================================================
              RESULT HEADER
              ================================================== */}

          <div className="correlation-result-title">


            <div>

              <span>
                SURVIVAL RESULT
              </span>


              <h2>
                Kaplan-Meier Survival Analysis
              </h2>


              <p>

                {
                  result
                    .configuration
                    ?.group_variable
                    ?
                    (
                      <>
                        Comparing survival across

                        {' '}

                        <strong>

                          {
                            result
                              .configuration
                              ?.group_variable
                          }

                        </strong>
                      </>
                    )
                    :
                    'Overall survival estimate'
                }

              </p>

            </div>


            {/* ==================================================
                RESULT ACTIONS
                ================================================== */}

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

          <div className="survival-summary-grid">


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
                Events
              </span>


              <strong>

                {
                  summary.events
                  ??
                  '—'
                }

              </strong>

            </div>


            <div>

              <span>
                Censored
              </span>


              <strong>

                {
                  summary.censored
                  ??
                  '—'
                }

              </strong>

            </div>


            <div>

              <span>
                Median Survival
              </span>


              <strong>

                {
                  summary
                    .median_survival
                  ??
                  'Not reached'
                }

              </strong>

            </div>


            <div>

              <span>
                Final Survival
              </span>


              <strong>

                {
                  summary
                    .final_survival_probability
                  !==
                  undefined
                  &&
                  summary
                    .final_survival_probability
                  !==
                  null
                    ?
                    Number(
                      summary
                        .final_survival_probability
                    )
                      .toFixed(
                        4
                      )
                    :
                    '—'
                }

              </strong>

            </div>

          </div>


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
          )}


          {/* ==================================================
              INTERPRETATION
              ================================================== */}

          {result.interpretation && (

            <div className="analysis-interpretation">


              <h4>
                Survival Interpretation
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

                  Detailed survival explanation
                  was not returned by the
                  Statistics Service.

                </div>

              )

          )}


          {/* ==================================================
              APA STYLE RESULT
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
