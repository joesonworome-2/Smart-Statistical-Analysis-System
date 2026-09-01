import {
  Download,
  FileSpreadsheet,
  UploadCloud,
  X,
} from 'lucide-react'

import {
  useRef,
  useState,
} from 'react'

import * as XLSX from 'xlsx'


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


export default function DataTransferModal({
  open,
  onClose,
  onImport,
  exportColumns = [],
  exportRows = [],
  datasetName =
    'SSAS-Dataset',
}) {
  const fileInputRef =
    useRef(null)


  const [
    dragging,
    setDragging,
  ] = useState(false)


  const [
    importing,
    setImporting,
  ] = useState(false)


  const [
    error,
    setError,
  ] = useState('')


  if (!open) {
    return null
  }


  // ========================================================
  // READ FILE
  // ========================================================

  const readFile =
    async (file) => {
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
          ![
            'csv',
            'xlsx',
            'xls',
          ].includes(
            extension
          )
        ) {
          throw new Error(
            'Only CSV, XLSX and XLS files are supported.'
          )
        }


        const buffer =
          await file
            .arrayBuffer()


        const workbook =
          XLSX.read(
            buffer,
            {
              type: 'array',
              cellDates: true,
            }
          )


        if (
          !workbook
            .SheetNames
            .length
        ) {
          throw new Error(
            'The selected file does not contain a worksheet.'
          )
        }


        const worksheet =
          workbook.Sheets[
            workbook
              .SheetNames[0]
          ]


        const matrix =
          XLSX.utils
            .sheet_to_json(
              worksheet,
              {
                header: 1,
                defval: '',
                raw: false,
                dateNF:
                  'yyyy-mm-dd',
              }
            )


        const cleaned =
          removeEmptyRows(
            matrix
          )


        if (
          cleaned.length < 2
        ) {
          throw new Error(
            'The file needs a header row and at least one data row.'
          )
        }


        onImport(
          cleaned,
          file.name
        )


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


  // ========================================================
  // INPUT
  // ========================================================

  const handleFileInput =
    (event) => {
      const file =
        event.target
          .files?.[0]


      if (file) {
        readFile(file)
      }


      event.target.value =
        ''
    }


  // ========================================================
  // DROP
  // ========================================================

  const handleDrop =
    (event) => {
      event.preventDefault()

      setDragging(false)


      const file =
        event
          .dataTransfer
          .files?.[0]


      if (file) {
        readFile(file)
      }
    }


  // ========================================================
  // EXPORT MATRIX
  // ========================================================

  const createExportMatrix =
    () => {
      if (
        !exportColumns.length
      ) {
        return []
      }


      return [
        exportColumns,

        ...exportRows,
      ]
    }


  // ========================================================
  // EXCEL EXPORT
  // ========================================================

  const downloadExcel =
    () => {
      setError('')


      const matrix =
        createExportMatrix()


      if (
        matrix.length <= 1
      ) {
        setError(
          'There is no spreadsheet data to export.'
        )

        return
      }


      const worksheet =
        XLSX.utils
          .aoa_to_sheet(
            matrix
          )


      const workbook =
        XLSX.utils
          .book_new()


      XLSX.utils
        .book_append_sheet(
          workbook,
          worksheet,
          'Data'
        )


      XLSX.writeFile(
        workbook,
        `${safeFilename(
          datasetName
        )}.xlsx`
      )
    }


  // ========================================================
  // CSV EXPORT
  // ========================================================

  const downloadCSV =
    () => {
      setError('')


      const matrix =
        createExportMatrix()


      if (
        matrix.length <= 1
      ) {
        setError(
          'There is no spreadsheet data to export.'
        )

        return
      }


      const worksheet =
        XLSX.utils
          .aoa_to_sheet(
            matrix
          )


      const csv =
        XLSX.utils
          .sheet_to_csv(
            worksheet
          )


      const blob =
        new Blob(
          [csv],
          {
            type:
              'text/csv;charset=utf-8;',
          }
        )


      const url =
        URL.createObjectURL(
          blob
        )


      const link =
        document.createElement(
          'a'
        )


      link.href =
        url

      link.download =
        `${safeFilename(
          datasetName
        )}.csv`


      document.body.appendChild(
        link
      )

      link.click()

      document.body.removeChild(
        link
      )

      URL.revokeObjectURL(
        url
      )
    }


  return (
    <div
      className="transfer-modal-overlay"
      onMouseDown={(event) => {
        if (
          event.target ===
            event.currentTarget &&
          !importing
        ) {
          onClose()
        }
      }}
    >

      <div className="transfer-modal">

        <div className="transfer-header">

          <h2>
            Export / Import
          </h2>


          <button
            type="button"
            onClick={onClose}
            disabled={
              importing
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

          <h3>
            Export
          </h3>


          <div className="transfer-line" />


          <div className="transfer-export-actions">

            <button
              type="button"
              onClick={
                downloadExcel
              }
            >
              <FileSpreadsheet
                size={15}
              />

              Download Excel
            </button>


            <button
              type="button"
              onClick={
                downloadCSV
              }
            >
              <Download
                size={15}
              />

              Download CSV
            </button>

          </div>

        </section>


        <section>

          <h3>
            Import
          </h3>


          <div className="transfer-line" />


          <div
            className={
              dragging
                ? 'transfer-drop dragging'
                : 'transfer-drop'
            }

            onDragOver={(event) => {
              event.preventDefault()

              setDragging(
                true
              )
            }}

            onDragLeave={() =>
              setDragging(
                false
              )
            }

            onDrop={
              handleDrop
            }
          >

            <UploadCloud
              size={32}
            />


            <strong>
              Drag and drop file into this field
            </strong>


            <span>
              .xlsx, .xls, .csv
            </span>


            {importing && (
              <small>
                Reading file...
              </small>
            )}

          </div>


          <div className="transfer-or">

            <span />

            <b>
              or
            </b>

            <span />

          </div>


          <div className="transfer-file-row">

            <span>
              Choose file
            </span>


            <button
              type="button"
              disabled={
                importing
              }
              onClick={() =>
                fileInputRef
                  .current
                  ?.click()
              }
            >
              Browse
            </button>


            <input
              ref={
                fileInputRef
              }
              type="file"
              hidden
              accept=".csv,.xlsx,.xls"
              onChange={
                handleFileInput
              }
            />

          </div>

        </section>

      </div>

    </div>
  )
}
