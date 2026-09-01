import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle,
  Database,
  Filter,
  RefreshCw,
  Save,
  Settings,
  Sparkles,
} from 'lucide-react'

import {
  useNavigate,
  useParams,
} from 'react-router-dom'

import api from '../../api/api'
import AppShell from '../../components/AppShell'


const tabs = [
  {
    id: 'overview',
    label: 'Overview',
  },
  {
    id: 'variables',
    label: 'Variables',
  },
  {
    id: 'missing',
    label: 'Missing Values',
  },
  {
    id: 'outliers',
    label: 'Outliers',
  },
  {
    id: 'transform',
    label: 'Transform',
  },
  {
    id: 'filter',
    label: 'Filter',
  },
]


function getErrorMessage(
  error,
  fallback
) {
  const detail =
    error.response?.data?.detail

  if (typeof detail === 'string') {
    return detail
  }

  if (Array.isArray(detail)) {
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


export default function DataPreparationPage() {
  const {
    datasetId,
  } = useParams()

  const navigate =
    useNavigate()

  const [dataset, setDataset] =
    useState(null)

  const [profile, setProfile] =
    useState(null)

  const [variables, setVariables] =
    useState([])

  const [
    variableDrafts,
    setVariableDrafts,
  ] = useState({})

  const [missingData, setMissingData] =
    useState(null)

  const [activeTab, setActiveTab] =
    useState('overview')

  const [loading, setLoading] =
    useState(true)

  const [error, setError] =
    useState('')

  const [success, setSuccess] =
    useState('')

  const [
    createdDataset,
    setCreatedDataset,
  ] = useState(null)

  const [
    savingVariable,
    setSavingVariable,
  ] = useState('')

  const [processing, setProcessing] =
    useState(false)


  // ========================================================
  // Missing values
  // ========================================================

  const [
    missingColumn,
    setMissingColumn,
  ] = useState('')

  const [
    missingStrategy,
    setMissingStrategy,
  ] = useState('mode')

  const [
    missingConstant,
    setMissingConstant,
  ] = useState('')


  // ========================================================
  // Outliers
  // ========================================================

  const [
    outlierColumn,
    setOutlierColumn,
  ] = useState('')

  const [
    outlierMethod,
    setOutlierMethod,
  ] = useState('iqr')

  const [
    outlierThreshold,
    setOutlierThreshold,
  ] = useState('1.5')

  const [
    outlierAction,
    setOutlierAction,
  ] = useState('remove')

  const [
    outlierResult,
    setOutlierResult,
  ] = useState(null)


  // ========================================================
  // Transformations
  // ========================================================

  const [
    transformColumn,
    setTransformColumn,
  ] = useState('')

  const [
    transformation,
    setTransformation,
  ] = useState('standardize')

  const [
    transformNewColumn,
    setTransformNewColumn,
  ] = useState('')

  const [
    recodeMapping,
    setRecodeMapping,
  ] = useState('')


  // ========================================================
  // Filtering
  // ========================================================

  const [
    filterColumn,
    setFilterColumn,
  ] = useState('')

  const [
    filterOperator,
    setFilterOperator,
  ] = useState('eq')

  const [
    filterValue,
    setFilterValue,
  ] = useState('')

  const [
    filterValue2,
    setFilterValue2,
  ] = useState('')


  const loadWorkbench = async () => {
    setLoading(true)
    setError('')

    try {
      const [
        datasetResponse,
        profileResponse,
        variablesResponse,
        missingResponse,
      ] = await Promise.all([
        api.get(
          `/datasets/${datasetId}`
        ),

        api.get(
          `/datasets/${datasetId}/profile`
        ),

        api.get(
          `/datasets/${datasetId}/variables`
        ),

        api.get(
          `/datasets/${datasetId}/missing-values`
        ),
      ])

      const datasetData =
        datasetResponse.data

      const profileData =
        profileResponse.data.profile

      const variableData =
        variablesResponse.data.variables ||
        profileResponse.data.variables ||
        []

      setDataset(datasetData)
      setProfile(profileData)
      setVariables(variableData)

      setMissingData(
        missingResponse.data
      )

      const drafts = {}

      variableData.forEach(
        (variable) => {
          drafts[variable.name] = {
            measurement_level:
              variable.measurement_level ||
              'nominal',

            semantic_role:
              variable.semantic_role ||
              'feature',

            exclude_from_recommendations:
              Boolean(
                variable
                  .exclude_from_recommendations
              ),
          }
        }
      )

      setVariableDrafts(drafts)

    } catch (err) {
      setError(
        getErrorMessage(
          err,
          'Unable to load the Data Preparation Workbench.'
        )
      )

    } finally {
      setLoading(false)
    }
  }


  useEffect(() => {
    loadWorkbench()
  }, [datasetId])


  const missingColumns =
    useMemo(
      () =>
        variables.filter(
          (variable) =>
            variable.missing_count > 0
        ),
      [variables]
    )


  const numericVariables =
    useMemo(
      () =>
        variables.filter(
          (variable) => {
            const dtype =
              variable.pandas_dtype ||
              ''

            return (
              (
                dtype.includes('int') ||
                dtype.includes('float')
              )
              &&
              variable.semantic_role !==
                'datetime'
            )
          }
        ),
      [variables]
    )


  useEffect(() => {
    if (
      !missingColumn &&
      missingColumns.length
    ) {
      setMissingColumn(
        missingColumns[0].name
      )
    }

    if (
      !outlierColumn &&
      numericVariables.length
    ) {
      setOutlierColumn(
        numericVariables[0].name
      )
    }

    if (
      !transformColumn &&
      numericVariables.length
    ) {
      setTransformColumn(
        numericVariables[0].name
      )
    }

    if (
      !filterColumn &&
      variables.length
    ) {
      setFilterColumn(
        variables[0].name
      )
    }

  }, [
    missingColumns,
    numericVariables,
    variables,
  ])


  const updateDraft = (
    column,
    field,
    value
  ) => {
    setVariableDrafts(
      (previous) => ({
        ...previous,

        [column]: {
          ...previous[column],
          [field]: value,
        },
      })
    )
  }


  const saveVariableMetadata =
    async (column) => {
      const draft =
        variableDrafts[column]

      if (!draft) return

      setSavingVariable(column)
      setError('')
      setSuccess('')

      try {
        await api.patch(
          `/datasets/${datasetId}/variables/${encodeURIComponent(column)}`,
          draft
        )

        setSuccess(
          `${column} metadata saved successfully.`
        )

        await loadWorkbench()

      } catch (err) {
        setError(
          getErrorMessage(
            err,
            'Unable to update variable metadata.'
          )
        )

      } finally {
        setSavingVariable('')
      }
    }


  const registerDerivedDataset = (
    response
  ) => {
    const derived =
      response.data?.derived_dataset

    if (derived) {
      setCreatedDataset(derived)

      setSuccess(
        response.data?.message ||
        'Prepared dataset created successfully.'
      )
    }
  }


  // ========================================================
  // Missing values
  // ========================================================

  const prepareMissingValues =
    async () => {
      if (!missingColumn) {
        setError(
          'Select a column containing missing values.'
        )

        return
      }

      setProcessing(true)
      setError('')
      setSuccess('')
      setCreatedDataset(null)

      const payload = {
        columns: [
          missingColumn,
        ],

        strategy:
          missingStrategy,
      }

      if (
        missingStrategy ===
        'constant'
      ) {
        payload.fill_value =
          missingConstant
      }

      try {
        const response =
          await api.post(
            `/datasets/${datasetId}/prepare/missing-values`,
            payload
          )

        registerDerivedDataset(
          response
        )

      } catch (err) {
        setError(
          getErrorMessage(
            err,
            'Unable to prepare missing values.'
          )
        )

      } finally {
        setProcessing(false)
      }
    }


  // ========================================================
  // Outliers
  // ========================================================

  const detectOutliers =
    async () => {
      if (!outlierColumn) return

      setProcessing(true)
      setError('')
      setOutlierResult(null)

      try {
        const response =
          await api.get(
            `/datasets/${datasetId}/outliers`,
            {
              params: {
                column:
                  outlierColumn,

                method:
                  outlierMethod,

                threshold:
                  Number(
                    outlierThreshold
                  ),
              },
            }
          )

        setOutlierResult(
          response.data.outliers
        )

      } catch (err) {
        setError(
          getErrorMessage(
            err,
            'Unable to detect outliers.'
          )
        )

      } finally {
        setProcessing(false)
      }
    }


  const prepareOutliers =
    async () => {
      setProcessing(true)
      setError('')
      setSuccess('')
      setCreatedDataset(null)

      try {
        const response =
          await api.post(
            `/datasets/${datasetId}/prepare/outliers`,
            {
              column:
                outlierColumn,

              method:
                outlierMethod,

              action:
                outlierAction,

              threshold:
                Number(
                  outlierThreshold
                ),
            }
          )

        registerDerivedDataset(
          response
        )

      } catch (err) {
        setError(
          getErrorMessage(
            err,
            'Unable to prepare outliers.'
          )
        )

      } finally {
        setProcessing(false)
      }
    }


  // ========================================================
  // Transformations
  // ========================================================

  const prepareTransformation =
    async () => {
      if (!transformColumn) return

      setProcessing(true)
      setError('')
      setSuccess('')
      setCreatedDataset(null)

      try {
        const payload = {
          column:
            transformColumn,

          transformation,

          new_column:
            transformNewColumn.trim()
              ? transformNewColumn.trim()
              : null,
        }

        if (
          transformation ===
          'recode'
        ) {
          if (!recodeMapping.trim()) {
            throw new Error(
              'Enter a JSON mapping for recoding.'
            )
          }

          payload.mapping =
            JSON.parse(
              recodeMapping
            )
        }

        const response =
          await api.post(
            `/datasets/${datasetId}/prepare/transform`,
            payload
          )

        registerDerivedDataset(
          response
        )

      } catch (err) {
        setError(
          getErrorMessage(
            err,
            'Unable to transform dataset.'
          )
        )

      } finally {
        setProcessing(false)
      }
    }


  // ========================================================
  // Filter
  // ========================================================

  const selectedFilterVariable =
    variables.find(
      (variable) =>
        variable.name ===
        filterColumn
    )


  const coerceFilterValue = (
    rawValue
  ) => {
    const dtype =
      selectedFilterVariable
        ?.pandas_dtype ||
      ''

    if (
      dtype.includes('int') ||
      dtype.includes('float')
    ) {
      const number =
        Number(rawValue)

      if (
        !Number.isNaN(number)
      ) {
        return number
      }
    }

    return rawValue
  }


  const prepareFilter =
    async () => {
      if (!filterColumn) return

      setProcessing(true)
      setError('')
      setSuccess('')
      setCreatedDataset(null)

      try {
        let value

        if (
          filterOperator ===
          'in'
        ) {
          value =
            filterValue
              .split(',')
              .map(
                (item) =>
                  coerceFilterValue(
                    item.trim()
                  )
              )
              .filter(
                (item) =>
                  item !== ''
              )

        } else {
          value =
            coerceFilterValue(
              filterValue
            )
        }

        const payload = {
          column:
            filterColumn,

          operator:
            filterOperator,

          value,
        }

        if (
          filterOperator ===
          'between'
        ) {
          payload.value2 =
            coerceFilterValue(
              filterValue2
            )
        }

        const response =
          await api.post(
            `/datasets/${datasetId}/prepare/filter`,
            payload
          )

        registerDerivedDataset(
          response
        )

      } catch (err) {
        setError(
          getErrorMessage(
            err,
            'Unable to filter dataset.'
          )
        )

      } finally {
        setProcessing(false)
      }
    }


  if (loading) {
    return (
      <AppShell>
        <div className="prep-loading">
          <div className="loader-circle" />

          <span>
            Loading Data Preparation
            Workbench...
          </span>
        </div>
      </AppShell>
    )
  }


  return (
    <AppShell>

      <div className="module-page prep-page">

        <div className="module-page-header">

          <div>
            <span className="eyebrow dark">
              SMART DATA PREPARATION
            </span>

            <h1>
              Data Preparation
            </h1>

            <p>
              Clean, classify, transform,
              and prepare your dataset
              without modifying the
              original file.
            </p>
          </div>

          <div className="prep-header-actions">

            <button
              className="secondary-button"
              onClick={loadWorkbench}
            >
              <RefreshCw size={17} />
              Refresh
            </button>

            <button
              className="secondary-button"
              onClick={() =>
                navigate('/datasets')
              }
            >
              <ArrowLeft size={17} />
              Datasets
            </button>

          </div>

        </div>


        {error && (
          <div className="alert error">
            {error}
          </div>
        )}


        {success && (
          <div className="prep-success">

            <CheckCircle size={19} />

            <div>
              <strong>
                Operation completed
              </strong>

              <span>
                {success}
              </span>
            </div>

          </div>
        )}


        {createdDataset && (
          <div className="prep-derived-card">

            <div>
              <span className="prep-derived-label">
                NEW DERIVED DATASET
              </span>

              <strong>
                {
                  createdDataset
                    .original_filename
                }
              </strong>

              <p>
                {
                  createdDataset.row_count
                }{' '}
                rows •{' '}
                {
                  createdDataset.column_count
                }{' '}
                columns
              </p>
            </div>

            <button
              className="prep-primary-button"
              onClick={() =>
                navigate(
                  `/datasets/${createdDataset.id}/prepare`
                )
              }
            >
              Open Prepared Dataset
            </button>

          </div>
        )}


        <section className="prep-dataset-banner">

          <div className="prep-dataset-icon">
            <Database size={23} />
          </div>

          <div className="prep-dataset-info">

            <strong>
              {
                dataset
                  ?.original_filename
              }
            </strong>

            <span>
              {dataset?.row_count || 0}
              {' '}rows •{' '}
              {dataset?.column_count || 0}
              {' '}variables •{' '}
              {dataset?.file_type
                ?.toUpperCase()}
            </span>

          </div>

          <div className="prep-dataset-badges">

            <span className="prep-status-badge">
              {
                dataset?.status ||
                'uploaded'
              }
            </span>

            {(
              dataset?.is_derived ||
              dataset?.status ===
                'prepared'
            ) && (
              <span className="prep-derived-badge">
                Derived Dataset
              </span>
            )}

          </div>

        </section>


        <div className="prep-tabs">

          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={
                activeTab === tab.id
                  ? 'prep-tab active'
                  : 'prep-tab'
              }
              onClick={() =>
                setActiveTab(
                  tab.id
                )
              }
            >
              {tab.label}
            </button>
          ))}

        </div>


        {/* =================================================
            OVERVIEW
        ================================================= */}

        {activeTab === 'overview' && (
          <div className="prep-section">

            <div className="prep-summary-grid">

              <div className="prep-summary-card">
                <span>Rows</span>
                <strong>
                  {profile?.row_count ?? 0}
                </strong>
              </div>

              <div className="prep-summary-card">
                <span>Variables</span>
                <strong>
                  {profile?.column_count ?? 0}
                </strong>
              </div>

              <div className="prep-summary-card warning">
                <span>Missing Values</span>
                <strong>
                  {
                    profile
                      ?.total_missing_values
                    ?? 0
                  }
                </strong>
              </div>

              <div className="prep-summary-card">
                <span>Duplicate Rows</span>
                <strong>
                  {
                    profile
                      ?.duplicate_rows
                    ?? 0
                  }
                </strong>
              </div>

              <div className="prep-summary-card">
                <span>Numeric</span>
                <strong>
                  {
                    profile
                      ?.numeric_columns
                    ?? 0
                  }
                </strong>
              </div>

              <div className="prep-summary-card">
                <span>Date / Time</span>
                <strong>
                  {
                    profile
                      ?.datetime_columns
                    ?? 0
                  }
                </strong>
              </div>

            </div>


            <div className="prep-panel">

              <div className="prep-panel-title">
                <Sparkles size={19} />

                <div>
                  <h3>
                    Smart Data Quality
                  </h3>

                  <p>
                    SSAS automatically
                    examines the structure
                    and quality of the
                    dataset.
                  </p>
                </div>
              </div>


              {(
                profile
                  ?.total_missing_values
                > 0
              ) ? (
                <div className="prep-recommendation warning">

                  <AlertTriangle size={20} />

                  <div>
                    <strong>
                      Missing values detected
                    </strong>

                    <p>
                      This dataset contains{' '}
                      {
                        profile
                          .total_missing_values
                      }{' '}
                      missing values.
                      Review the Missing
                      Values tab before
                      analysis.
                    </p>

                    <button
                      className="prep-link-button"
                      onClick={() =>
                        setActiveTab(
                          'missing'
                        )
                      }
                    >
                      Review Missing Values
                    </button>
                  </div>

                </div>
              ) : (
                <div className="prep-recommendation good">

                  <CheckCircle size={20} />

                  <div>
                    <strong>
                      No missing values
                    </strong>

                    <p>
                      No missing values were
                      detected in this
                      dataset.
                    </p>
                  </div>

                </div>
              )}

            </div>

          </div>
        )}


        {/* =================================================
            VARIABLES
        ================================================= */}

        {activeTab === 'variables' && (
          <div className="prep-section">

            <div className="prep-panel">

              <div className="prep-panel-title">
                <Settings size={19} />

                <div>
                  <h3>
                    Variable Metadata
                  </h3>

                  <p>
                    Review measurement
                    levels and tell SSAS
                    how each variable
                    should be used.
                  </p>
                </div>
              </div>


              <div className="prep-table-wrapper">

                <table className="prep-table">

                  <thead>
                    <tr>
                      <th>Variable</th>
                      <th>Data Type</th>
                      <th>Level</th>
                      <th>Role</th>
                      <th>Missing</th>
                      <th>Exclude</th>
                      <th>Action</th>
                    </tr>
                  </thead>

                  <tbody>

                    {variables.map(
                      (variable) => {
                        const draft =
                          variableDrafts[
                            variable.name
                          ] || {}

                        return (
                          <tr
                            key={
                              variable.name
                            }
                          >

                            <td>
                              <strong>
                                {
                                  variable
                                    .name
                                }
                              </strong>

                              {variable
                                .user_override && (
                                <span className="prep-override-badge">
                                  Manual
                                </span>
                              )}
                            </td>

                            <td>
                              {
                                variable
                                  .pandas_dtype
                              }
                            </td>

                            <td>
                              <select
                                value={
                                  draft
                                    .measurement_level
                                  || 'nominal'
                                }
                                onChange={(
                                  event
                                ) =>
                                  updateDraft(
                                    variable.name,
                                    'measurement_level',
                                    event
                                      .target
                                      .value
                                  )
                                }
                              >
                                <option value="metric">
                                  Metric
                                </option>

                                <option value="ordinal">
                                  Ordinal
                                </option>

                                <option value="nominal">
                                  Nominal
                                </option>
                              </select>
                            </td>

                            <td>
                              <select
                                value={
                                  draft
                                    .semantic_role
                                  || 'feature'
                                }
                                onChange={(
                                  event
                                ) =>
                                  updateDraft(
                                    variable.name,
                                    'semantic_role',
                                    event
                                      .target
                                      .value
                                  )
                                }
                              >
                                <option value="feature">
                                  Feature
                                </option>

                                <option value="outcome">
                                  Outcome
                                </option>

                                <option value="group">
                                  Group
                                </option>

                                <option value="identifier">
                                  Identifier
                                </option>

                                <option value="datetime">
                                  Date / Time
                                </option>

                                <option value="ignored">
                                  Ignored
                                </option>
                              </select>
                            </td>

                            <td>
                              {
                                variable
                                  .missing_count
                              }

                              {variable
                                .missing_count >
                                0 && (
                                <span className="prep-warning-dot">
                                  ⚠
                                </span>
                              )}
                            </td>

                            <td>
                              <input
                                type="checkbox"
                                checked={
                                  Boolean(
                                    draft
                                      .exclude_from_recommendations
                                  )
                                }
                                onChange={(
                                  event
                                ) =>
                                  updateDraft(
                                    variable.name,
                                    'exclude_from_recommendations',
                                    event
                                      .target
                                      .checked
                                  )
                                }
                              />
                            </td>

                            <td>
                              <button
                                className="prep-small-button"
                                disabled={
                                  savingVariable ===
                                  variable.name
                                }
                                onClick={() =>
                                  saveVariableMetadata(
                                    variable.name
                                  )
                                }
                              >
                                <Save size={14} />

                                {savingVariable ===
                                variable.name
                                  ? 'Saving...'
                                  : 'Save'}
                              </button>
                            </td>

                          </tr>
                        )
                      }
                    )}

                  </tbody>

                </table>

              </div>

            </div>

          </div>
        )}


        {/* =================================================
            MISSING VALUES
        ================================================= */}

        {activeTab === 'missing' && (
          <div className="prep-section">

            <div className="prep-panel">

              <h3>
                Missing Value Treatment
              </h3>

              <p className="prep-muted">
                Treatment creates a new
                derived dataset. Your
                original file remains
                unchanged.
              </p>


              {missingColumns.length ===
              0 ? (
                <div className="prep-recommendation good">
                  <CheckCircle size={20} />

                  <div>
                    <strong>
                      No missing values
                    </strong>

                    <p>
                      This dataset currently
                      has no missing values.
                    </p>
                  </div>
                </div>
              ) : (
                <>

                  <div className="prep-form-grid">

                    <label>
                      Column

                      <select
                        value={
                          missingColumn
                        }
                        onChange={(
                          event
                        ) =>
                          setMissingColumn(
                            event
                              .target
                              .value
                          )
                        }
                      >
                        {missingColumns.map(
                          (variable) => (
                            <option
                              key={
                                variable.name
                              }
                              value={
                                variable.name
                              }
                            >
                              {
                                variable.name
                              }
                              {' — '}
                              {
                                variable
                                  .missing_count
                              }{' '}
                              missing
                            </option>
                          )
                        )}
                      </select>
                    </label>


                    <label>
                      Treatment

                      <select
                        value={
                          missingStrategy
                        }
                        onChange={(
                          event
                        ) =>
                          setMissingStrategy(
                            event
                              .target
                              .value
                          )
                        }
                      >
                        <option value="mode">
                          Replace with Mode
                        </option>

                        <option value="mean">
                          Replace with Mean
                        </option>

                        <option value="median">
                          Replace with Median
                        </option>

                        <option value="constant">
                          Replace with Constant
                        </option>

                        <option value="drop_rows">
                          Drop Affected Rows
                        </option>
                      </select>
                    </label>


                    {missingStrategy ===
                      'constant' && (
                      <label>
                        Replacement Value

                        <input
                          value={
                            missingConstant
                          }
                          onChange={(
                            event
                          ) =>
                            setMissingConstant(
                              event
                                .target
                                .value
                            )
                          }
                          placeholder="e.g. Unknown"
                        />
                      </label>
                    )}

                  </div>


                  <button
                    className="prep-primary-button"
                    disabled={processing}
                    onClick={
                      prepareMissingValues
                    }
                  >
                    <Sparkles size={16} />

                    {processing
                      ? 'Processing...'
                      : 'Create Prepared Dataset'}
                  </button>

                </>
              )}

            </div>


            <div className="prep-panel">

              <h3>
                Missing Value Summary
              </h3>

              <div className="prep-table-wrapper">

                <table className="prep-table">

                  <thead>
                    <tr>
                      <th>Column</th>
                      <th>Missing</th>
                      <th>Missing %</th>
                      <th>Available</th>
                    </tr>
                  </thead>

                  <tbody>
                    {(
                      missingData?.columns ||
                      []
                    ).map(
                      (item) => (
                        <tr
                          key={
                            item.column
                          }
                        >
                          <td>
                            <strong>
                              {
                                item.column
                              }
                            </strong>
                          </td>

                          <td>
                            {
                              item
                                .missing_count
                            }
                          </td>

                          <td>
                            {
                              item
                                .missing_percent
                            }%
                          </td>

                          <td>
                            {
                              item
                                .non_missing_count
                            }
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>

                </table>

              </div>

            </div>

          </div>
        )}


        {/* =================================================
            OUTLIERS
        ================================================= */}

        {activeTab === 'outliers' && (
          <div className="prep-section">

            <div className="prep-panel">

              <h3>
                Outlier Detection
              </h3>

              <p className="prep-muted">
                Detect unusual numeric
                observations before deciding
                whether they should be
                changed.
              </p>


              <div className="prep-form-grid">

                <label>
                  Numeric Variable

                  <select
                    value={
                      outlierColumn
                    }
                    onChange={(
                      event
                    ) => {
                      setOutlierColumn(
                        event
                          .target
                          .value
                      )

                      setOutlierResult(
                        null
                      )
                    }}
                  >
                    {numericVariables.map(
                      (variable) => (
                        <option
                          key={
                            variable.name
                          }
                          value={
                            variable.name
                          }
                        >
                          {
                            variable.name
                          }
                        </option>
                      )
                    )}
                  </select>
                </label>


                <label>
                  Method

                  <select
                    value={
                      outlierMethod
                    }
                    onChange={(
                      event
                    ) =>
                      setOutlierMethod(
                        event
                          .target
                          .value
                      )
                    }
                  >
                    <option value="iqr">
                      IQR
                    </option>

                    <option value="zscore">
                      Z-Score
                    </option>
                  </select>
                </label>


                <label>
                  Threshold

                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    value={
                      outlierThreshold
                    }
                    onChange={(
                      event
                    ) =>
                      setOutlierThreshold(
                        event
                          .target
                          .value
                      )
                    }
                  />
                </label>

              </div>


              <button
                className="secondary-button"
                disabled={processing}
                onClick={detectOutliers}
              >
                Detect Outliers
              </button>


              {outlierResult && (
                <div className="prep-outlier-result">

                  <div>
                    <span>
                      Outliers
                    </span>

                    <strong>
                      {
                        outlierResult
                          .outlier_count
                      }
                    </strong>
                  </div>

                  <div>
                    <span>
                      Percentage
                    </span>

                    <strong>
                      {
                        outlierResult
                          .outlier_percent
                      }%
                    </strong>
                  </div>

                  <div>
                    <span>
                      Lower Bound
                    </span>

                    <strong>
                      {
                        outlierResult
                          .lower_bound
                      }
                    </strong>
                  </div>

                  <div>
                    <span>
                      Upper Bound
                    </span>

                    <strong>
                      {
                        outlierResult
                          .upper_bound
                      }
                    </strong>
                  </div>

                </div>
              )}

            </div>


            {outlierResult && (
              <div className="prep-panel">

                <h3>
                  Prepare Outliers
                </h3>

                <div className="prep-form-grid">

                  <label>
                    Action

                    <select
                      value={
                        outlierAction
                      }
                      onChange={(
                        event
                      ) =>
                        setOutlierAction(
                          event
                            .target
                            .value
                        )
                      }
                    >
                      <option value="remove">
                        Remove Outlier Rows
                      </option>

                      <option value="clip">
                        Clip to Bounds
                      </option>
                    </select>
                  </label>

                </div>

                <button
                  className="prep-primary-button"
                  disabled={processing}
                  onClick={
                    prepareOutliers
                  }
                >
                  Create Prepared Dataset
                </button>

              </div>
            )}

          </div>
        )}


        {/* =================================================
            TRANSFORM
        ================================================= */}

        {activeTab === 'transform' && (
          <div className="prep-section">

            <div className="prep-panel">

              <h3>
                Variable Transformation
              </h3>

              <p className="prep-muted">
                A transformed variable is
                written to a new derived
                dataset.
              </p>


              <div className="prep-form-grid">

                <label>
                  Variable

                  <select
                    value={
                      transformColumn
                    }
                    onChange={(
                      event
                    ) =>
                      setTransformColumn(
                        event
                          .target
                          .value
                      )
                    }
                  >
                    {variables.map(
                      (variable) => (
                        <option
                          key={
                            variable.name
                          }
                          value={
                            variable.name
                          }
                        >
                          {
                            variable.name
                          }
                        </option>
                      )
                    )}
                  </select>
                </label>


                <label>
                  Transformation

                  <select
                    value={
                      transformation
                    }
                    onChange={(
                      event
                    ) =>
                      setTransformation(
                        event
                          .target
                          .value
                      )
                    }
                  >
                    <option value="standardize">
                      Standardize (Z-score)
                    </option>

                    <option value="normalize">
                      Normalize (0–1)
                    </option>

                    <option value="log1p">
                      Log Transform
                    </option>

                    <option value="recode">
                      Recode Categories
                    </option>
                  </select>
                </label>


                <label>
                  New Column Name

                  <input
                    value={
                      transformNewColumn
                    }
                    onChange={(
                      event
                    ) =>
                      setTransformNewColumn(
                        event
                          .target
                          .value
                      )
                    }
                    placeholder="Optional"
                  />
                </label>

              </div>


              {transformation ===
                'recode' && (
                <label className="prep-full-field">
                  Recode Mapping (JSON)

                  <textarea
                    rows="6"
                    value={
                      recodeMapping
                    }
                    onChange={(
                      event
                    ) =>
                      setRecodeMapping(
                        event
                          .target
                          .value
                      )
                    }
                    placeholder={`{
  "Yes": 1,
  "No": 0
}`}
                  />
                </label>
              )}


              <button
                className="prep-primary-button"
                disabled={processing}
                onClick={
                  prepareTransformation
                }
              >
                Create Transformed Dataset
              </button>

            </div>

          </div>
        )}


        {/* =================================================
            FILTER
        ================================================= */}

        {activeTab === 'filter' && (
          <div className="prep-section">

            <div className="prep-panel">

              <div className="prep-panel-title">
                <Filter size={19} />

                <div>
                  <h3>
                    Dataset Filter
                  </h3>

                  <p>
                    Keep only records
                    satisfying a selected
                    condition.
                  </p>
                </div>
              </div>


              <div className="prep-form-grid">

                <label>
                  Variable

                  <select
                    value={
                      filterColumn
                    }
                    onChange={(
                      event
                    ) =>
                      setFilterColumn(
                        event
                          .target
                          .value
                      )
                    }
                  >
                    {variables.map(
                      (variable) => (
                        <option
                          key={
                            variable.name
                          }
                          value={
                            variable.name
                          }
                        >
                          {
                            variable.name
                          }
                        </option>
                      )
                    )}
                  </select>
                </label>


                <label>
                  Operator

                  <select
                    value={
                      filterOperator
                    }
                    onChange={(
                      event
                    ) =>
                      setFilterOperator(
                        event
                          .target
                          .value
                      )
                    }
                  >
                    <option value="eq">
                      Equal To
                    </option>

                    <option value="ne">
                      Not Equal To
                    </option>

                    <option value="gt">
                      Greater Than
                    </option>

                    <option value="gte">
                      Greater Than or Equal
                    </option>

                    <option value="lt">
                      Less Than
                    </option>

                    <option value="lte">
                      Less Than or Equal
                    </option>

                    <option value="in">
                      In List
                    </option>

                    <option value="contains">
                      Contains
                    </option>

                    <option value="between">
                      Between
                    </option>
                  </select>
                </label>


                <label>
                  Value

                  <input
                    value={
                      filterValue
                    }
                    onChange={(
                      event
                    ) =>
                      setFilterValue(
                        event
                          .target
                          .value
                      )
                    }
                    placeholder={
                      filterOperator ===
                      'in'
                        ? 'East, West, North'
                        : 'Enter value'
                    }
                  />
                </label>


                {filterOperator ===
                  'between' && (
                  <label>
                    Second Value

                    <input
                      value={
                        filterValue2
                      }
                      onChange={(
                        event
                      ) =>
                        setFilterValue2(
                          event
                            .target
                            .value
                        )
                      }
                    />
                  </label>
                )}

              </div>


              <button
                className="prep-primary-button"
                disabled={processing}
                onClick={
                  prepareFilter
                }
              >
                Create Filtered Dataset
              </button>

            </div>

          </div>
        )}

      </div>

    </AppShell>
  )
}
