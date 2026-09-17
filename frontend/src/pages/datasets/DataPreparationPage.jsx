import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Database,
  RefreshCw,
  Sparkles,
} from 'lucide-react'

import {
  useNavigate,
  useParams,
  useSearchParams,
} from 'react-router-dom'

import api from '../../api/api'
import AppShell from '../../components/AppShell'

function getErrorMessage(error) {
  const detail = error?.response?.data?.detail

  if (typeof detail === 'string') return detail

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || String(item))
      .join(', ')
  }

  return error?.message || 'Unable to prepare dataset.'
}

function badgeStyle(type) {
  if (type === 'warning') {
    return {
      background: '#fff7ed',
      color: '#b54708',
      border: '1px solid #fed7aa',
    }
  }

  if (type === 'success') {
    return {
      background: '#ecfdf3',
      color: '#027a48',
      border: '1px solid #abefc6',
    }
  }

  return {
    background: '#f2f4f7',
    color: '#475467',
    border: '1px solid #eaecf0',
  }
}

export default function DataPreparationPage() {
  const { datasetId } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const requestedMethod =
    searchParams.get('method') || 'descriptive'
  const selectedRequest =
    searchParams.get('selected') || ''

  const [dataset, setDataset] = useState(null)
  const [profile, setProfile] = useState(null)
  const [variables, setVariables] = useState([])
  const [missingData, setMissingData] = useState(null)
  const [outliers, setOutliers] = useState([])
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [removeDuplicates, setRemoveDuplicates] = useState(true)
  const [trimText, setTrimText] = useState(true)
  const [normalizeBlankStrings, setNormalizeBlankStrings] = useState(true)
  const [coerceNumericStrings, setCoerceNumericStrings] = useState(true)
  const [missingStrategy, setMissingStrategy] = useState('keep')
  const [outlierAction, setOutlierAction] = useState('keep')

  const analysisPath = (id) => {
    const params = new URLSearchParams()
    params.set('datasetId', id)
    params.set('method', requestedMethod)

    if (selectedRequest) {
      params.set('selected', selectedRequest)
    }

    return `/analysis?${params.toString()}`
  }

  const datasetsPath = () => {
    const params = new URLSearchParams()
    params.set('method', requestedMethod)

    if (selectedRequest) {
      params.set('selected', selectedRequest)
    }

    return `/datasets?${params.toString()}`
  }

  const loadPreparation = async () => {
    setLoading(true)
    setError('')

    try {
      const [
        datasetResponse,
        profileResponse,
        variableResponse,
        missingResponse,
      ] = await Promise.all([
        api.get(`/datasets/${datasetId}`),
        api.get(`/datasets/${datasetId}/profile`),
        api.get(`/datasets/${datasetId}/variables`),
        api.get(`/datasets/${datasetId}/missing-values`),
      ])

      const loadedVariables =
        variableResponse.data?.variables ||
        profileResponse.data?.variables ||
        []

      setDataset(datasetResponse.data)
      setProfile(profileResponse.data?.profile || null)
      setVariables(loadedVariables)
      setMissingData(missingResponse.data || null)

      const numericVariables = loadedVariables.filter((variable) => {
        const dtype = String(variable?.pandas_dtype || '').toLowerCase()

        return (
          dtype.includes('int') ||
          dtype.includes('float')
        )
      })

      const outlierResults = await Promise.all(
        numericVariables.map(async (variable) => {
          try {
            const response = await api.get(
              `/datasets/${datasetId}/outliers`,
              {
                params: {
                  column: variable.name,
                  method: 'iqr',
                  threshold: 1.5,
                },
              }
            )

            return response.data?.outliers || null
          } catch {
            return null
          }
        })
      )

      setOutliers(
        outlierResults.filter(Boolean)
      )
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPreparation()
  }, [datasetId])

  const issueSummary = useMemo(() => {
    const missing = profile?.total_missing_values || 0
    const duplicates = profile?.duplicate_rows || 0
    const outlierCount = outliers.reduce(
      (total, item) => total + (item?.outlier_count || 0),
      0
    )

    const suspectTypes = variables.filter(
      (variable) =>
        variable.confidence === 'medium' ||
        variable.confidence === 'low'
    ).length

    return {
      missing,
      duplicates,
      outlierCount,
      suspectTypes,
      totalIssues:
        missing + duplicates + outlierCount + suspectTypes,
    }
  }, [profile, variables, outliers])

  const applyPreparationAndContinue = async () => {
    setProcessing(true)
    setError('')
    setSuccess('')

    try {
      const response = await api.post(
        `/datasets/${datasetId}/prepare/workflow`,
        {
          remove_duplicates: removeDuplicates,
          trim_text: trimText,
          normalize_blank_strings: normalizeBlankStrings,
          coerce_numeric_strings: coerceNumericStrings,
          missing_strategy: missingStrategy,
          outlier_action: outlierAction,
        }
      )

      const preparedId =
        response.data?.derived_dataset?.id ||
        response.data?.dataset_id ||
        datasetId

      setSuccess(
        'Data preparation completed. Opening Statistical Analysis...'
      )

      window.setTimeout(() => {
        navigate(analysisPath(preparedId))
      }, 350)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setProcessing(false)
    }
  }

  const continueWithoutChanges = () => {
    navigate(analysisPath(datasetId))
  }

  if (loading) {
    return (
      <AppShell>
        <div className="dataset-empty">
          <div className="loader-circle" />
          <p>Inspecting dataset quality...</p>
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
              PREPARE DATA
            </span>
            <h1>Data Preparation</h1>
            <p>
              SSAS has automatically inspected missing values,
              duplicate rows, variable types and numeric outliers.
              Choose how the detected issues should be handled,
              then continue directly to Analysis.
            </p>
          </div>

          <div
            style={{
              display: 'flex',
              gap: 8,
              flexWrap: 'wrap',
            }}
          >
            <button
              type="button"
              className="secondary-button"
              onClick={() => navigate(datasetsPath())}
            >
              <ArrowLeft size={17} />
              Datasets
            </button>

            <button
              type="button"
              className="secondary-button"
              onClick={loadPreparation}
            >
              <RefreshCw size={17} />
              Re-scan
            </button>
          </div>
        </div>

        {error && <div className="alert error">{error}</div>}
        {success && <div className="alert success">{success}</div>}

        {selectedRequest && (
          <div className="alert success">
            <Sparkles size={16} />
            Selected method: <strong>{selectedRequest}</strong>.
            It will open automatically after preparation.
          </div>
        )}

        <section className="dashboard-panel">
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              justifyContent: 'space-between',
              flexWrap: 'wrap',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}
            >
              <Database size={24} />
              <div>
                <strong>
                  {dataset?.original_filename || dataset?.filename}
                </strong>
                <div style={{ fontSize: 12, marginTop: 3 }}>
                  {profile?.row_count ?? 0} rows ·{' '}
                  {profile?.column_count ?? 0} columns
                </div>
              </div>
            </div>

            <span
              style={{
                ...badgeStyle(
                  issueSummary.totalIssues
                    ? 'warning'
                    : 'success'
                ),
                padding: '7px 10px',
                borderRadius: 999,
                fontWeight: 700,
                fontSize: 12,
              }}
            >
              {issueSummary.totalIssues
                ? `${issueSummary.totalIssues} issue signals detected`
                : 'No obvious quality issues detected'}
            </span>
          </div>
        </section>

        <section
          style={{
            display: 'grid',
            gridTemplateColumns:
              'repeat(auto-fit, minmax(190px, 1fr))',
            gap: 12,
            marginTop: 16,
          }}
        >
          {[
            {
              label: 'Missing values',
              value: issueSummary.missing,
            },
            {
              label: 'Duplicate rows',
              value: issueSummary.duplicates,
            },
            {
              label: 'Outlier flags',
              value: issueSummary.outlierCount,
            },
            {
              label: 'Type/role checks',
              value: issueSummary.suspectTypes,
            },
          ].map((item) => (
            <div
              key={item.label}
              className="dashboard-panel"
            >
              <div style={{ fontSize: 12, color: '#667085' }}>
                {item.label}
              </div>
              <div
                style={{
                  fontSize: 26,
                  fontWeight: 800,
                  marginTop: 6,
                }}
              >
                {item.value}
              </div>
            </div>
          ))}
        </section>

        <section
          className="dashboard-panel"
          style={{ marginTop: 16 }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 9,
              marginBottom: 14,
            }}
          >
            {issueSummary.totalIssues ? (
              <AlertTriangle size={20} />
            ) : (
              <CheckCircle2 size={20} />
            )}
            <div>
              <h2 style={{ margin: 0 }}>
                Automatic preparation options
              </h2>
              <p style={{ margin: '5px 0 0' }}>
                The original dataset is preserved. SSAS creates a
                prepared derived dataset when changes are applied.
              </p>
            </div>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns:
                'repeat(auto-fit, minmax(260px, 1fr))',
              gap: 14,
            }}
          >
            <label
              style={{
                display: 'flex',
                gap: 8,
                alignItems: 'flex-start',
              }}
            >
              <input
                type="checkbox"
                checked={normalizeBlankStrings}
                onChange={(event) =>
                  setNormalizeBlankStrings(event.target.checked)
                }
              />
              <span>
                <strong>Normalize blank cells</strong>
                <br />
                Treat whitespace-only text as missing data.
              </span>
            </label>

            <label
              style={{
                display: 'flex',
                gap: 8,
                alignItems: 'flex-start',
              }}
            >
              <input
                type="checkbox"
                checked={trimText}
                onChange={(event) =>
                  setTrimText(event.target.checked)
                }
              />
              <span>
                <strong>Trim text errors</strong>
                <br />
                Remove accidental spaces before and after text.
              </span>
            </label>

            <label
              style={{
                display: 'flex',
                gap: 8,
                alignItems: 'flex-start',
              }}
            >
              <input
                type="checkbox"
                checked={removeDuplicates}
                onChange={(event) =>
                  setRemoveDuplicates(event.target.checked)
                }
              />
              <span>
                <strong>Remove duplicate rows</strong>
                <br />
                {issueSummary.duplicates} duplicates detected.
              </span>
            </label>

            <label
              style={{
                display: 'flex',
                gap: 8,
                alignItems: 'flex-start',
              }}
            >
              <input
                type="checkbox"
                checked={coerceNumericStrings}
                onChange={(event) =>
                  setCoerceNumericStrings(event.target.checked)
                }
              />
              <span>
                <strong>Correct numeric types</strong>
                <br />
                Convert mostly-numeric text columns to numbers.
              </span>
            </label>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns:
                'repeat(auto-fit, minmax(260px, 1fr))',
              gap: 14,
              marginTop: 18,
            }}
          >
            <label>
              <strong>Missing-value strategy</strong>
              <select
                value={missingStrategy}
                onChange={(event) =>
                  setMissingStrategy(event.target.value)
                }
                style={{
                  display: 'block',
                  width: '100%',
                  marginTop: 6,
                }}
              >
                <option value="keep">
                  Keep missing values for manual/statistical handling
                </option>
                <option value="drop_rows">
                  Remove rows containing missing values
                </option>
                <option value="mean">
                  Mean for numeric + mode for categorical
                </option>
                <option value="median">
                  Median for numeric + mode for categorical
                </option>
                <option value="mode">
                  Mode imputation
                </option>
              </select>
            </label>

            <label>
              <strong>Outlier handling</strong>
              <select
                value={outlierAction}
                onChange={(event) =>
                  setOutlierAction(event.target.value)
                }
                style={{
                  display: 'block',
                  width: '100%',
                  marginTop: 6,
                }}
              >
                <option value="keep">
                  Keep outliers — only flag them
                </option>
                <option value="clip_iqr">
                  Clip numeric outliers to IQR limits
                </option>
                <option value="remove_iqr">
                  Remove rows with IQR outliers
                </option>
              </select>
            </label>
          </div>
        </section>

        <section
          className="dashboard-panel"
          style={{ marginTop: 16 }}
        >
          <h2 style={{ marginTop: 0 }}>
            Variable quality summary
          </h2>

          <div style={{ overflowX: 'auto' }}>
            <table className="dataset-table">
              <thead>
                <tr>
                  <th>Variable</th>
                  <th>Type</th>
                  <th>Measurement</th>
                  <th>Role</th>
                  <th>Missing</th>
                  <th>Unique</th>
                </tr>
              </thead>
              <tbody>
                {variables.map((variable) => (
                  <tr key={variable.name}>
                    <td><strong>{variable.name}</strong></td>
                    <td>{variable.pandas_dtype}</td>
                    <td>{variable.measurement_level}</td>
                    <td>{variable.semantic_role}</td>
                    <td>
                      {variable.missing_count || 0}
                      {' '}
                      ({variable.missing_percent || 0}%)
                    </td>
                    <td>{variable.unique_count ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {missingData?.columns?.some(
            (item) => item.missing_count > 0
          ) && (
            <div style={{ marginTop: 14 }}>
              <strong>Columns with missing values:</strong>{' '}
              {missingData.columns
                .filter((item) => item.missing_count > 0)
                .map((item) =>
                  `${item.column} (${item.missing_count})`
                )
                .join(', ')}
            </div>
          )}

          {outliers.some((item) => item.outlier_count > 0) && (
            <div style={{ marginTop: 10 }}>
              <strong>Numeric outlier flags:</strong>{' '}
              {outliers
                .filter((item) => item.outlier_count > 0)
                .map((item) =>
                  `${item.column} (${item.outlier_count})`
                )
                .join(', ')}
            </div>
          )}
        </section>

        <section
          className="dashboard-panel"
          style={{
            marginTop: 16,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12,
            flexWrap: 'wrap',
          }}
        >
          <div>
            <strong>Next: Statistical Analysis</strong>
            <p style={{ margin: '5px 0 0' }}>
              Your selected dataset and statistical method will
              be carried forward automatically.
            </p>
          </div>

          <div
            style={{
              display: 'flex',
              gap: 8,
              flexWrap: 'wrap',
            }}
          >
            <button
              type="button"
              className="secondary-button"
              onClick={continueWithoutChanges}
              disabled={processing}
            >
              Continue Without Changes
            </button>

            <button
              type="button"
              className="primary-button"
              onClick={applyPreparationAndContinue}
              disabled={processing}
            >
              <Sparkles size={17} />
              {processing
                ? 'Preparing...'
                : 'Prepare & Continue'}
              {!processing && <ArrowRight size={17} />}
            </button>
          </div>
        </section>
      </div>
    </AppShell>
  )
}
