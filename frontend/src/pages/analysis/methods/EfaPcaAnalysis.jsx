import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  Calculator,
  Check,
  FileText,
  Layers3,
  Save,
  Sparkles,
} from 'lucide-react'

import api
  from '../../../api/api'

import ResultTable
  from '../components/ResultTable'

import DetailedExplanation
  from '../components/DetailedExplanation'


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
    'Unable to perform EFA/PCA.'
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
      name:
        item,

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
      String(
        item.measurement_level ||
        item.inferred_measurement_level ||
        'nominal'
      )
        .trim()
        .toLowerCase(),
  }
}


function isExcludedVariable(
  variable
) {
  const name =
    String(
      variable?.name ||
      ''
    )
      .toLowerCase()
      .replace(
        /[\s_-]/g,
        ''
      )


  return (
    name ===
    'date'
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
  )
}


export default function EfaPcaAnalysis({
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
  ] = useState('pca')


  const [
    automaticFactors,
    setAutomaticFactors,
  ] = useState(true)


  const [
    nFactors,
    setNFactors,
  ] = useState('2')


  const [
    rotation,
    setRotation,
  ] = useState('varimax')


  const [
    loadingThreshold,
    setLoadingThreshold,
  ] = useState('0.40')


  const [
    alpha,
    setAlpha,
  ] = useState('0.05')


  const [
    loading,
    setLoading,
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
    success,
    setSuccess,
  ] = useState('')


  const [
    saving,
    setSaving,
  ] = useState(false)


  const [
    saved,
    setSaved,
  ] = useState(false)


  const [
    showExplanation,
    setShowExplanation,
  ] = useState(false)


  const [
    showAPA,
    setShowAPA,
  ] = useState(false)


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


            setVariables(
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


  const toggleVariable =
    (
      name
    ) => {

      setSelectedVariables(
        (
          previous
        ) =>
          previous.includes(
            name
          )
            ?
            previous.filter(
              (
                item
              ) =>
                item !==
                name
            )
            :
            [
              ...previous,
              name,
            ]
      )


      clearResult()
    }


  const calculate =
    async () => {

      if (
        selectedVariables.length
        <
        2
      ) {
        setError(
          'Select at least two numeric variables.'
        )

        return
      }


      setCalculating(
        true
      )

      setError('')
      setSuccess('')
      setResult(null)
      setSaved(false)


      try {

        const response =
          await api.post(
            `/statistics/efa-pca-analysis/${datasetId}`,
            {
              variables:
                selectedVariables,

              method:
                method,

              n_factors:
                automaticFactors
                  ?
                  null
                  :
                  Number(
                    nFactors
                  ),

              rotation:
                rotation,

              alpha:
                Number(
                  alpha
                ),

              loading_threshold:
                Number(
                  loadingThreshold
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
              (
                method ===
                'efa'
                  ?
                  'efa'
                  :
                  'pca'
              ),

            title:
              result
                .analysis_name,

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

            metadata:
              result
                .metadata,
          }
        )


        setSaved(
          true
        )

        setSuccess(
          'EFA/PCA result saved successfully.'
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


  if (
    loading
  ) {
    return (
      <div className="analysis-method-loading">

        Loading variables...

      </div>
    )
  }


  const summary =
    result?.summary
    ||
    {}


  return (
    <div className="efa-pca-analysis">


      <section className="analysis-configuration">


        <div className="analysis-section-label">

          EFA / PCA Configuration

        </div>


        <div className="efa-pca-information">

          <Layers3
            size={18}
          />


          <div>

            <strong>
              Dimension Reduction & Factor Analysis
            </strong>


            <p>
              Use PCA to reduce variables into components
              or EFA to investigate possible latent factors.
            </p>

          </div>

        </div>


        <div className="efa-method-selector">


          <label
            className={
              method ===
              'pca'
                ?
                'active'
                :
                ''
            }
          >

            <input
              type="radio"

              name="efa-method"

              value="pca"

              checked={
                method ===
                'pca'
              }

              onChange={() => {
                setMethod(
                  'pca'
                )

                clearResult()
              }}
            />


            <div>

              <strong>
                PCA
              </strong>

              <span>
                Principal Component Analysis
              </span>

            </div>

          </label>


          <label
            className={
              method ===
              'efa'
                ?
                'active'
                :
                ''
            }
          >

            <input
              type="radio"

              name="efa-method"

              value="efa"

              checked={
                method ===
                'efa'
              }

              onChange={() => {
                setMethod(
                  'efa'
                )

                clearResult()
              }}
            />


            <div>

              <strong>
                EFA
              </strong>

              <span>
                Exploratory Factor Analysis
              </span>

            </div>

          </label>

        </div>


        <div className="efa-variable-section">

          <h3>
            Variables
          </h3>

          <p>
            Select at least two metric or ordinal variables.
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
                    {variable.name}
                  </span>

                </label>

              )
            )}

          </div>

        </div>


        <div className="efa-options-grid">


          <div>

            <label>
              Number of Factors / Components
            </label>


            <select
              value={
                automaticFactors
                  ?
                  'auto'
                  :
                  'manual'
              }

              onChange={
                (
                  event
                ) => {

                  setAutomaticFactors(
                    event
                      .target
                      .value
                    ===
                    'auto'
                  )

                  clearResult()
                }
              }
            >

              <option value="auto">
                Automatic — Kaiser criterion
              </option>

              <option value="manual">
                Manual
              </option>

            </select>

          </div>


          {!automaticFactors && (

            <div>

              <label>
                Number to Retain
              </label>


              <input
                type="number"

                min="1"

                max={
                  Math.max(
                    1,
                    selectedVariables.length
                  )
                }

                value={
                  nFactors
                }

                onChange={
                  (
                    event
                  ) => {

                    setNFactors(
                      event
                        .target
                        .value
                    )

                    clearResult()
                  }
                }
              />

            </div>

          )}


          <div>

            <label>
              Rotation
            </label>


            <select
              value={
                rotation
              }

              onChange={
                (
                  event
                ) => {

                  setRotation(
                    event
                      .target
                      .value
                  )

                  clearResult()
                }
              }
            >

              <option value="none">
                None
              </option>

              <option value="varimax">
                Varimax
              </option>

            </select>

          </div>


          <div>

            <label>
              Loading Threshold
            </label>


            <select
              value={
                loadingThreshold
              }

              onChange={
                (
                  event
                ) => {

                  setLoadingThreshold(
                    event
                      .target
                      .value
                  )

                  clearResult()
                }
              }
            >

              <option value="0.30">
                |0.30|
              </option>

              <option value="0.40">
                |0.40|
              </option>

              <option value="0.50">
                |0.50|
              </option>

              <option value="0.60">
                |0.60|
              </option>

            </select>

          </div>


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

        </div>


        <div className="regression-current-model">

          <span>
            Analysis
          </span>


          <strong>

            {
              method ===
              'efa'
                ?
                'EFA'
                :
                'PCA'
            }

            {' ['}

            {
              selectedVariables.length
                ?
                selectedVariables.join(
                  ', '
                )
                :
                'Select variables'
            }

            {']'}

          </strong>

        </div>


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
              'Calculating...'
              :
              (
                method ===
                'efa'
                  ?
                  'Calculate EFA'
                  :
                  'Calculate PCA'
              )
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


      {result && (

        <section className="analysis-results-container">


          <div className="correlation-result-title">


            <div>

              <span>
                EFA / PCA RESULT
              </span>


              <h2>
                {
                  result
                    .analysis_name
                }
              </h2>


              <p>

                Retained

                {' '}

                <strong>
                  {
                    summary
                      .retained
                  }
                </strong>

                {' '}

                dimensions using

                {' '}

                <strong>
                  {
                    summary
                      .rotation
                  }
                </strong>

                {' '}
                rotation.

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


          <div className="efa-summary-grid">


            <div>

              <span>
                Observations
              </span>

              <strong>
                {
                  summary.n
                }
              </strong>

            </div>


            <div>

              <span>
                Variables
              </span>

              <strong>
                {
                  summary.variables
                }
              </strong>

            </div>


            <div>

              <span>
                KMO
              </span>

              <strong>
                {
                  summary.kmo
                  !==
                  null
                  &&
                  summary.kmo
                  !==
                  undefined
                    ?
                    Number(
                      summary.kmo
                    )
                      .toFixed(
                        3
                      )
                    :
                    '—'
                }
              </strong>

            </div>


            <div>

              <span>
                KMO Assessment
              </span>

              <strong>
                {
                  summary
                    .kmo_assessment
                }
              </strong>

            </div>


            <div>

              <span>
                Retained
              </span>

              <strong>
                {
                  summary.retained
                }
              </strong>

            </div>


            <div>

              <span>
                Suitable
              </span>

              <strong>
                {
                  summary.suitable
                    ?
                    'Yes'
                    :
                    'Review'
                }
              </strong>

            </div>

          </div>


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


          {result.interpretation && (

            <div className="analysis-interpretation">

              <h4>
                EFA / PCA Interpretation
              </h4>


              <p>
                {
                  result
                    .interpretation
                }
              </p>

            </div>

          )}


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

                  Detailed explanation was not returned.

                </div>

              )

          )}


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
