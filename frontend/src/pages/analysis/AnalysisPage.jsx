import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  useNavigate,
  useSearchParams,
} from 'react-router-dom'

import {
  ArrowRight,
  BarChart3,
  Database,
} from 'lucide-react'

import AppShell from '../../components/AppShell'
import api from '../../api/api'

import DescriptiveAnalysis from './methods/DescriptiveAnalysis'
import HypothesisAnalysis from './methods/HypothesisAnalysis'
import CorrelationAnalysis from './methods/CorrelationAnalysis'
import RegressionAnalysis from './methods/RegressionAnalysis'
import PredictiveAnalysis from './methods/PredictiveAnalysis'
import AncovaAnalysis from './methods/AncovaAnalysis'
import SurvivalAnalysis from './methods/SurvivalAnalysis'
import EfaPcaAnalysis from './methods/EfaPcaAnalysis'
import ReliabilityAnalysis from './methods/ReliabilityAnalysis'
import ClusterAnalysis from './methods/ClusterAnalysis'

import './AnalysisPage.css'

const ANALYSIS_METHODS = [
  { key: 'descriptive', label: 'Descriptive Statistics' },
  { key: 'hypothesis', label: 'Hypothesis Tests' },
  { key: 'correlation', label: 'Correlation' },
  { key: 'regression', label: 'Regression' },
  { key: 'predictive', label: 'Predictive Analytics' },
  { key: 'ancova', label: 'ANCOVA' },
  { key: 'survival', label: 'Survival Analysis' },
  { key: 'factor', label: 'EFA / PCA' },
  { key: 'reliability', label: 'Reliability' },
  { key: 'cluster', label: 'Cluster' },
  { key: 'msa', label: 'MSA' },
  { key: 'capability', label: 'Process Capability' },
  { key: 'spc', label: 'SPC' },
  { key: 'doe', label: 'DoE' },
]

function getErrorMessage(error) {
  const detail = error?.response?.data?.detail

  if (typeof detail === 'string') return detail

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || String(item))
      .join(', ')
  }

  return error?.message || 'Unable to load datasets.'
}

function getValidMethod(method) {
  return ANALYSIS_METHODS.some((item) => item.key === method)
    ? method
    : 'descriptive'
}

export default function AnalysisPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const requestedDatasetId = searchParams.get('datasetId') || ''
  const methodFromUrl = searchParams.get('method') || 'descriptive'
  const selectedRequest = searchParams.get('selected') || ''

  const [datasets, setDatasets] = useState([])
  const [selectedDatasetId, setSelectedDatasetId] = useState(
    requestedDatasetId
  )
  const [activeMethod, setActiveMethod] = useState(
    getValidMethod(methodFromUrl)
  )
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadDatasets = async () => {
      setLoading(true)
      setError('')

      try {
        const response = await api.get('/datasets')
        const loaded = response.data?.datasets || []
        setDatasets(loaded)

        const requestedExists = loaded.some(
          (dataset) => dataset.id === requestedDatasetId
        )

        if (requestedExists) {
          setSelectedDatasetId(requestedDatasetId)
        } else if (loaded.length) {
          setSelectedDatasetId((current) => {
            const currentExists = loaded.some(
              (dataset) => dataset.id === current
            )

            return currentExists ? current : loaded[0].id
          })
        } else {
          setSelectedDatasetId('')
        }
      } catch (err) {
        setError(getErrorMessage(err))
      } finally {
        setLoading(false)
      }
    }

    loadDatasets()
  }, [requestedDatasetId])

  useEffect(() => {
    setActiveMethod(getValidMethod(methodFromUrl))
  }, [methodFromUrl])

  const selectedDataset = useMemo(
    () =>
      datasets.find(
        (dataset) => dataset.id === selectedDatasetId
      ) || null,
    [datasets, selectedDatasetId]
  )

  const currentMethod = useMemo(
    () =>
      ANALYSIS_METHODS.find(
        (method) => method.key === activeMethod
      ) || ANALYSIS_METHODS[0],
    [activeMethod]
  )

  const updateUrl = (datasetIdValue, methodValue) => {
    const params = new URLSearchParams()

    if (datasetIdValue) {
      params.set('datasetId', datasetIdValue)
    }

    params.set('method', methodValue)

    if (selectedRequest) {
      params.set('selected', selectedRequest)
    }

    setSearchParams(params)
  }

  const changeMethod = (methodKey) => {
    const validMethod = getValidMethod(methodKey)
    setActiveMethod(validMethod)
    updateUrl(selectedDatasetId, validMethod)
  }

  const changeDataset = (datasetIdValue) => {
    setSelectedDatasetId(datasetIdValue)
    updateUrl(datasetIdValue, activeMethod)
  }

  const continueToVisualization = () => {
    if (!selectedDatasetId) return

    const params = new URLSearchParams()
    params.set('datasetId', selectedDatasetId)
    params.set('method', activeMethod)

    if (selectedRequest) {
      params.set('selected', selectedRequest)
    }

    navigate(`/visualizations?${params.toString()}`)
  }

  const renderMethod = () => {
    if (!selectedDataset) {
      return (
        <div className="analysis-no-dataset">
          <Database size={34} />
          <h3>A dataset is required</h3>
          <p>
            Return to Datasets and upload, paste, or open a
            dataset before performing statistical analysis.
          </p>

          <button
            type="button"
            className="primary-button"
            onClick={() =>
              navigate(`/datasets?method=${activeMethod}`)
            }
          >
            Choose Dataset
          </button>
        </div>
      )
    }

    if (activeMethod === 'descriptive') {
      return <DescriptiveAnalysis dataset={selectedDataset} />
    }

    if (activeMethod === 'hypothesis') {
      return <HypothesisAnalysis dataset={selectedDataset} />
    }

    if (activeMethod === 'correlation') {
      return <CorrelationAnalysis dataset={selectedDataset} />
    }

    if (activeMethod === 'regression') {
      return <RegressionAnalysis dataset={selectedDataset} />
    }

    if (activeMethod === 'predictive') {
      return <PredictiveAnalysis dataset={selectedDataset} />
    }

    if (activeMethod === 'ancova') {
      return <AncovaAnalysis dataset={selectedDataset} />
    }

    if (activeMethod === 'survival') {
      return <SurvivalAnalysis dataset={selectedDataset} />
    }

    if (activeMethod === 'factor') {
      return <EfaPcaAnalysis dataset={selectedDataset} />
    }

    if (activeMethod === 'reliability') {
      return <ReliabilityAnalysis dataset={selectedDataset} />
    }

    if (activeMethod === 'cluster') {
      return <ClusterAnalysis dataset={selectedDataset} />
    }

    return (
      <div className="analysis-method-placeholder">
        <h2>{currentMethod.label}</h2>
        <p>
          This method is part of the SSAS analysis catalogue but
          its calculation interface has not yet been implemented.
        </p>
        <div className="analysis-method-placeholder-note">
          Select another implemented method to continue.
        </div>
      </div>
    )
  }

  return (
    <AppShell>
      <div className="analysis-page">
        <header className="analysis-page-header">
          <div>
            <span className="analysis-eyebrow">
              STATISTICAL ANALYSIS
            </span>
            <h1>Statistical Analysis</h1>
            <p>
              Run descriptive, inferential and predictive
              analysis using the prepared dataset.
            </p>
          </div>
        </header>

        {error && (
          <div className="analysis-error">
            {error}
          </div>
        )}

        {selectedRequest && (
          <div className="alert success">
            Requested from the calculator:{' '}
            <strong>{selectedRequest}</strong>
          </div>
        )}

        <section className="analysis-dataset-selector">
          <div className="analysis-dataset-icon">
            <Database size={20} />
          </div>

          <div className="analysis-dataset-content">
            <label>Dataset</label>

            <select
              value={selectedDatasetId}
              disabled={loading}
              onChange={(event) =>
                changeDataset(event.target.value)
              }
            >
              {!datasets.length && (
                <option value="">
                  {loading
                    ? 'Loading datasets...'
                    : 'No datasets available'}
                </option>
              )}

              {datasets.map((dataset) => (
                <option
                  key={dataset.id}
                  value={dataset.id}
                >
                  {dataset.original_filename ||
                    dataset.filename ||
                    'Dataset'}
                </option>
              ))}
            </select>

            {selectedDataset && (
              <span className="analysis-dataset-summary">
                {selectedDataset.row_count ?? 0}
                {' rows · '}
                {selectedDataset.column_count ?? 0}
                {' columns'}
              </span>
            )}
          </div>
        </section>

        <nav className="analysis-method-menu">
          {ANALYSIS_METHODS.map((method) => (
            <button
              key={method.key}
              type="button"
              className={
                activeMethod === method.key
                  ? 'active'
                  : ''
              }
              onClick={() => changeMethod(method.key)}
            >
              {method.label}
            </button>
          ))}
        </nav>

        <main className="analysis-workspace">
          <div className="analysis-workspace-title">
            <BarChart3 size={19} />
            <div>
              <span>Analysis Method</span>
              <h2>{currentMethod.label}</h2>
            </div>
          </div>

          {renderMethod()}
        </main>

        {selectedDataset && (
          <section
            className="analysis-workspace"
            style={{
              marginTop: 16,
              display: 'flex',
              justifyContent: 'space-between',
              gap: 12,
              alignItems: 'center',
              flexWrap: 'wrap',
            }}
          >
            <div>
              <strong>Next: Visualization</strong>
              <p style={{ margin: '5px 0 0' }}>
                Review your statistical result, then carry the
                same dataset into the Visualization module.
              </p>
            </div>

            <button
              type="button"
              className="primary-button"
              onClick={continueToVisualization}
            >
              Continue to Visualization
              <ArrowRight size={17} />
            </button>
          </section>
        )}
      </div>
    </AppShell>
  )
}
