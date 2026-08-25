import { useEffect, useState } from 'react'
import {
  ArrowLeft,
  Database,
  FileSpreadsheet,
  RefreshCw,
  Upload,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import api from '../../api/api'
import AppShell from '../../components/AppShell'

export default function DatasetsPage() {
  const navigate = useNavigate()

  const [datasets, setDatasets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)

  const loadDatasets = async () => {
    setLoading(true)
    setError('')

    try {
      const response = await api.get('/datasets')
      setDatasets(response.data.datasets || [])
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to load datasets.'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDatasets()
  }, [])

  const handleUpload = async (event) => {
    const file = event.target.files?.[0]

    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    setUploading(true)
    setError('')

    try {
      await api.post(
        '/datasets/upload',
        formData
      )

      await loadDatasets()
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Dataset upload failed.'
      )
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  return (
    <AppShell>
<div className="module-page">

      <div className="module-page-header">

        <div>
          <span className="eyebrow dark">
            DATA MANAGEMENT
          </span>

          <h1>Datasets</h1>

          <p>
            Upload and manage datasets used
            throughout SSAS.
          </p>
        </div>

        <button
          className="secondary-button"
          onClick={() => navigate('/dashboard')}
        >
          <ArrowLeft size={17} />
          Dashboard
        </button>

      </div>

      {error && (
        <div className="alert error">
          {error}
        </div>
      )}

      <div className="dataset-page-toolbar">

        <div>
          <strong>
            {datasets.length}
          </strong>{' '}
          dataset
          {datasets.length === 1 ? '' : 's'}
        </div>

        <div className="dataset-page-actions">

          <button
            className="secondary-button"
            onClick={loadDatasets}
            disabled={loading}
          >
            <RefreshCw size={17} />
            Refresh
          </button>

          <label className="upload-button">
            <Upload size={17} />

            {uploading
              ? 'Uploading...'
              : 'Upload Dataset'}

            <input
              type="file"
              hidden
              onChange={handleUpload}
              disabled={uploading}
            />
          </label>

        </div>

      </div>

      <div className="dashboard-panel">

        {loading ? (
          <div className="dataset-empty">
            <div className="loader-circle" />
            <p>Loading datasets...</p>
          </div>
        ) : datasets.length === 0 ? (
          <div className="dataset-empty">
            <Database size={42} />
            <h3>No datasets available</h3>
          </div>
        ) : (
          <div className="dataset-table-wrapper">

            <table className="dataset-table">

              <thead>
                <tr>
                  <th>Dataset</th>
                  <th>Rows</th>
                  <th>Columns</th>
                  <th>Type</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>

                {datasets.map((dataset) => (
                  <tr key={dataset.id}>

                    <td>
                      <div className="dataset-name-button">
                        <FileSpreadsheet size={18} />

                        <strong>
                          {dataset.original_filename}
                        </strong>
                      </div>
                    </td>

                    <td>
                      {dataset.row_count}
                    </td>

                    <td>
                      {dataset.column_count}
                    </td>

                    <td>
                      {dataset.file_type.toUpperCase()}
                    </td>

                    <td>
                      <span className="dataset-status">
                        {dataset.status}
                      </span>
                    </td>

                  </tr>
                ))}

              </tbody>

            </table>

          </div>
        )}

      </div>

    </div>
</AppShell>
  )
}
