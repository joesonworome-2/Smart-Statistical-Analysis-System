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
  Sparkles,
  Waypoints,
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

  if (typeof detail === 'string') {
    return detail
  }

  if (Array.isArray(detail)) {
    return detail
      .map(
        (item) =>
          item?.msg ||
          String(item)
      )
      .join(', ')
  }

  return (
    error?.message ||
    'Unable to perform cluster analysis.'
  )
}


function normalizeVariable(item) {
  if (typeof item === 'string') {
    return {
      name: item,
      measurement_level: 'nominal',
      data_type: '',
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


function isExcludedVariable(variable) {
  const name =
    String(
      variable?.name || ''
    )
      .toLowerCase()
      .replace(
        /[\s_-]/g,
        ''
      )

  const type =
    String(
      variable?.data_type || ''
    )
      .toLowerCase()

  return (
    name === 'date'
    ||
    name === 'datetime'
    ||
    name === 'timestamp'
    ||
    name.endsWith('date')
    ||
    name.endsWith('id')
    ||
    name.includes(
      'trackingnumber'
    )
    ||
    name.includes('address')
    ||
    type.includes('date')
    ||
    type.includes('time')
  )
}


function formatNumber(
  value,
  digits = 3
) {
  if (
    value === null
    ||
    value === undefined
    ||
    Number.isNaN(
      Number(value)
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


export default function ClusterAnalysis({
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
  ] = useState(
    'kmeans'
  )


  const [
    automaticClusters,
    setAutomaticClusters,
  ] = useState(true)


  const [
    clusterCount,
    setClusterCount,
  ] = useState('3')


  const [
    standardize,
    setStandardize,
  ] = useState(true)


  const [
    maxAutoClusters,
    setMaxAutoClusters,
  ] = useState('8')


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


  const clearResult = () => {
    setResult(null)
    setError('')
    setSuccess('')
    setSaved(false)
    setShowExplanation(false)
    setShowAPA(false)
  }


  useEffect(
    () => {
      if (!datasetId) {
        return
      }

      const loadVariables =
        async () => {
          setLoading(true)

          setVariables([])
          setSelectedVariables([])

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
                  (variable) =>
                    Boolean(
                      variable.name
                    )
                )
            )

          } catch (err) {
            setError(
              getErrorMessage(
                err
              )
            )

          } finally {
            setLoading(false)
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
          (variable) =>
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
    (name) => {
      setSelectedVariables(
        (previous) =>
          previous.includes(name)
            ?
            previous.filter(
              (item) =>
                item !== name
            )
            :
            [
              ...previous,
              name,
            ]
      )

      clearResult()
    }


  const selectAll = () => {
    setSelectedVariables(
      eligibleVariables.map(
        (variable) =>
          variable.name
      )
    )

    clearResult()
  }


  const clearAll = () => {
    setSelectedVariables([])

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

      setCalculating(true)

      setError('')
      setSuccess('')
      setResult(null)
      setSaved(false)
      setShowExplanation(false)
      setShowAPA(false)

      try {
        const response =
          await api.post(
            `/statistics/cluster-analysis/${datasetId}`,
            {
              variables:
                selectedVariables,

              method:
                method,

              n_clusters:
                automaticClusters
                  ?
                  null
                  :
                  Number(
                    clusterCount
                  ),

              standardize:
                standardize,

              max_auto_clusters:
                Number(
                  maxAutoClusters
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
        setCalculating(false)
      }
    }


  const saveResult =
    async () => {
      if (!result) {
        return
      }

      setSaving(true)
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
                ?.filename
              ||
              'Dataset',

            method:
              'cluster',

            title:
              result.title
              ||
              'Cluster Analysis',

            configuration:
              result.configuration,

            tables:
              result.tables,

            interpretation:
              result.interpretation,

            detailed_explanation:
              result.detailed_explanation,

            apa:
              result.apa,

            metadata:
              result.metadata,
          }
        )

        setSaved(true)

        setSuccess(
          'Cluster analysis result saved successfully.'
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


  if (!datasetId) {
    return (
      <div className="analysis-error">
        Select a dataset before performing
        cluster analysis.
      </div>
    )
  }


  if (loading) {
    return (
      <div className="analysis-method-loading">
        Loading cluster variables...
      </div>
    )
  }


  const summary =
    result?.summary || {}


  return (
    <div className="cluster-analysis">


      <section className="analysis-configuration">


        <div className="analysis-section-label">
          Cluster Analysis Configuration
        </div>


        <div className="cluster-information">

          <Waypoints size={18} />

          <div>
            <strong>
              Unsupervised Cluster Analysis
            </strong>

            <p>
              Discover naturally occurring groups
              of observations based on similarities
              across selected numeric variables.
            </p>
          </div>

        </div>


        <div className="cluster-method-selector">


          <label
            className={
              method === 'kmeans'
                ?
                'active'
                :
                ''
            }
          >
            <input
              type="radio"
              name="cluster-method"
              checked={
                method ===
                'kmeans'
              }
              onChange={() => {
                setMethod(
                  'kmeans'
                )

                clearResult()
              }}
            />

            <div>
              <strong>
                K-Means
              </strong>

              <span>
                Partition observations into
                compact clusters.
              </span>
            </div>
          </label>


          <label
            className={
              method ===
              'hierarchical'
                ?
                'active'
                :
                ''
            }
          >
            <input
              type="radio"
              name="cluster-method"
              checked={
                method ===
                'hierarchical'
              }
              onChange={() => {
                setMethod(
                  'hierarchical'
                )

                clearResult()
              }}
            />

            <div>
              <strong>
                Hierarchical
              </strong>

              <span>
                Agglomerative clustering using
                Ward linkage.
              </span>
            </div>
          </label>

        </div>


        <div className="cluster-variable-section">


          <div className="cluster-variable-heading">

            <div>
              <h3>
                Clustering Variables
              </h3>

              <p>
                Select at least two metric or
                ordinal variables.
              </p>
            </div>


            <div className="cluster-selection-actions">

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
              eligibleVariables.length
                ?
                eligibleVariables.map(
                  (variable) => (

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
                )
                :
                (
                  <span className="analysis-empty-variable-group">
                    No suitable numeric variables found.
                  </span>
                )
            }

          </div>

        </div>


        <div className="cluster-options-grid">


          <div>
            <label>
              Number of Clusters
            </label>

            <select
              value={
                automaticClusters
                  ?
                  'auto'
                  :
                  'manual'
              }
              onChange={
                (event) => {
                  setAutomaticClusters(
                    event.target.value
                    ===
                    'auto'
                  )

                  clearResult()
                }
              }
            >
              <option value="auto">
                Automatic — Silhouette
              </option>

              <option value="manual">
                Manual
              </option>
            </select>
          </div>


          {!automaticClusters && (

            <div>
              <label>
                Cluster Count
              </label>

              <input
                type="number"
                min="2"
                max="20"
                value={
                  clusterCount
                }
                onChange={
                  (event) => {
                    setClusterCount(
                      event.target.value
                    )

                    clearResult()
                  }
                }
              />
            </div>

          )}


          {automaticClusters && (

            <div>
              <label>
                Maximum Tested Clusters
              </label>

              <select
                value={
                  maxAutoClusters
                }
                onChange={
                  (event) => {
                    setMaxAutoClusters(
                      event.target.value
                    )

                    clearResult()
                  }
                }
              >
                <option value="5">
                  5
                </option>

                <option value="6">
                  6
                </option>

                <option value="8">
                  8
                </option>

                <option value="10">
                  10
                </option>
              </select>
            </div>

          )}


          <div>
            <label>
              Standardize Variables
            </label>

            <select
              value={
                standardize
                  ?
                  'yes'
                  :
                  'no'
              }
              onChange={
                (event) => {
                  setStandardize(
                    event.target.value
                    ===
                    'yes'
                  )

                  clearResult()
                }
              }
            >
              <option value="yes">
                Yes — Recommended
              </option>

              <option value="no">
                No
              </option>
            </select>
          </div>

        </div>


        <div className="regression-current-model">

          <span>
            Cluster Model
          </span>

          <strong>

            {
              method ===
              'kmeans'
                ?
                'K-Means'
                :
                'Hierarchical'
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
          <Calculator size={16} />

          {
            calculating
              ?
              'Calculating clusters...'
              :
              'Calculate Clusters'
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
          <Check size={14} />
          {success}
        </div>
      )}


      {result && (

        <section className="analysis-results-container">


          <div className="correlation-result-title">


            <div>
              <span>
                CLUSTER ANALYSIS RESULT
              </span>

              <h2>
                {result.title}
              </h2>

              <p>
                SSAS identified{' '}
                <strong>
                  {summary.clusters}
                </strong>{' '}
                clusters with a silhouette score of{' '}
                <strong>
                  {
                    formatNumber(
                      summary
                        .silhouette_score
                    )
                  }
                </strong>.
              </p>
            </div>


            <div className="correlation-result-tools">

              <button
                type="button"
                onClick={() =>
                  setShowExplanation(
                    (previous) =>
                      !previous
                  )
                }
              >
                <Sparkles size={14} />
                Explain
              </button>


              <button
                type="button"
                onClick={() =>
                  setShowAPA(
                    (previous) =>
                      !previous
                  )
                }
              >
                <FileText size={14} />
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
                    <Check size={14} />
                    :
                    <Save size={14} />
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


          <div className="cluster-summary-grid">

            <div>
              <span>
                Observations
              </span>

              <strong>
                {summary.n ?? '—'}
              </strong>
            </div>


            <div>
              <span>
                Variables
              </span>

              <strong>
                {summary.variables ?? '—'}
              </strong>
            </div>


            <div>
              <span>
                Clusters
              </span>

              <strong>
                {summary.clusters ?? '—'}
              </strong>
            </div>


            <div className="cluster-score-card">
              <span>
                Silhouette Score
              </span>

              <strong>
                {
                  formatNumber(
                    summary
                      .silhouette_score
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
                Excluded Cases
              </span>

              <strong>
                {
                  summary.excluded_cases
                  ??
                  '—'
                }
              </strong>
            </div>

          </div>


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
                    }-${index}`
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


          {result.interpretation && (

            <div className="analysis-interpretation">

              <h4>
                Cluster Interpretation
              </h4>

              <p>
                {result.interpretation}
              </p>

            </div>

          )}


          {showExplanation && (

            result.detailed_explanation
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
                  Detailed cluster explanation
                  was not returned.
                </div>
              )

          )}


          {showAPA && result.apa && (

            <div className="analysis-apa-result">

              <div>
                <FileText size={15} />

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
