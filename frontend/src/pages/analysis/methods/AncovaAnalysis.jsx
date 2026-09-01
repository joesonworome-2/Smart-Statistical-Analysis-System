import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  Calculator,
  Check,
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
// ERROR HELPER
// ==========================================================

function errorMessage(
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
    'Unable to perform ANCOVA.'
  )
}


// ==========================================================
// NORMALIZE DATASET VARIABLE
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
// DATE / TIME VARIABLE CHECK
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
    'time'
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
    name.endsWith(
      'time'
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
// IDENTIFIER VARIABLE CHECK
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
    name.endsWith(
      'identifier'
    )
    ||
    name.includes(
      'trackingnumber'
    )
  )
}


// ==========================================================
// ADDRESS / FREE-TEXT VARIABLE CHECK
// ==========================================================

function isAddressVariable(
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
    name.includes(
      'address'
    )
    ||
    name.includes(
      'description'
    )
    ||
    name.includes(
      'comment'
    )
    ||
    name.includes(
      'notes'
    )
  )
}


// ==========================================================
// UNSUITABLE ANCOVA VARIABLE
// ==========================================================

function isExcludedVariable(
  variable
) {
  return (
    isTimeVariable(
      variable
    )
    ||
    isIdentifierVariable(
      variable
    )
    ||
    isAddressVariable(
      variable
    )
  )
}


// ==========================================================
// COMPONENT
// ==========================================================

export default function AncovaAnalysis({
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
    dependentVariable,
    setDependentVariable,
  ] = useState('')


  const [
    factorVariable,
    setFactorVariable,
  ] = useState('')


  const [
    covariates,
    setCovariates,
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
  // RESET RESULT
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
  // LOAD DATASET VARIABLES
  // ========================================================

  useEffect(
    () => {
      if (
        !datasetId
      ) {
        setVariables(
          []
        )

        return
      }


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

          setDependentVariable(
            ''
          )

          setFactorVariable(
            ''
          )

          setCovariates(
            []
          )

          setSaved(
            false
          )


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
              errorMessage(
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
  // DEPENDENT VARIABLES
  //
  // ANCOVA dependent variable should be continuous.
  // Exclude date/time, IDs and free-text fields.
  // ========================================================

  const metricVariables =
    useMemo(
      () =>
        variables.filter(
          (
            variable
          ) =>
            variable
              .measurement_level
            ===
            'metric'
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
  // COVARIATES
  //
  // Covariates can be metric or ordinal.
  // Date/time fields are excluded from standard ANCOVA.
  // ========================================================

  const covariateVariables =
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
  // FACTOR VARIABLES
  //
  // ANCOVA factor must be categorical.
  // Exclude IDs, dates, addresses and free-text.
  // ========================================================

  const nominalVariables =
    useMemo(
      () =>
        variables.filter(
          (
            variable
          ) =>
            variable
              .measurement_level
            ===
            'nominal'
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
  // EXCLUDED VARIABLES FOR INFORMATION DISPLAY
  // ========================================================

  const excludedVariables =
    useMemo(
      () =>
        variables.filter(
          (
            variable
          ) =>
            isExcludedVariable(
              variable
            )
        ),

      [
        variables,
      ]
    )


  // ========================================================
  // SELECT DEPENDENT VARIABLE
  // ========================================================

  const selectDependent =
    (
      name
    ) => {

      setDependentVariable(
        name
      )


      setCovariates(
        (
          previous
        ) =>
          previous.filter(
            (
              item
            ) =>
              item !==
              name
          )
      )


      clearResult()
    }


  // ========================================================
  // SELECT FACTOR
  // ========================================================

  const selectFactor =
    (
      name
    ) => {

      setFactorVariable(
        name
      )


      clearResult()
    }


  // ========================================================
  // TOGGLE COVARIATE
  // ========================================================

  const toggleCovariate =
    (
      name
    ) => {

      if (
        name ===
        dependentVariable
      ) {
        return
      }


      setCovariates(
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
  // CALCULATE ANCOVA
  // ========================================================

  const calculate =
    async () => {

      if (
        !datasetId
      ) {
        setError(
          'Select a dataset before running ANCOVA.'
        )

        return
      }


      if (
        !dependentVariable
      ) {
        setError(
          'Select a continuous dependent variable.'
        )

        return
      }


      if (
        !factorVariable
      ) {
        setError(
          'Select a categorical factor variable.'
        )

        return
      }


      if (
        covariates.length
        ===
        0
      ) {
        setError(
          'Select at least one numeric covariate.'
        )

        return
      }


      if (
        covariates.includes(
          dependentVariable
        )
      ) {
        setError(
          'The dependent variable cannot also be used as a covariate.'
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
            `/statistics/ancova-analysis/${datasetId}`,
            {
              dependent_variable:
                dependentVariable,

              factor_variable:
                factorVariable,

              covariates:
                covariates,

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
          errorMessage(
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
              'ancova',

            title:
              'Analysis of Covariance (ANCOVA)',

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
          'ANCOVA result saved successfully.'
        )

      } catch (
        err
      ) {

        setError(
          errorMessage(
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
    loading
  ) {
    return (

      <div className="analysis-method-loading">

        Loading ANCOVA variables...

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
          Choose a dataset before configuring ANCOVA.
        </p>

      </div>

    )
  }


  // ========================================================
  // MODEL TEXT
  // ========================================================

  const modelText =
    `${
      dependentVariable ||
      'Outcome'
    } ~ ${
      factorVariable ||
      'Factor'
    }${
      covariates.length
        ?
        ` + ${covariates.join(' + ')}`
        :
        ' + Covariate(s)'
    }`


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <div className="ancova-analysis">


      {/* ==================================================
          CONFIGURATION
          ================================================== */}

      <section className="analysis-configuration">


        <div className="analysis-section-label">

          ANCOVA Configuration

        </div>


        {/* ==================================================
            INFORMATION
            ================================================== */}

        <div className="ancova-information">

          <strong>
            Analysis of Covariance
          </strong>

          <p>
            Compare categorical groups while statistically
            controlling for one or more continuous or
            ordinal covariates.
          </p>

        </div>


        {/* ==================================================
            EXCLUDED VARIABLE NOTICE
            ================================================== */}

        {excludedVariables.length > 0 && (

          <div className="ancova-variable-notice">

            <Info
              size={15}
            />


            <div>

              <strong>
                Variable filtering applied
              </strong>


              <p>
                Date/time, identifier, address and free-text
                variables are excluded from standard ANCOVA roles.

                {' '}

                Excluded:

                {' '}

                {
                  excludedVariables
                    .map(
                      (
                        variable
                      ) =>
                        variable.name
                    )
                    .join(
                      ', '
                    )
                }.
              </p>

            </div>

          </div>

        )}


        {/* ==================================================
            VARIABLE PANELS
            ================================================== */}

        <div className="regression-variable-layout">


          {/* ==================================================
              DEPENDENT VARIABLE
              ================================================== */}

          <div className="regression-variable-panel">


            <h3>
              Dependent Variable
            </h3>


            <p>
              Select the continuous outcome variable.
            </p>


            <div className="analysis-variable-list">


              {metricVariables.length > 0 ? (

                metricVariables.map(
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

                        name="ancova-dependent"

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
                )

              ) : (

                <span className="analysis-empty-variable-group">

                  No suitable continuous variables found.

                </span>

              )}

            </div>

          </div>


          {/* ==================================================
              FACTOR VARIABLE
              ================================================== */}

          <div className="regression-variable-panel">


            <h3>
              Factor Variable
            </h3>


            <p>
              Select the categorical grouping variable.
            </p>


            <div className="analysis-variable-list">


              {nominalVariables.length > 0 ? (

                nominalVariables.map(
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

                        name="ancova-factor"

                        checked={
                          factorVariable
                          ===
                          variable.name
                        }

                        onChange={() =>
                          selectFactor(
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

                  No suitable categorical factors found.

                </span>

              )}

            </div>

          </div>


          {/* ==================================================
              COVARIATES
              ================================================== */}

          <div className="regression-variable-panel">


            <h3>
              Covariates
            </h3>


            <p>
              Select numeric variables to statistically control.
            </p>


            <div className="analysis-variable-list">


              {covariateVariables.length > 0 ? (

                covariateVariables.map(
                  (
                    variable
                  ) => {

                    const disabled =
                      variable.name
                      ===
                      dependentVariable


                    return (

                      <label
                        key={
                          variable.name
                        }

                        className={
                          disabled
                            ?
                            'regression-variable-disabled'
                            :
                            ''
                        }
                      >

                        <input
                          type="checkbox"

                          disabled={
                            disabled
                          }

                          checked={
                            covariates.includes(
                              variable.name
                            )
                          }

                          onChange={() =>
                            toggleCovariate(
                              variable.name
                            )
                          }
                        />


                        <span>
                          {variable.name}
                        </span>

                      </label>

                    )
                  }
                )

              ) : (

                <span className="analysis-empty-variable-group">

                  No suitable numeric covariates found.

                </span>

              )}

            </div>

          </div>

        </div>


        {/* ==================================================
            OPTIONS
            ================================================== */}

        <div className="ancova-options">


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
            CURRENT ANCOVA MODEL
            ================================================== */}

        <div className="regression-current-model">


          <span>
            ANCOVA Model
          </span>


          <strong>

            {modelText}

          </strong>

        </div>


        {/* ==================================================
            CALCULATE BUTTON
            ================================================== */}

        <button
          type="button"

          className="analysis-calculate-button"

          disabled={
            calculating
            ||
            !dependentVariable
            ||
            !factorVariable
            ||
            covariates.length === 0
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
              'Calculating ANCOVA...'
              :
              'Calculate ANCOVA'
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
                ANCOVA RESULT
              </span>


              <h2>
                Analysis of Covariance
              </h2>


              <p>

                Adjusted effect of

                {' '}

                <strong>

                  {
                    result
                      .configuration
                      ?.factor_variable
                  }

                </strong>

                {' '}

                on

                {' '}

                <strong>

                  {
                    result
                      .configuration
                      ?.dependent_variable
                  }

                </strong>

                {' '}

                while controlling for

                {' '}

                <strong>

                  {
                    result
                      .configuration
                      ?.covariates
                      ?.join(
                        ', '
                      )
                  }

                </strong>

              </p>

            </div>


            {/* ==================================================
                RESULT TOOLS
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
              RESULT TABLES
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
                ANCOVA Interpretation
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

                  Detailed ANCOVA explanation
                  was not returned by the
                  Statistics Service.

                </div>

              )

          )}


          {/* ==================================================
              APA STYLE
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
