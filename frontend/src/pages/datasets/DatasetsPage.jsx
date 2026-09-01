import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'

import {
  ChevronLeft,
  ChevronRight,
  Download,
  ExternalLink,
  FileSpreadsheet,
  Plus,
  RefreshCw,
  Save,
  Sparkles,
  Trash2,
} from 'lucide-react'

import {
  useNavigate,
} from 'react-router-dom'

import api from '../../api/api'
import AppShell from '../../components/AppShell'
import DataTransferModal from './DataTransferModal'

import './DatasetsPage.css'


// ==========================================================
// CONFIGURATION
// ==========================================================

const DEFAULT_COLUMN_COUNT = 8
const DEFAULT_ROW_COUNT = 14

/*
 * Only 100 rows are rendered at once.
 *
 * The complete imported dataset remains
 * stored in sheetRows.
 */
const PAGE_SIZE = 100


// ==========================================================
// ERROR HELPER
// ==========================================================

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
    'Something went wrong.'
  )
}


// ==========================================================
// CSV EXPORT HELPER
// ==========================================================

function escapeCSV(value) {
  const text =
    value === null ||
    value === undefined
      ? ''
      : String(value)

  if (
    text.includes(',') ||
    text.includes('"') ||
    text.includes('\n')
  ) {
    return `"${text.replace(
      /"/g,
      '""'
    )}"`
  }

  return text
}


// ==========================================================
// CSV LINE PARSER
// ==========================================================

function parseCSVLine(
  line,
  delimiter = ','
) {
  const values = []

  let current = ''
  let insideQuotes = false


  for (
    let index = 0;
    index < line.length;
    index += 1
  ) {
    const character =
      line[index]


    if (
      character === '"'
    ) {
      if (
        insideQuotes &&
        line[index + 1] === '"'
      ) {
        current += '"'

        index += 1

      } else {
        insideQuotes =
          !insideQuotes
      }

      continue
    }


    if (
      character === delimiter &&
      !insideQuotes
    ) {
      values.push(
        current
      )

      current = ''

      continue
    }


    current += character
  }


  values.push(
    current
  )

  return values
}


// ==========================================================
// EXCEL / CSV CLIPBOARD PARSER
// ==========================================================

function parseClipboardData(text) {
  const cleaned =
    String(
      text ?? ''
    )
      .replace(
        /\r\n/g,
        '\n'
      )
      .replace(
        /\r/g,
        '\n'
      )


  if (
    !cleaned.trim()
  ) {
    return []
  }


  const lines =
    cleaned.split('\n')


  /*
   * Remove blank lines from the end.
   */
  while (
    lines.length &&
    lines[
      lines.length - 1
    ].trim() === ''
  ) {
    lines.pop()
  }


  const delimiter =
    cleaned.includes('\t')
      ? '\t'
      : ','


  return lines.map(
    (line) => {
      if (
        delimiter === '\t'
      ) {
        return line
          .split('\t')
          .map(
            (value) =>
              value.trim()
          )
      }


      return parseCSVLine(
        line,
        ','
      ).map(
        (value) =>
          value.trim()
      )
    }
  )
}


// ==========================================================
// MEASUREMENT LEVEL AUTO-DETECTION
// ==========================================================

function detectMeasurementLevel(values) {
  const cleanValues =
    values
      .map(
        (value) =>
          String(
            value ?? ''
          ).trim()
      )
      .filter(Boolean)


  if (
    !cleanValues.length
  ) {
    return 'nominal'
  }


  // --------------------------------------------------------
  // ORDINAL VALUES
  // --------------------------------------------------------

  const ordinalTerms =
    new Set([
      'very low',
      'low',
      'medium',
      'high',
      'very high',

      'poor',
      'fair',
      'good',
      'very good',
      'excellent',

      'strongly disagree',
      'disagree',
      'neutral',
      'agree',
      'strongly agree',

      'beginner',
      'intermediate',
      'advanced',

      'primary',
      'secondary',
      'tertiary',

      'freshman',
      'sophomore',
      'junior',
      'senior',
    ])


  const normalized =
    cleanValues.map(
      (value) =>
        value.toLowerCase()
    )


  const ordinal =
    normalized.every(
      (value) =>
        ordinalTerms.has(
          value
        )
    )


  if (ordinal) {
    return 'ordinal'
  }


  // --------------------------------------------------------
  // DATE VALUES
  // --------------------------------------------------------

  const datePattern =
    /^(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})$/


  const dateCount =
    cleanValues.filter(
      (value) =>
        datePattern.test(
          value
        )
    ).length


  if (
    dateCount /
      cleanValues.length >=
    0.8
  ) {
    return 'metric'
  }


  // --------------------------------------------------------
  // TIME VALUES
  // --------------------------------------------------------

  const timePattern =
    /^([01]?\d|2[0-3]):[0-5]\d(:[0-5]\d)?$/


  const timeCount =
    cleanValues.filter(
      (value) =>
        timePattern.test(
          value
        )
    ).length


  if (
    timeCount /
      cleanValues.length >=
    0.8
  ) {
    return 'metric'
  }


  // --------------------------------------------------------
  // NUMERIC
  // --------------------------------------------------------

  const numeric =
    cleanValues.every(
      (value) =>
        value !== '' &&
        !Number.isNaN(
          Number(value)
        )
    )


  if (numeric) {
    const uniqueCount =
      new Set(
        cleanValues
      ).size


    /*
     * Binary 0/1 variables should
     * normally be treated as nominal.
     */
    if (
      uniqueCount <= 2
    ) {
      return 'nominal'
    }


    return 'metric'
  }


  return 'nominal'
}


// ==========================================================
// CREATE EMPTY ROWS
// ==========================================================

function createEmptyRows(
  rowCount,
  columnCount
) {
  return Array.from(
    {
      length:
        rowCount,
    },
    () =>
      Array(
        columnCount
      ).fill('')
  )
}


// ==========================================================
// DATASETS PAGE
// ==========================================================

export default function DatasetsPage() {
  const navigate =
    useNavigate()


  const sheetRef =
    useRef(null)


  // ========================================================
  // SAVED DATASETS
  // ========================================================

  const [
    datasets,
    setDatasets,
  ] = useState([])


  const [
    loading,
    setLoading,
  ] = useState(true)


  const [
    deletingId,
    setDeletingId,
  ] = useState(null)


  const [
    datasetPendingDelete,
    setDatasetPendingDelete,
  ] = useState(null)


  const [
    exportingId,
    setExportingId,
  ] = useState(null)


  // ========================================================
  // CURRENT SPREADSHEET
  // ========================================================

  const [
    datasetName,
    setDatasetName,
  ] = useState(
    'New-SSAS-Dataset'
  )


  /*
   * Real column names.
   *
   * These start blank.
   * There is no Variable1,
   * Variable2, etc.
   */
  const [
    sheetColumns,
    setSheetColumns,
  ] = useState(
    Array(
      DEFAULT_COLUMN_COUNT
    ).fill('')
  )


  /*
   * Complete data.
   *
   * Even when only 100 rows are
   * displayed, all imported rows
   * stay here.
   */
  const [
    sheetRows,
    setSheetRows,
  ] = useState(
    createEmptyRows(
      DEFAULT_ROW_COUNT,
      DEFAULT_COLUMN_COUNT
    )
  )


  /*
   * User-selected measurement
   * overrides by column index.
   */
  const [
    measurementOverrides,
    setMeasurementOverrides,
  ] = useState({})


  // ========================================================
  // PAGINATION
  // ========================================================

  const [
    currentPage,
    setCurrentPage,
  ] = useState(1)


  // ========================================================
  // ACTIVE SPREADSHEET CELL
  // ========================================================

  const [
    activeCell,
    setActiveCell,
  ] = useState({
    area: 'header',
    rowIndex: 0,
    columnIndex: 0,
  })


  // ========================================================
  // EXPORT / IMPORT MODAL
  // ========================================================

  const [
    transferOpen,
    setTransferOpen,
  ] = useState(false)


  // ========================================================
  // GENERAL
  // ========================================================

  const [
    saving,
    setSaving,
  ] = useState(false)


  const [
    error,
    setError,
  ] = useState('')


  const [
    success,
    setSuccess,
  ] = useState('')


  // ========================================================
  // LOAD SAVED DATASETS
  // ========================================================

  const loadDatasets =
    async () => {
      setLoading(true)


      try {
        const response =
          await api.get(
            '/datasets'
          )


        setDatasets(
          response
            .data
            .datasets ||
          []
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


  useEffect(() => {
    loadDatasets()
  }, [])


  // ========================================================
  // FIND COLUMNS CURRENTLY IN USE
  // ========================================================

  const usedColumnIndexes =
    useMemo(
      () =>
        sheetColumns
          .map(
            (
              _,
              index
            ) =>
              index
          )
          .filter(
            (columnIndex) => {
              const header =
                String(
                  sheetColumns[
                    columnIndex
                  ] ?? ''
                ).trim()


              const hasData =
                sheetRows.some(
                  (row) =>
                    String(
                      row?.[
                        columnIndex
                      ] ?? ''
                    ).trim() !== ''
                )


              return (
                header !== '' ||
                hasData
              )
            }
          ),

      [
        sheetColumns,
        sheetRows,
      ]
    )


  // ========================================================
  // ACTUAL CASE COUNT
  // ========================================================

  const dataRowCount =
    useMemo(
      () =>
        sheetRows.filter(
          (row) =>
            row.some(
              (value) =>
                String(
                  value ?? ''
                ).trim() !== ''
            )
        ).length,

      [
        sheetRows,
      ]
    )


  // ========================================================
  // PAGINATION VALUES
  // ========================================================

  const totalPages =
    Math.max(
      1,

      Math.ceil(
        sheetRows.length /
        PAGE_SIZE
      )
    )


  /*
   * Ensure current page remains valid
   * after deleting rows.
   */
  useEffect(() => {
    if (
      currentPage >
      totalPages
    ) {
      setCurrentPage(
        totalPages
      )
    }
  }, [
    currentPage,
    totalPages,
  ])


  const pageStart =
    (
      currentPage - 1
    ) * PAGE_SIZE


  const pageEnd =
    Math.min(
      pageStart +
        PAGE_SIZE,

      sheetRows.length
    )


  const visibleRows =
    useMemo(
      () =>
        sheetRows
          .slice(
            pageStart,
            pageEnd
          )
          .map(
            (
              row,
              localIndex
            ) => ({
              row,

              actualRowIndex:
                pageStart +
                localIndex,
            })
          ),

      [
        sheetRows,
        pageStart,
        pageEnd,
      ]
    )


  // ========================================================
  // RESET SPREADSHEET SCROLL
  // ========================================================

  const resetSpreadsheetScroll =
    () => {
      window.requestAnimationFrame(
        () => {
          window.requestAnimationFrame(
            () => {
              if (
                sheetRef.current
              ) {
                sheetRef.current.scrollTop =
                  0

                sheetRef.current.scrollLeft =
                  0
              }
            }
          )
        }
      )
    }


  // ========================================================
  // UPDATE CELL
  // ========================================================

  const updateCell = (
    rowIndex,
    columnIndex,
    value
  ) => {
    setSheetRows(
      (previous) => {
        const copy =
          previous.map(
            (row) => [
              ...row,
            ]
          )


        if (
          !copy[rowIndex]
        ) {
          copy[rowIndex] =
            Array(
              sheetColumns.length
            ).fill('')
        }


        copy[
          rowIndex
        ][
          columnIndex
        ] =
          value


        return copy
      }
    )
  }


  // ========================================================
  // UPDATE COLUMN NAME
  // ========================================================

  const updateColumnName = (
    columnIndex,
    value
  ) => {
    setSheetColumns(
      (previous) =>
        previous.map(
          (
            column,
            index
          ) =>
            index ===
              columnIndex
              ? value
              : column
        )
    )
  }


  // ========================================================
  // UPDATE MEASUREMENT LEVEL
  // ========================================================

  const updateMeasurementLevel = (
    columnIndex,
    value
  ) => {
    setMeasurementOverrides(
      (previous) => ({
        ...previous,

        [columnIndex]:
          value,
      })
    )
  }


  // ========================================================
  // ADD ROW
  // ========================================================

  const addRow = () => {
    setSheetRows(
      (previous) => [
        ...previous,

        Array(
          sheetColumns.length
        ).fill(''),
      ]
    )


    /*
     * Jump to final page so the newly
     * created row can be seen.
     */
    const nextRowCount =
      sheetRows.length + 1


    setCurrentPage(
      Math.ceil(
        nextRowCount /
        PAGE_SIZE
      )
    )
  }


  // ========================================================
  // DELETE CASE / ROW
  // ========================================================

  const deleteRow = (
    rowIndex
  ) => {
    setSheetRows(
      (previous) => {
        let next =
          previous.filter(
            (
              _,
              index
            ) =>
              index !==
              rowIndex
          )


        if (
          !next.length
        ) {
          next =
            createEmptyRows(
              1,
              sheetColumns.length
            )
        }


        return next
      }
    )


    setError('')


    setSuccess(
      `Case ${
        rowIndex + 1
      } removed.`
    )
  }


  // ========================================================
  // ADD VARIABLE
  // ========================================================

  const addColumn = () => {
    setSheetColumns(
      (previous) => [
        ...previous,
        '',
      ]
    )


    setSheetRows(
      (previous) =>
        previous.map(
          (row) => [
            ...row,
            '',
          ]
        )
    )
  }


  // ========================================================
  // IMPORT COMPLETE DATASET
  // ========================================================

  const applyImportedDataset = (
    matrix,
    filename = null
  ) => {
    setError('')
    setSuccess('')


    if (
      !Array.isArray(
        matrix
      ) ||
      matrix.length < 2
    ) {
      setError(
        'The imported dataset must contain a header row and at least one data row.'
      )

      return
    }


    // ------------------------------------------------------
    // Headers
    // ------------------------------------------------------

    const firstRow =
      Array.isArray(
        matrix[0]
      )
        ? matrix[0]
        : []


    // ------------------------------------------------------
    // Valid data rows
    // ------------------------------------------------------

    const rawRows =
      matrix
        .slice(1)
        .filter(
          (row) =>
            Array.isArray(
              row
            ) &&
            row.some(
              (value) =>
                String(
                  value ?? ''
                ).trim() !== ''
            )
        )


    const rowWidths =
      rawRows.map(
        (row) =>
          row.length
      )


    const columnCount =
      Math.max(
        firstRow.length,
        ...rowWidths,
        0
      )


    if (
      columnCount === 0
    ) {
      setError(
        'No variables were found in the imported dataset.'
      )

      return
    }


    // ------------------------------------------------------
    // Build REAL headers
    // ------------------------------------------------------

    const newColumns =
      Array.from(
        {
          length:
            columnCount,
        },
        (
          _,
          columnIndex
        ) =>
          String(
            firstRow?.[
              columnIndex
            ] ?? ''
          ).trim()
      )


    // ------------------------------------------------------
    // Build REAL data rows
    // ------------------------------------------------------

    const importedRows =
      rawRows.map(
        (sourceRow) =>
          Array.from(
            {
              length:
                columnCount,
            },
            (
              _,
              columnIndex
            ) => {
              const value =
                sourceRow?.[
                  columnIndex
                ]


              if (
                value === null ||
                value === undefined
              ) {
                return ''
              }


              /*
               * Inputs display strings
               * consistently.
               */
              return String(
                value
              )
            }
          )
      )


    if (
      !importedRows.length
    ) {
      setError(
        'No cases were found in the imported dataset.'
      )

      return
    }


    // ------------------------------------------------------
    // Add four blank rows at the end
    // ------------------------------------------------------

    const blankRows =
      createEmptyRows(
        4,
        columnCount
      )


    const newRows = [
      ...importedRows,
      ...blankRows,
    ]


    // ------------------------------------------------------
    // REPLACE complete spreadsheet
    // ------------------------------------------------------

    setSheetColumns(
      newColumns
    )


    setSheetRows(
      newRows
    )


    /*
     * Imported dataset must be
     * auto-detected again.
     */
    setMeasurementOverrides(
      {}
    )


    // ------------------------------------------------------
    // Dataset name
    // ------------------------------------------------------

    if (filename) {
      const cleanName =
        String(
          filename
        )
          .replace(
            /\.[^/.]+$/,
            ''
          )
          .trim()


      if (cleanName) {
        setDatasetName(
          cleanName
        )
      }
    }


    // ------------------------------------------------------
    // Return to first page
    // ------------------------------------------------------

    setCurrentPage(1)


    setActiveCell({
      area:
        'data',

      rowIndex:
        0,

      columnIndex:
        0,
    })


    resetSpreadsheetScroll()


    setSuccess(
      `Loaded ${importedRows.length} cases and ${newColumns.length} variables into the spreadsheet.`
    )
  }


  // ========================================================
  // PASTE COMPLETE DATASET
  // ========================================================

  const applyDatasetPaste = (
    matrix,
    startColumnIndex
  ) => {
    if (
      !Array.isArray(
        matrix
      ) ||
      !matrix.length
    ) {
      return
    }


    const pastedHeaders =
      Array.isArray(
        matrix[0]
      )
        ? matrix[0]
        : []


    const pastedRows =
      matrix
        .slice(1)
        .filter(
          (row) =>
            Array.isArray(
              row
            ) &&
            row.some(
              (value) =>
                String(
                  value ?? ''
                ).trim() !== ''
            )
        )


    const widths =
      pastedRows.map(
        (row) =>
          row.length
      )


    const pastedWidth =
      Math.max(
        pastedHeaders.length,
        ...widths,
        0
      )


    if (
      pastedWidth === 0
    ) {
      return
    }


    const totalColumns =
      Math.max(
        sheetColumns.length,

        startColumnIndex +
          pastedWidth
      )


    // ------------------------------------------------------
    // Columns
    // ------------------------------------------------------

    const newColumns =
      Array.from(
        {
          length:
            totalColumns,
        },
        (
          _,
          index
        ) =>
          sheetColumns?.[
            index
          ] ?? ''
      )


    pastedHeaders.forEach(
      (
        value,
        offset
      ) => {
        newColumns[
          startColumnIndex +
          offset
        ] =
          String(
            value ?? ''
          ).trim()
      }
    )


    // ------------------------------------------------------
    // Rows
    // ------------------------------------------------------

    const requiredRows =
      Math.max(
        sheetRows.length,

        pastedRows.length + 4,

        DEFAULT_ROW_COUNT
      )


    const newRows =
      Array.from(
        {
          length:
            requiredRows,
        },
        (
          _,
          rowIndex
        ) =>
          Array.from(
            {
              length:
                totalColumns,
            },
            (
              __,
              columnIndex
            ) =>
              sheetRows?.[
                rowIndex
              ]?.[
                columnIndex
              ] ?? ''
          )
      )


    pastedRows.forEach(
      (
        pastedRow,
        pastedRowIndex
      ) => {
        pastedRow.forEach(
          (
            value,
            offset
          ) => {
            newRows[
              pastedRowIndex
            ][
              startColumnIndex +
              offset
            ] =
              value === null ||
              value === undefined
                ? ''
                : String(value)
          }
        )
      }
    )


    setSheetColumns(
      newColumns
    )


    setSheetRows(
      newRows
    )


    setMeasurementOverrides(
      {}
    )


    setCurrentPage(1)


    resetSpreadsheetScroll()


    setError('')


    setSuccess(
      `Pasted ${pastedRows.length} cases and ${pastedHeaders.length} variables into the spreadsheet.`
    )
  }


  // ========================================================
  // PASTE CELLS INTO EXISTING DATASET
  // ========================================================

  const applyCellPaste = (
    matrix,
    startRowIndex,
    startColumnIndex
  ) => {
    if (
      !Array.isArray(
        matrix
      ) ||
      !matrix.length
    ) {
      return
    }


    const widths =
      matrix.map(
        (row) =>
          Array.isArray(row)
            ? row.length
            : 0
      )


    const pastedWidth =
      Math.max(
        ...widths,
        0
      )


    if (
      pastedWidth === 0
    ) {
      return
    }


    const requiredColumns =
      Math.max(
        sheetColumns.length,

        startColumnIndex +
          pastedWidth
      )


    const requiredRows =
      Math.max(
        sheetRows.length,

        startRowIndex +
          matrix.length
      )


    const newColumns =
      Array.from(
        {
          length:
            requiredColumns,
        },
        (
          _,
          index
        ) =>
          sheetColumns?.[
            index
          ] ?? ''
      )


    const newRows =
      Array.from(
        {
          length:
            requiredRows,
        },
        (
          _,
          rowIndex
        ) =>
          Array.from(
            {
              length:
                requiredColumns,
            },
            (
              __,
              columnIndex
            ) =>
              sheetRows?.[
                rowIndex
              ]?.[
                columnIndex
              ] ?? ''
          )
      )


    matrix.forEach(
      (
        pastedRow,
        pastedRowIndex
      ) => {
        if (
          !Array.isArray(
            pastedRow
          )
        ) {
          return
        }


        pastedRow.forEach(
          (
            value,
            pastedColumnIndex
          ) => {
            newRows[
              startRowIndex +
                pastedRowIndex
            ][
              startColumnIndex +
                pastedColumnIndex
            ] =
              value === null ||
              value === undefined
                ? ''
                : String(value)
          }
        )
      }
    )


    setSheetColumns(
      newColumns
    )


    setSheetRows(
      newRows
    )


    setError('')


    setSuccess(
      `Pasted ${matrix.length} row(s) into the spreadsheet.`
    )
  }


  // ========================================================
  // IMPORT FROM MODAL
  // ========================================================

  const loadImportedMatrix = (
    matrix,
    filename
  ) => {
    applyImportedDataset(
      matrix,
      filename
    )
  }


  // ========================================================
  // SPREADSHEET COPY / PASTE
  // ========================================================

  const handleSpreadsheetPaste = (
    event
  ) => {
    const text =
      event
        .clipboardData
        ?.getData(
          'text/plain'
        )


    if (!text) {
      return
    }


    const matrix =
      parseClipboardData(
        text
      )


    if (
      !matrix.length
    ) {
      return
    }


    event.preventDefault()


    const headersBlank =
      sheetColumns.every(
        (column) =>
          String(
            column ?? ''
          ).trim() === ''
      )


    // ------------------------------------------------------
    // Paste complete dataset into header
    // ------------------------------------------------------

    if (
      activeCell.area ===
      'header'
    ) {
      if (
        headersBlank &&
        activeCell.columnIndex ===
          0
      ) {
        applyImportedDataset(
          matrix
        )

        return
      }


      applyDatasetPaste(
        matrix,
        activeCell.columnIndex
      )

      return
    }


    // ------------------------------------------------------
    // Paste complete dataset into first
    // blank data cell
    // ------------------------------------------------------

    if (
      activeCell.area ===
        'data' &&
      activeCell.rowIndex ===
        0 &&
      activeCell.columnIndex ===
        0 &&
      headersBlank
    ) {
      applyImportedDataset(
        matrix
      )

      return
    }


    // ------------------------------------------------------
    // Paste cells starting at selected
    // location
    // ------------------------------------------------------

    applyCellPaste(
      matrix,

      activeCell.rowIndex,

      activeCell.columnIndex
    )
  }


  // ========================================================
  // RESET NEW SPREADSHEET
  // ========================================================

  const resetSheet = () => {
    setDatasetName(
      'New-SSAS-Dataset'
    )


    setSheetColumns(
      Array(
        DEFAULT_COLUMN_COUNT
      ).fill('')
    )


    setSheetRows(
      createEmptyRows(
        DEFAULT_ROW_COUNT,
        DEFAULT_COLUMN_COUNT
      )
    )


    setMeasurementOverrides(
      {}
    )


    setCurrentPage(1)


    setActiveCell({
      area:
        'header',

      rowIndex:
        0,

      columnIndex:
        0,
    })


    setError('')
    setSuccess('')


    resetSpreadsheetScroll()
  }


  // ========================================================
  // SAVE DATASET
  // ========================================================

  const saveDataset =
    async () => {
      setSaving(true)

      setError('')
      setSuccess('')


      try {
        if (
          !usedColumnIndexes.length
        ) {
          throw new Error(
            'Enter or import data before saving.'
          )
        }


        // --------------------------------------------------
        // Headers
        // --------------------------------------------------

        const headers =
          usedColumnIndexes.map(
            (
              columnIndex,
              outputIndex
            ) => {
              const name =
                String(
                  sheetColumns?.[
                    columnIndex
                  ] ?? ''
                ).trim()


              return (
                name ||
                `Column${
                  outputIndex + 1
                }`
              )
            }
          )


        // --------------------------------------------------
        // Duplicate validation
        // --------------------------------------------------

        const normalized =
          headers.map(
            (header) =>
              header
                .toLowerCase()
                .trim()
          )


        if (
          new Set(
            normalized
          ).size !==
          normalized.length
        ) {
          throw new Error(
            'Variable names must be unique.'
          )
        }


        // --------------------------------------------------
        // Extract actual cases
        // --------------------------------------------------

        const rows =
          sheetRows
            .map(
              (row) =>
                usedColumnIndexes.map(
                  (columnIndex) =>
                    row?.[
                      columnIndex
                    ] ?? ''
                )
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


        if (
          !rows.length
        ) {
          throw new Error(
            'The spreadsheet contains no cases.'
          )
        }


        // --------------------------------------------------
        // Generate CSV
        // --------------------------------------------------

        const csv = [
          headers
            .map(
              escapeCSV
            )
            .join(','),

          ...rows.map(
            (row) =>
              row
                .map(
                  escapeCSV
                )
                .join(',')
          ),
        ].join('\n')


        // --------------------------------------------------
        // Dataset filename
        // --------------------------------------------------

        let filename =
          datasetName.trim()


        if (
          !filename
        ) {
          filename =
            'New-SSAS-Dataset'
        }


        if (
          !filename
            .toLowerCase()
            .endsWith(
              '.csv'
            )
        ) {
          filename += '.csv'
        }


        // --------------------------------------------------
        // Create file
        // --------------------------------------------------

        const file =
          new File(
            [csv],
            filename,
            {
              type:
                'text/csv',
            }
          )


        const formData =
          new FormData()


        formData.append(
          'file',
          file
        )


        // --------------------------------------------------
        // Upload
        // --------------------------------------------------

        const response =
          await api.post(
            '/datasets/upload',
            formData
          )


        const newDatasetId =
          response.data.id


        // --------------------------------------------------
        // Save measurement levels
        // --------------------------------------------------

        for (
          let outputIndex = 0;
          outputIndex <
          usedColumnIndexes.length;
          outputIndex += 1
        ) {
          const originalColumnIndex =
            usedColumnIndexes[
              outputIndex
            ]


          const column =
            headers[
              outputIndex
            ]


          const automatic =
            detectMeasurementLevel(
              rows.map(
                (row) =>
                  row[
                    outputIndex
                  ]
              )
            )


          const level =
            measurementOverrides[
              originalColumnIndex
            ] ||
            automatic


          await api.patch(
            `/datasets/${newDatasetId}/variables/${encodeURIComponent(column)}`,
            {
              measurement_level:
                level,
            }
          )
        }


        await loadDatasets()


        setSuccess(
          `"${filename}" saved successfully.`
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


  // ========================================================
  // DELETE SAVED DATASET
  // ========================================================

  const deleteSavedDataset =
    async () => {
      if (
        !datasetPendingDelete
      ) {
        return
      }


      const target =
        datasetPendingDelete


      setDeletingId(
        target.id
      )


      setError('')
      setSuccess('')


      try {
        await api.delete(
          `/datasets/${target.id}`
        )


        setDatasets(
          (previous) =>
            previous.filter(
              (item) =>
                item.id !==
                target.id
            )
        )


        setDatasetPendingDelete(
          null
        )


        setSuccess(
          `"${target.original_filename}" deleted successfully.`
        )

      } catch (err) {
        setError(
          getErrorMessage(
            err
          )
        )

      } finally {
        setDeletingId(null)
      }
    }


  // ========================================================
  // EXPORT SAVED DATASET
  // ========================================================

  const exportSavedDataset =
    async (dataset) => {
      setExportingId(
        dataset.id
      )


      setError('')


      try {
        const rows = []

        let columns = []
        let offset = 0

        const limit = 5000

        let hasMore = true


        while (
          hasMore
        ) {
          const response =
            await api.get(
              `/datasets/${dataset.id}/data`,
              {
                params: {
                  offset,
                  limit,
                },
              }
            )


          if (
            !columns.length
          ) {
            columns =
              response
                .data
                .columns ||
              []
          }


          rows.push(
            ...(
              response
                .data
                .rows ||
              []
            )
          )


          hasMore =
            Boolean(
              response
                .data
                .has_more
            )


          const returned =
            response
              .data
              .returned_rows ||
            0


          offset +=
            returned


          if (
            returned === 0
          ) {
            break
          }
        }


        const csv = [
          columns
            .map(
              escapeCSV
            )
            .join(','),

          ...rows.map(
            (row) =>
              columns
                .map(
                  (column) =>
                    escapeCSV(
                      row?.[
                        column
                      ]
                    )
                )
                .join(',')
          ),
        ].join('\n')


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


        const baseName =
          dataset
            .original_filename
            .replace(
              /\.[^/.]+$/,
              ''
            )


        link.href =
          url


        link.download =
          `${baseName}.csv`


        document
          .body
          .appendChild(
            link
          )


        link.click()


        document
          .body
          .removeChild(
            link
          )


        URL.revokeObjectURL(
          url
        )

      } catch (err) {
        setError(
          getErrorMessage(
            err
          )
        )

      } finally {
        setExportingId(
          null
        )
      }
    }


  // ========================================================
  // EXPORT / IMPORT CURRENT SHEET
  // ========================================================

  const transferColumns =
    usedColumnIndexes.map(
      (
        columnIndex,
        outputIndex
      ) =>
        String(
          sheetColumns?.[
            columnIndex
          ] ?? ''
        ).trim() ||
        `Column${
          outputIndex + 1
        }`
    )


  const transferRows =
    sheetRows
      .map(
        (row) =>
          usedColumnIndexes.map(
            (columnIndex) =>
              row?.[
                columnIndex
              ] ?? ''
          )
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


  // ========================================================
  // PAGINATION CONTROLS
  // ========================================================

  const goToPreviousPage =
    () => {
      setCurrentPage(
        (previous) =>
          Math.max(
            1,
            previous - 1
          )
      )


      resetSpreadsheetScroll()
    }


  const goToNextPage =
    () => {
      setCurrentPage(
        (previous) =>
          Math.min(
            totalPages,
            previous + 1
          )
      )


      resetSpreadsheetScroll()
    }


  // ========================================================
  // RENDER
  // ========================================================

  return (
    <AppShell>

      <div className="datasets-page">


        {/* ==================================================
            TOP MENU
        ================================================== */}

        <div className="sheet-toolbar">

          <div className="sheet-toolbar-left">

            <button
              type="button"
              className="sheet-tab active"
              onClick={
                resetSheet
              }
            >
              enter new data
            </button>


            <button
              type="button"
              className="sheet-tab"
              onClick={() =>
                setTransferOpen(
                  true
                )
              }
            >
              export / import
            </button>


            <button
              type="button"
              className="sheet-tab"
              onClick={() =>
                document
                  .getElementById(
                    'saved-datasets'
                  )
                  ?.scrollIntoView({
                    behavior:
                      'smooth',
                  })
              }
            >
              prepare data
            </button>


            <button
              type="button"
              className="sheet-tab sheet-tab-muted"
            >
              settings
            </button>

          </div>


          <div className="sheet-toolbar-note">
            import is previewed before saving
          </div>

        </div>


        {/* ==================================================
            DATASET NAME / ACTIONS
        ================================================== */}

        <div className="sheet-control-bar">

          <input
            className="sheet-name-input"
            value={
              datasetName
            }
            onChange={(event) =>
              setDatasetName(
                event.target.value
              )
            }
            placeholder="Dataset name"
          />


          <div className="sheet-control-actions">

            <button
              type="button"
              className="sheet-small-button"
              onClick={
                addRow
              }
            >
              <Plus
                size={14}
              />

              row
            </button>


            <button
              type="button"
              className="sheet-small-button"
              onClick={
                addColumn
              }
            >
              <Plus
                size={14}
              />

              variable
            </button>


            <button
              type="button"
              className="sheet-save-button"
              disabled={
                saving
              }
              onClick={
                saveDataset
              }
            >
              <Save
                size={14}
              />

              {saving
                ? 'saving...'
                : 'save dataset'}
            </button>

          </div>

        </div>


        {/* ==================================================
            MESSAGES
        ================================================== */}

        {error && (
          <div className="sheet-message error">
            {error}
          </div>
        )}


        {success && (
          <div className="sheet-message success">
            {success}
          </div>
        )}


        {/* ==================================================
            SPREADSHEET
        ================================================== */}

        <div
          ref={
            sheetRef
          }
          className="sheet-grid-wrapper"
          onPaste={
            handleSpreadsheetPaste
          }
        >

          <table className="sheet-grid">

            <thead>


              {/* ============================================
                  MEASUREMENT LEVEL
              ============================================ */}

              <tr className="sheet-level-row">

                <th className="sheet-case-column" />


                {sheetColumns.map(
                  (
                    column,
                    columnIndex
                  ) => {
                    const columnValues =
                      sheetRows.map(
                        (row) =>
                          row?.[
                            columnIndex
                          ] ?? ''
                      )


                    const automatic =
                      detectMeasurementLevel(
                        columnValues
                      )


                    const selected =
                      measurementOverrides[
                        columnIndex
                      ] ||
                      automatic


                    return (
                      <th
                        key={
                          `level-${columnIndex}`
                        }
                        className="sheet-level-cell"
                      >

                        <div className="sheet-level-control">

                          <select
                            value={
                              selected
                            }
                            onChange={(event) =>
                              updateMeasurementLevel(
                                columnIndex,
                                event.target.value
                              )
                            }
                            title={
                              `SSAS automatically detected ${automatic}`
                            }
                          >

                            <option value="metric">
                              metric
                            </option>


                            <option value="nominal">
                              nominal
                            </option>


                            <option value="ordinal">
                              ordinal
                            </option>

                          </select>


                          <span
                            className={
                              `measurement-dot ${selected}`
                            }
                          />

                        </div>

                      </th>
                    )
                  }
                )}

              </tr>


              {/* ============================================
                  VARIABLE HEADINGS
              ============================================ */}

              <tr className="sheet-header-row">

                <th className="sheet-case-column sheet-case-title">
                  Case
                </th>


                {sheetColumns.map(
                  (
                    column,
                    columnIndex
                  ) => (
                    <th
                      key={
                        `header-${columnIndex}`
                      }
                      className="sheet-variable-header"
                    >

                      <input
                        type="text"

                        value={
                          String(
                            column ?? ''
                          )
                        }

                        placeholder=""

                        onFocus={() =>
                          setActiveCell({
                            area:
                              'header',

                            rowIndex:
                              0,

                            columnIndex,
                          })
                        }

                        onClick={() =>
                          setActiveCell({
                            area:
                              'header',

                            rowIndex:
                              0,

                            columnIndex,
                          })
                        }

                        onChange={(event) =>
                          updateColumnName(
                            columnIndex,
                            event.target.value
                          )
                        }
                      />

                    </th>
                  )
                )}

              </tr>

            </thead>


            {/* ==============================================
                DATA ROWS
            ============================================== */}

            <tbody>

              {visibleRows.map(
                ({
                  row,
                  actualRowIndex,
                }) => (
                  <tr
                    key={
                      `case-${actualRowIndex}`
                    }
                    className="sheet-data-row"
                  >


                    {/* ======================================
                        CASE NUMBER / DELETE
                    ====================================== */}

                    <td className="sheet-case-column sheet-case-cell">

                      <span className="sheet-case-number">
                        {
                          actualRowIndex +
                          1
                        }
                      </span>


                      <button
                        type="button"

                        className="sheet-case-delete"

                        title={
                          `Delete Case ${
                            actualRowIndex +
                            1
                          }`
                        }

                        onClick={() =>
                          deleteRow(
                            actualRowIndex
                          )
                        }
                      >
                        <Trash2
                          size={15}
                        />
                      </button>

                    </td>


                    {/* ======================================
                        ACTUAL CELLS
                    ====================================== */}

                    {sheetColumns.map(
                      (
                        _,
                        columnIndex
                      ) => {
                        const value =
                          row?.[
                            columnIndex
                          ] ?? ''


                        return (
                          <td
                            key={
                              `cell-${actualRowIndex}-${columnIndex}`
                            }
                            className="sheet-data-cell"
                          >

                            <input
                              type="text"

                              value={
                                String(
                                  value
                                )
                              }

                              onFocus={() =>
                                setActiveCell({
                                  area:
                                    'data',

                                  rowIndex:
                                    actualRowIndex,

                                  columnIndex,
                                })
                              }

                              onClick={() =>
                                setActiveCell({
                                  area:
                                    'data',

                                  rowIndex:
                                    actualRowIndex,

                                  columnIndex,
                                })
                              }

                              onChange={(event) =>
                                updateCell(
                                  actualRowIndex,
                                  columnIndex,
                                  event.target.value
                                )
                              }
                            />

                          </td>
                        )
                      }
                    )}

                  </tr>
                )
              )}

            </tbody>

          </table>

        </div>


        {/* ==================================================
            SPREADSHEET PAGINATION
        ================================================== */}

        <div
          style={{
            display:
              'flex',

            justifyContent:
              'space-between',

            alignItems:
              'center',

            gap:
              '12px',

            marginTop:
              '10px',

            marginBottom:
              '20px',

            fontSize:
              '11px',

            color:
              '#667085',
          }}
        >

          <div>

            {dataRowCount > 0
              ? (
                  <>
                    Showing cases{' '}

                    <strong>
                      {
                        pageStart +
                        1
                      }
                    </strong>

                    {' '}to{' '}

                    <strong>
                      {
                        Math.min(
                          pageEnd,
                          sheetRows.length
                        )
                      }
                    </strong>

                    {' '}of{' '}

                    <strong>
                      {
                        sheetRows.length
                      }
                    </strong>

                    {' '}rows
                  </>
                )
              : (
                  <>
                    Empty spreadsheet
                  </>
                )}

          </div>


          <div
            style={{
              display:
                'flex',

              alignItems:
                'center',

              gap:
                '8px',
            }}
          >

            <button
              type="button"
              className="sheet-small-button"
              disabled={
                currentPage <= 1
              }
              onClick={
                goToPreviousPage
              }
            >
              <ChevronLeft
                size={14}
              />

              previous
            </button>


            <span>

              Page{' '}

              <strong>
                {currentPage}
              </strong>

              {' '}of{' '}

              <strong>
                {totalPages}
              </strong>

            </span>


            <button
              type="button"
              className="sheet-small-button"
              disabled={
                currentPage >=
                totalPages
              }
              onClick={
                goToNextPage
              }
            >
              next

              <ChevronRight
                size={14}
              />
            </button>

          </div>

        </div>


        {/* ==================================================
            SAVED DATASETS
        ================================================== */}

        <section
          id="saved-datasets"
          className="saved-datasets-section"
        >

          <div className="saved-datasets-heading">

            <div>

              <h2>
                Saved Datasets
              </h2>


              <span>
                {datasets.length}
                {' '}
                dataset
                {datasets.length === 1
                  ? ''
                  : 's'}
              </span>

            </div>


            <button
              type="button"
              className="saved-refresh-button"
              disabled={
                loading
              }
              onClick={
                loadDatasets
              }
            >
              <RefreshCw
                size={15}
              />

              refresh
            </button>

          </div>


          {loading ? (

            <div className="saved-empty">
              Loading datasets...
            </div>

          ) : datasets.length === 0 ? (

            <div className="saved-empty compact">

              No saved datasets yet.
              Enter, paste or import data
              in the spreadsheet above,
              then click Save Dataset.

            </div>

          ) : (

            <div className="saved-table-wrapper">

              <table className="saved-table">

                <thead>

                  <tr>

                    <th>
                      Dataset
                    </th>

                    <th>
                      Rows
                    </th>

                    <th>
                      Columns
                    </th>

                    <th>
                      Type
                    </th>

                    <th>
                      Status
                    </th>

                    <th>
                      Source
                    </th>

                    <th>
                      Actions
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {datasets.map(
                    (dataset) => {
                      const derived =
                        dataset.is_derived ||
                        dataset.status ===
                          'prepared'


                      return (
                        <tr
                          key={
                            dataset.id
                          }
                        >

                          <td>

                            <div className="saved-dataset-name">

                              <FileSpreadsheet
                                size={17}
                              />


                              <div>

                                <strong>
                                  {
                                    dataset
                                      .original_filename
                                  }
                                </strong>


                                {derived && (
                                  <span>
                                    Prepared Dataset
                                  </span>
                                )}

                              </div>

                            </div>

                          </td>


                          <td>
                            {
                              dataset
                                .row_count
                            }
                          </td>


                          <td>
                            {
                              dataset
                                .column_count
                            }
                          </td>


                          <td>
                            {
                              dataset
                                .file_type
                                ?.toUpperCase()
                            }
                          </td>


                          <td>
                            {
                              dataset.status
                            }
                          </td>


                          <td>
                            {derived
                              ? 'Derived'
                              : 'Original'}
                          </td>


                          <td>

                            <div className="saved-actions">

                              <button
                                type="button"
                                className="saved-action"
                                onClick={() =>
                                  navigate(
                                    `/datasets/${dataset.id}/workspace`
                                  )
                                }
                              >
                                <ExternalLink
                                  size={13}
                                />

                                open
                              </button>


                              <button
                                type="button"
                                className="saved-action prepare"
                                onClick={() =>
                                  navigate(
                                    `/datasets/${dataset.id}/prepare`
                                  )
                                }
                              >
                                <Sparkles
                                  size={13}
                                />

                                prepare
                              </button>


                              <button
                                type="button"
                                className="saved-action export"
                                disabled={
                                  exportingId ===
                                  dataset.id
                                }
                                onClick={() =>
                                  exportSavedDataset(
                                    dataset
                                  )
                                }
                              >
                                <Download
                                  size={13}
                                />

                                {exportingId ===
                                dataset.id
                                  ? 'exporting'
                                  : 'export'}
                              </button>


                              <button
                                type="button"
                                className="saved-action delete"
                                onClick={() =>
                                  setDatasetPendingDelete(
                                    dataset
                                  )
                                }
                              >
                                <Trash2
                                  size={13}
                                />

                                delete
                              </button>

                            </div>

                          </td>

                        </tr>
                      )
                    }
                  )}

                </tbody>

              </table>

            </div>
          )}

        </section>


        {/* ==================================================
            EXPORT / IMPORT MODAL
        ================================================== */}

        <DataTransferModal
          open={
            transferOpen
          }

          onClose={() =>
            setTransferOpen(
              false
            )
          }

          onImport={
            loadImportedMatrix
          }

          exportColumns={
            transferColumns
          }

          exportRows={
            transferRows
          }

          datasetName={
            datasetName
          }
        />


        {/* ==================================================
            DELETE DATASET CONFIRMATION
        ================================================== */}

        {datasetPendingDelete && (

          <div className="delete-modal-overlay">

            <div className="delete-modal">

              <div className="delete-modal-icon">

                <Trash2
                  size={24}
                />

              </div>


              <h2>
                Delete Dataset?
              </h2>


              <p>
                Are you sure you want
                to permanently delete:
              </p>


              <strong className="delete-dataset-name">
                {
                  datasetPendingDelete
                    .original_filename
                }
              </strong>


              <div className="delete-modal-warning">

                This removes the stored
                dataset file and its
                database record.

                <br />

                This action cannot be undone.

              </div>


              <div className="delete-modal-actions">

                <button
                  type="button"
                  className="delete-modal-cancel"
                  disabled={
                    deletingId !==
                    null
                  }
                  onClick={() =>
                    setDatasetPendingDelete(
                      null
                    )
                  }
                >
                  Cancel
                </button>


                <button
                  type="button"
                  className="delete-modal-confirm"
                  disabled={
                    deletingId !==
                    null
                  }
                  onClick={
                    deleteSavedDataset
                  }
                >
                  <Trash2
                    size={14}
                  />

                  {deletingId
                    ? 'Deleting...'
                    : 'Delete Dataset'}

                </button>

              </div>

            </div>

          </div>
        )}

      </div>

    </AppShell>
  )
}
