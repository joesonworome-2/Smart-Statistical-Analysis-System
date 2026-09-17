import {
  Download,
  ExternalLink,
  FileSpreadsheet,
  RefreshCw,
  Trash2,
  UploadCloud,
  X,
} from 'lucide-react'

import {
  useEffect,
  useRef,
  useState,
} from 'react'

import {
  useNavigate,
} from 'react-router-dom'

import * as XLSX from 'xlsx'

import api from '../../api/api'


function removeEmptyRows(matrix) {
  return matrix
    .map(
      (row) =>
        Array.isArray(row)
          ? row
          : []
    )
    .filter(
      (row) =>
        row.some(
          (value) =>
            String(
              value ?? ''
            ).trim() !== ''
        )
    )
}


function safeFilename(name) {
  return (
    String(
      name ||
      'SSAS-Dataset'
    )
      .replace(
        /\.[^/.]+$/,
        ''
      )
      .trim() ||
    'SSAS-Dataset'
  )
}


function sortNewestFirst(items) {
  return [
    ...(items || []),
  ].sort(
    (a, b) => {
      const bTime =
        Date.parse(
          b?.created_at ||
          b?.updated_at ||
          ''
        ) || 0

      const aTime =
        Date.parse(
          a?.created_at ||
          a?.updated_at ||
          ''
        ) || 0

      if (bTime !== aTime) {
        return bTime - aTime
      }

      return String(
        b?.id || ''
      ).localeCompare(
        String(
          a?.id || ''
        )
      )
    }
  )
}


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
    'Unable to process saved datasets.'
  )
}


export default function DataTransferModal({
  open,
  onClose,
  onImport,
  exportColumns = [],
  exportRows = [],
  datasetName = 'SSAS-Dataset',
  onDatasetsChanged,
}) {
  const navigate =
    useNavigate()

  const fileInputRef =
    useRef(null)

  const [dragging, setDragging] = useState(false)
  const [importing, setImporting] = useState(false)
  const [error, setError] = useState('')

  const [savedDatasets, setSavedDatasets] = useState([])
  const [loadingSaved, setLoadingSaved] = useState(false)
  const [pendingDeleteId, setPendingDeleteId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)


  const loadSavedDatasets = async () => {
    setLoadingSaved(true)

    try {
      const response = await api.get('/datasets')

      setSavedDatasets(
        sortNewestFirst(
          response.data?.datasets || []
        )
      )
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoadingSaved(false)
    }
  }


  useEffect(() => {
    if (!open) {
      return
    }

    setError('')
    setPendingDeleteId(null)
    loadSavedDatasets()
  }, [open])


  if (!open) {
    return null
  }


  const readFile = async (file) => {
    if (!file) {
      return
    }

    setImporting(true)
    setError('')

    try {
      const extension =
        file.name
          .split('.')
          .pop()
          ?.toLowerCase()

      if (
        !['csv', 'xlsx', 'xls']
          .includes(extension)
      ) {
        throw new Error(
          'Only CSV, XLSX and XLS files are supported.'
        )
      }

      const buffer = await file.arrayBuffer()

      const workbook = XLSX.read(
        buffer,
        {
          type: 'array',
          cellDates: true,
        }
      )

      if (!workbook.SheetNames.length) {
        throw new Error(
          'The selected file does not contain a worksheet.'
        )
      }

      const worksheet =
        workbook.Sheets[
          workbook.SheetNames[0]
        ]

      const matrix =
        XLSX.utils.sheet_to_json(
          worksheet,
          {
            header: 1,
            defval: '',
            raw: false,
            dateNF: 'yyyy-mm-dd',
          }
        )

      const cleaned =
        removeEmptyRows(matrix)

      if (cleaned.length < 2) {
        throw new Error(
          'The file needs a header row and at least one data row.'
        )
      }

      onImport(cleaned, file.name)
      onClose()
    } catch (err) {
      setError(
        err?.message ||
        'Unable to import file.'
      )
    } finally {
      setImporting(false)
    }
  }


  const handleFileInput = (event) => {
    const file = event.target.files?.[0]

    if (file) {
      readFile(file)
    }

    event.target.value = ''
  }


  const handleDrop = (event) => {
    event.preventDefault()
    setDragging(false)

    const file =
      event.dataTransfer.files?.[0]

    if (file) {
      readFile(file)
    }
  }


  const createExportMatrix = () => {
    if (!exportColumns.length) {
      return []
    }

    return [
      exportColumns,
      ...exportRows,
    ]
  }


  const downloadExcel = () => {
    setError('')

    const matrix = createExportMatrix()

    if (matrix.length <= 1) {
      setError(
        'There is no spreadsheet data to export.'
      )
      return
    }

    const worksheet =
      XLSX.utils.aoa_to_sheet(matrix)

    const workbook =
      XLSX.utils.book_new()

    XLSX.utils.book_append_sheet(
      workbook,
      worksheet,
      'Data'
    )

    XLSX.writeFile(
      workbook,
      `${safeFilename(datasetName)}.xlsx`
    )
  }


  const downloadCSV = () => {
    setError('')

    const matrix = createExportMatrix()

    if (matrix.length <= 1) {
      setError(
        'There is no spreadsheet data to export.'
      )
      return
    }

    const worksheet =
      XLSX.utils.aoa_to_sheet(matrix)

    const csv =
      XLSX.utils.sheet_to_csv(worksheet)

    const blob = new Blob(
      [csv],
      {
        type: 'text/csv;charset=utf-8;',
      }
    )

    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')

    link.href = url
    link.download = `${safeFilename(datasetName)}.csv`

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }


  const openSavedDataset = (dataset) => {
    if (!dataset?.id) {
      return
    }

    onClose()
    navigate(
      `/datasets/${dataset.id}/workspace`
    )
  }


  const requestDeleteSavedDataset = async (dataset) => {
    const datasetId = dataset?.id

    if (!datasetId) {
      return
    }

    setError('')

    if (pendingDeleteId !== datasetId) {
      setPendingDeleteId(datasetId)
      return
    }

    setDeletingId(datasetId)

    try {
      await api.delete(
        `/datasets/${encodeURIComponent(datasetId)}`
      )

      setSavedDatasets((previous) =>
        previous.filter(
          (item) =>
            String(item.id) !== String(datasetId)
        )
      )

      setPendingDeleteId(null)

      if (
        typeof onDatasetsChanged === 'function'
      ) {
        await onDatasetsChanged()
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setDeletingId(null)
    }
  }


  return (
    <div
      className="transfer-modal-overlay"
      onMouseDown={(event) => {
        if (
          event.target === event.currentTarget &&
          !importing &&
          deletingId === null
        ) {
          onClose()
        }
      }}
    >
      <div className="transfer-modal">

        <div className="transfer-header">
          <h2>Export / Import</h2>

          <button
            type="button"
            onClick={onClose}
            disabled={
              importing ||
              deletingId !== null
            }
          >
            <X size={19} />
          </button>
        </div>

        {error && (
          <div className="transfer-error">
            {error}
          </div>
        )}

        <section>
          <h3>Import</h3>
          <div className="transfer-line" />

          <div
            className={
              dragging
                ? 'transfer-drop dragging'
                : 'transfer-drop'
            }
            onDragOver={(event) => {
              event.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() =>
              setDragging(false)
            }
            onDrop={handleDrop}
          >
            <UploadCloud size={32} />
            <strong>Upload CSV / Excel</strong>
            <span>.xlsx, .xls, .csv</span>

            {importing && (
              <small>Reading file...</small>
            )}
          </div>

          <div className="transfer-file-row">
            <span>Choose file</span>

            <button
              type="button"
              disabled={importing}
              onClick={() =>
                fileInputRef.current?.click()
              }
            >
              Browse
            </button>

            <input
              ref={fileInputRef}
              type="file"
              hidden
              accept=".csv,.xlsx,.xls"
              onChange={handleFileInput}
            />
          </div>
        </section>

        <section>
          <h3>Export current data</h3>
          <div className="transfer-line" />

          <div className="transfer-export-actions">
            <button
              type="button"
              onClick={downloadExcel}
            >
              <FileSpreadsheet size={15} />
              Download Excel
            </button>

            <button
              type="button"
              onClick={downloadCSV}
            >
              <Download size={15} />
              Download CSV
            </button>
          </div>
        </section>

        <section>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 10,
            }}
          >
            <h3 style={{ margin: 0 }}>
              Saved Datasets
            </h3>

            <button
              type="button"
              onClick={loadSavedDatasets}
              disabled={loadingSaved}
              title="Refresh saved datasets"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 5,
              }}
            >
              <RefreshCw size={14} />
              Refresh
            </button>
          </div>

          <div className="transfer-line" />

          {loadingSaved ? (
            <div
              style={{
                padding: '14px 0',
                color: '#667085',
              }}
            >
              Loading saved datasets...
            </div>
          ) : savedDatasets.length === 0 ? (
            <div
              style={{
                padding: '14px 0',
                color: '#667085',
              }}
            >
              No saved datasets available.
            </div>
          ) : (
            <div
              style={{
                maxHeight: 300,
                overflowY: 'auto',
                border: '1px solid #e4e7ec',
                borderRadius: 8,
              }}
            >
              {savedDatasets.map((dataset) => {
                const pending =
                  pendingDeleteId === dataset.id

                const deleting =
                  deletingId === dataset.id

                return (
                  <div
                    key={dataset.id}
                    style={{
                      display: 'grid',
                      gridTemplateColumns:
                        'minmax(0, 1fr) auto auto auto',
                      alignItems: 'center',
                      gap: 8,
                      padding: '10px 12px',
                      borderBottom: '1px solid #f2f4f7',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        minWidth: 0,
                      }}
                    >
                      <FileSpreadsheet size={16} />

                      <span
                        title={
                          dataset.original_filename ||
                          dataset.filename
                        }
                        style={{
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {dataset.original_filename ||
                          dataset.filename ||
                          'Saved dataset'}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        openSavedDataset(dataset)
                      }
                      disabled={deleting}
                    >
                      <ExternalLink size={13} />
                      Open
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        requestDeleteSavedDataset(dataset)
                      }
                      disabled={deleting}
                      style={{
                        color: pending
                          ? '#ffffff'
                          : '#b42318',
                        background: pending
                          ? '#b42318'
                          : '#ffffff',
                        borderColor: '#f04438',
                        fontWeight: pending
                          ? 700
                          : 500,
                      }}
                    >
                      <Trash2 size={13} />

                      {deleting
                        ? 'Deleting...'
                        : pending
                          ? 'Confirm Delete'
                          : 'Delete'}
                    </button>

                    {pending ? (
                      <button
                        type="button"
                        onClick={() =>
                          setPendingDeleteId(null)
                        }
                        disabled={deleting}
                      >
                        Cancel
                      </button>
                    ) : (
                      <span />
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </section>

      </div>
    </div>
  )
}
