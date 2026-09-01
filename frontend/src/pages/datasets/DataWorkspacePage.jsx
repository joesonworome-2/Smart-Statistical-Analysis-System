import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  ArrowLeft,
  BarChart3,
  FilePlus2,
  Plus,
  Save,
  Sparkles,
  Trash2,
  Upload,
} from 'lucide-react'

import {
  useLocation,
  useNavigate,
  useParams,
} from 'react-router-dom'

import Plot from 'react-plotly.js'

import api from '../../api/api'
import AppShell from '../../components/AppShell'
import DataTransferModal from './DataTransferModal'

import './DataWorkspacePage.css'


// ==========================================================
// ANALYSIS METHODS
// ==========================================================

const analysisMethods = [
  'Descriptive / Charts',
  'Hypothesis Tests',
  'Correlation',
  'Regression',
  'Predictive Analytics',
  'ANCOVA',
  'Survival Analysis',
  'EFA / PCA',
  'Reliability',
  'Cluster Analysis',
  'ROC Analysis',
  'Mediation / Moderation',
  'Monte Carlo',
  'Sample Size',
]


// ==========================================================
// DESCRIPTIVE OPTIONS
// ==========================================================

const statisticOptions = [
  ['count', 'Number of Values'],
  ['mean', 'Mean'],
  ['median', 'Median'],
  ['mode', 'Mode'],
  ['sum', 'Sum'],

  [
    'standard_deviation',
    'Std. Deviation',
  ],

  [
    'standard_error',
    'Standard Error',
  ],

  ['variance', 'Variance'],
  ['minimum', 'Minimum'],
  ['maximum', 'Maximum'],
  ['range', 'Range'],

  ['q1', 'Quartile 1'],
  ['q2', 'Quartile 2'],
  ['q3', 'Quartile 3'],

  [
    'iqr',
    'Interquartile Range',
  ],

  [
    'median_absolute_deviation',
    'Median Absolute Deviation',
  ],

  ['skewness', 'Skewness'],
  ['kurtosis', 'Kurtosis'],

  [
    'confidence_interval_95',
    '95% Confidence Interval',
  ],

  [
    'coefficient_of_variation_percent',
    'Coefficient of Variation (%)',
  ],
]


const defaultCalculations = {
  count: true,

  mean: true,
  median: true,
  mode: false,
  sum: false,

  standard_deviation: true,
  standard_error: false,
  variance: false,

  minimum: true,
  maximum: true,
  range: false,

  q1: false,
  q2: false,
  q3: false,
  iqr: false,

  median_absolute_deviation: false,

  skewness: false,
  kurtosis: false,

  confidence_interval_95: false,

  coefficient_of_variation_percent:
    false,
}


// ==========================================================
// HELPERS
// ==========================================================

function getErrorMessage(error) {
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
    'Something went wrong.'
  )
}


function formatNumber(value) {
  if (
    value === null ||
    value === undefined
  ) {
    return '—'
  }

  if (
    typeof value ===
    'number'
  ) {
    return new Intl.NumberFormat(
      undefined,
      {
        maximumFractionDigits:
          4,
      }
    ).format(value)
  }

  return String(value)
}


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
// MEASUREMENT LEVEL AUTO-DETECTION
// ==========================================================

function detectManualLevel(values) {
  const cleanValues =
    values.filter(
      (value) =>
        value !== null &&
        value !== undefined &&
        String(value).trim() !== ''
    )


  if (!cleanValues.length) {
    return 'nominal'
  }


  const numeric =
    cleanValues.every(
      (value) =>
        !Number.isNaN(
          Number(value)
        )
    )


  const uniqueCount =
    new Set(
      cleanValues.map(String)
    ).size


  if (numeric) {
    /*
     * Binary numerical variables
     * such as 0/1 are treated
     * as nominal initially.
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
// CSV PARSER FOR COPY/PASTE
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
        current.trim()
      )

      current = ''

      continue
    }


    current += character
  }


  values.push(
    current.trim()
  )

  return values
}


function parseClipboardData(text) {
  const cleanText =
    text
      .replace(/\r\n/g, '\n')
      .replace(/\r/g, '\n')
      .trim()


  if (!cleanText) {
    return []
  }


  const lines =
    cleanText
      .split('\n')
      .filter(
        (line) =>
          line.trim() !== ''
      )


  const delimiter =
    cleanText.includes('\t')
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
      )
    }
  )
}


// ==========================================================
// COMPONENT
// ==========================================================

export default function DataWorkspacePage() {
  const navigate =
    useNavigate()

  const location =
    useLocation()

  const {
    datasetId,
  } = useParams()


  const isNewDataset =
    !datasetId


  // ========================================================
  // EXISTING DATASET STATE
  // ========================================================

  const [
    dataset,
    setDataset,
  ] = useState(null)

  const [
    columns,
    setColumns,
  ] = useState([])

  const [
    previewRows,
    setPreviewRows,
  ] = useState([])

  const [
    variables,
    setVariables,
  ] = useState([])

  const [
    measurementLevels,
    setMeasurementLevels,
  ] = useState({})


  // ========================================================
  // MANUAL DATASET STATE
  // ========================================================

  const [
    newDatasetName,
    setNewDatasetName,
  ] = useState(
    'New-SSAS-Dataset'
  )


  /*
   * Blank column names.
   *
   * Column 1 / Column 2 shown in the
   * interface are placeholders only.
   */

  const [
    manualColumns,
    setManualColumns,
  ] = useState([
    '',
    '',
    '',
    '',
    '',
  ])


  const [
    manualRows,
    setManualRows,
  ] = useState(
    Array.from(
      {
        length: 8,
      },
      () =>
        Array(5).fill('')
    )
  )


  /*
   * Measurement overrides are stored
   * by column INDEX.
   */

  const [
    manualLevels,
    setManualLevels,
  ] = useState({})


  // ========================================================
  // EXPORT / IMPORT MODAL
  // ========================================================

  const [
    transferModalOpen,
    setTransferModalOpen,
  ] = useState(false)


  // ========================================================
  // DESCRIPTIVE STATE
  // ========================================================

  const [
    selectedVariables,
    setSelectedVariables,
  ] = useState([])

  const [
    selectedStatistics,
    setSelectedStatistics,
  ] = useState(
    defaultCalculations
  )

  const [
    descriptiveResults,
    setDescriptiveResults,
  ] = useState({})

  const [
    fullRows,
    setFullRows,
  ] = useState([])

  const [
    calculationComplete,
    setCalculationComplete,
  ] = useState(false)

  const [
    showNormalCurve,
    setShowNormalCurve,
  ] = useState(true)


  // ========================================================
  // GENERAL STATE
  // ========================================================

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
    error,
    setError,
  ] = useState('')

  const [
    success,
    setSuccess,
  ] = useState('')


  // ========================================================
  // LOAD IMPORTED FILE INTO EDITABLE FORM
  // ========================================================

  const loadImportedFileIntoForm = (
    matrix,
    filename
  ) => {
    setError('')
    setSuccess('')


    if (
      !Array.isArray(matrix) ||
      matrix.length < 2
    ) {
      setError(
        'Imported file must contain headers and at least one data row.'
      )

      return
    }


    const columnCount =
      Math.max(
        ...matrix.map(
          (row) =>
            row.length
        )
      )


    const sourceHeaders =
      matrix[0]


    /*
     * First imported row becomes the
     * REAL variable names.
     */

    const headers =
      Array.from(
        {
          length:
            columnCount,
        },
        (_, index) =>
          String(
            sourceHeaders[
              index
            ] ?? ''
          ).trim()
      )


    /*
     * Everything after first row
     * becomes cases.
     */

    const importedRows =
      matrix
        .slice(1)
        .map(
          (row) =>
            Array.from(
              {
                length:
                  columnCount,
              },
              (_, index) =>
                row[index] ?? ''
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
      !importedRows.length
    ) {
      setError(
        'The imported file contains no data rows.'
      )

      return
    }


    /*
     * Keep at least eight rows visible
     * for additional manual entry.
     */

    const visibleRows =
      Math.max(
        importedRows.length,
        8
      )


    const displayRows =
      Array.from(
        {
          length:
            visibleRows,
        },
        (_, index) =>
          importedRows[index] ||
          Array(
            columnCount
          ).fill('')
      )


    setManualColumns(
      headers
    )

    setManualRows(
      displayRows
    )


    /*
     * Clear previous measurement
     * overrides.
     *
     * SSAS will auto-detect each column
     * using actual observation values.
     */

    setManualLevels({})


    const baseName =
      String(
        filename ||
        'Imported-Dataset'
      )
        .replace(
          /\.[^/.]+$/,
          ''
        )
        .trim()


    setNewDatasetName(
      baseName ||
      'Imported-Dataset'
    )


    setCalculationComplete(
      false
    )


    setSuccess(
      `Imported ${importedRows.length} cases and ${columnCount} variables into the SSAS form. Review the measurement levels and press Save Dataset when ready.`
    )
  }


  // ========================================================
  // IMPORT FROM MODAL
  // ========================================================

  const handleTransferImport = (
    matrix,
    filename
  ) => {
    /*
     * When importing while already on
     * /datasets/new, populate the form.
     */

    if (isNewDataset) {
      loadImportedFileIntoForm(
        matrix,
        filename
      )

      return
    }


    /*
     * If user imports while viewing an
     * existing dataset, switch to the
     * new-data form and carry the file
     * data through React Router state.
     */

    navigate(
      '/datasets/new',
      {
        state: {
          importedMatrix:
            matrix,

          importedFilename:
            filename,
        },
      }
    )
  }


  // ========================================================
  // RECEIVE IMPORT AFTER NAVIGATION
  // ========================================================

  useEffect(() => {
    if (
      !isNewDataset ||
      !location.state
        ?.importedMatrix
    ) {
      return
    }


    loadImportedFileIntoForm(
      location
        .state
        .importedMatrix,

      location
        .state
        .importedFilename
    )


    /*
     * Remove temporary router state
     * after it has been consumed.
     */

    navigate(
      '/datasets/new',
      {
        replace: true,
        state: null,
      }
    )

  }, [
    isNewDataset,
    location.state,
    navigate,
  ])


  // ========================================================
  // LOAD EXISTING DATASET
  // ========================================================

  useEffect(() => {
    if (!datasetId) {
      return
    }


    const loadWorkspace =
      async () => {
        setLoading(true)
        setError('')


        try {
          const [
            datasetResponse,
            dataResponse,
            variableResponse,
          ] =
            await Promise.all([
              api.get(
                `/datasets/${datasetId}`
              ),

              api.get(
                `/datasets/${datasetId}/data`,
                {
                  params: {
                    limit: 100,
                  },
                }
              ),

              api.get(
                `/datasets/${datasetId}/variables`
              ),
            ])


          setDataset(
            datasetResponse.data
          )


          setColumns(
            dataResponse
              .data
              .columns ||
            []
          )


          setPreviewRows(
            dataResponse
              .data
              .rows ||
            []
          )


          const variableData =
            variableResponse
              .data
              .variables ||
            []


          setVariables(
            variableData
          )


          const detected = {}


          variableData.forEach(
            (variable) => {
              detected[
                variable.name
              ] =
                variable
                  .measurement_level ||
                'nominal'
            }
          )


          setMeasurementLevels(
            detected
          )

        } catch (err) {
          setError(
            getErrorMessage(err)
          )

        } finally {
          setLoading(false)
        }
      }


    loadWorkspace()

  }, [datasetId])


  // ========================================================
  // VARIABLE GROUPS
  // ========================================================

  const usableVariables =
    useMemo(
      () =>
        variables.filter(
          (variable) => {
            const role =
              variable.semantic_role

            return (
              role !== 'datetime' &&
              role !== 'identifier' &&
              role !== 'ignored'
            )
          }
        ),
      [variables]
    )


  const metricVariables =
    usableVariables.filter(
      (variable) =>
        measurementLevels[
          variable.name
        ] === 'metric'
    )


  const ordinalVariables =
    usableVariables.filter(
      (variable) =>
        measurementLevels[
          variable.name
        ] === 'ordinal'
    )


  const nominalVariables =
    usableVariables.filter(
      (variable) =>
        measurementLevels[
          variable.name
        ] === 'nominal'
    )


  // ========================================================
  // EXISTING DATASET MEASUREMENT LEVEL
  // ========================================================

  const updateMeasurementLevel =
    async (
      column,
      newLevel
    ) => {
      setMeasurementLevels(
        (previous) => ({
          ...previous,
          [column]:
            newLevel,
        })
      )


      try {
        await api.patch(
          `/datasets/${datasetId}/variables/${encodeURIComponent(column)}`,
          {
            measurement_level:
              newLevel,
          }
        )


        setSuccess(
          `${column} set to ${newLevel}.`
        )

      } catch (err) {
        setError(
          getErrorMessage(err)
        )
      }
    }


  // ========================================================
  // UPDATE MANUAL CELL
  // ========================================================

  const updateManualCell = (
    rowIndex,
    columnIndex,
    value
  ) => {
    setManualRows(
      (previous) => {
        const copy =
          previous.map(
            (row) => [
              ...row,
            ]
          )


        copy[
          rowIndex
        ][
          columnIndex
        ] = value


        return copy
      }
    )
  }


  // ========================================================
  // UPDATE MANUAL HEADER
  // ========================================================

  const updateManualColumn = (
    columnIndex,
    value
  ) => {
    setManualColumns(
      (previous) =>
        previous.map(
          (column, index) =>
            index ===
            columnIndex
              ? value
              : column
        )
    )
  }


  // ========================================================
  // UPDATE MANUAL MEASUREMENT LEVEL
  // ========================================================

  const updateManualLevel = (
    columnIndex,
    value
  ) => {
    setManualLevels(
      (previous) => ({
        ...previous,

        [columnIndex]:
          value,
      })
    )
  }


  // ========================================================
  // ADD CASE
  // ========================================================

  const addManualRow = () => {
    setManualRows(
      (previous) => [
        ...previous,

        Array(
          manualColumns.length
        ).fill(''),
      ]
    )
  }


  // ========================================================
  // DELETE CASE
  // ========================================================

  const deleteManualRow = (
    rowIndex
  ) => {
    setManualRows(
      (previous) => {
        let next =
          previous.filter(
            (_, index) =>
              index !==
              rowIndex
          )


        if (!next.length) {
          next = [
            Array(
              manualColumns.length
            ).fill(''),
          ]
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

  const addManualColumn = () => {
    setManualColumns(
      (previous) => [
        ...previous,
        '',
      ]
    )


    setManualRows(
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
  // PASTE COMPLETE TABLE INTO HEADER
  // ========================================================

  const pasteDatasetFromHeader = (
    event,
    startColumnIndex
  ) => {
    event.preventDefault()

    setError('')
    setSuccess('')


    const clipboardText =
      event.clipboardData
        .getData(
          'text/plain'
        )


    const matrix =
      parseClipboardData(
        clipboardText
      )


    if (!matrix.length) {
      return
    }


    const pastedHeaders =
      matrix[0]

    const pastedData =
      matrix.slice(1)


    const maximumWidth =
      Math.max(
        ...matrix.map(
          (row) =>
            row.length
        )
      )


    const requiredColumns =
      startColumnIndex +
      maximumWidth


    const newColumns = [
      ...manualColumns,
    ]


    while (
      newColumns.length <
      requiredColumns
    ) {
      newColumns.push('')
    }


    pastedHeaders.forEach(
      (
        value,
        pastedColumnIndex
      ) => {
        const targetColumn =
          startColumnIndex +
          pastedColumnIndex


        newColumns[
          targetColumn
        ] =
          String(
            value ?? ''
          ).trim()
      }
    )


    const requiredRows =
      Math.max(
        manualRows.length,
        pastedData.length
      )


    const newRows =
      Array.from(
        {
          length:
            requiredRows,
        },
        (_, rowIndex) => {
          const existing =
            manualRows[
              rowIndex
            ] || []


          return Array.from(
            {
              length:
                newColumns.length,
            },
            (_, columnIndex) =>
              existing[
                columnIndex
              ] ?? ''
          )
        }
      )


    pastedData.forEach(
      (
        pastedRow,
        pastedRowIndex
      ) => {
        pastedRow.forEach(
          (
            value,
            pastedColumnIndex
          ) => {
            const targetColumn =
              startColumnIndex +
              pastedColumnIndex


            newRows[
              pastedRowIndex
            ][
              targetColumn
            ] = value
          }
        )
      }
    )


    setManualColumns(
      newColumns
    )

    setManualRows(
      newRows
    )

    setManualLevels({})


    setSuccess(
      `Pasted ${pastedData.length} cases and ${pastedHeaders.length} variables. Measurement levels were automatically detected.`
    )
  }


  // ========================================================
  // PASTE INTO DATA CELLS
  // ========================================================

  const pasteIntoDataCells = (
    event,
    startRowIndex,
    startColumnIndex
  ) => {
    const headersAreBlank =
      manualColumns.every(
        (column) =>
          String(
            column
          ).trim() === ''
      )


    /*
     * When pasting a complete table
     * into Case 1 of a blank form,
     * use first row as headers.
     */

    if (
      startRowIndex === 0 &&
      headersAreBlank
    ) {
      pasteDatasetFromHeader(
        event,
        startColumnIndex
      )

      return
    }


    event.preventDefault()

    setError('')
    setSuccess('')


    const clipboardText =
      event.clipboardData
        .getData(
          'text/plain'
        )


    const matrix =
      parseClipboardData(
        clipboardText
      )


    if (!matrix.length) {
      return
    }


    const maximumWidth =
      Math.max(
        ...matrix.map(
          (row) =>
            row.length
        )
      )


    const requiredColumns =
      startColumnIndex +
      maximumWidth


    const newColumns = [
      ...manualColumns,
    ]


    while (
      newColumns.length <
      requiredColumns
    ) {
      newColumns.push('')
    }


    const requiredRows =
      Math.max(
        manualRows.length,

        startRowIndex +
        matrix.length
      )


    const newRows =
      Array.from(
        {
          length:
            requiredRows,
        },
        (_, rowIndex) => {
          const existing =
            manualRows[
              rowIndex
            ] || []


          return Array.from(
            {
              length:
                newColumns.length,
            },
            (_, columnIndex) =>
              existing[
                columnIndex
              ] ?? ''
          )
        }
      )


    matrix.forEach(
      (
        pastedRow,
        pastedRowIndex
      ) => {
        pastedRow.forEach(
          (
            value,
            pastedColumnIndex
          ) => {
            const targetRow =
              startRowIndex +
              pastedRowIndex


            const targetColumn =
              startColumnIndex +
              pastedColumnIndex


            newRows[
              targetRow
            ][
              targetColumn
            ] = value
          }
        )
      }
    )


    setManualColumns(
      newColumns
    )

    setManualRows(
      newRows
    )


    setSuccess(
      `${matrix.length} case(s) pasted into the spreadsheet.`
    )
  }


  // ========================================================
  // SAVE MANUAL DATASET
  // ========================================================

  const saveManualDataset =
    async () => {
      setSaving(true)
      setError('')
      setSuccess('')


      try {
        const headers =
          manualColumns.map(
            (column, index) => {
              const clean =
                String(
                  column
                ).trim()

              return (
                clean ||
                `Column${index + 1}`
              )
            }
          )


        const normalizedHeaders =
          headers.map(
            (header) =>
              header
                .trim()
                .toLowerCase()
          )


        if (
          new Set(
            normalizedHeaders
          ).size !==
          normalizedHeaders.length
        ) {
          throw new Error(
            'Variable names must be unique.'
          )
        }


        const dataRows =
          manualRows.filter(
            (row) =>
              row.some(
                (value) =>
                  String(
                    value
                  ).trim() !== ''
              )
          )


        if (!dataRows.length) {
          throw new Error(
            'Enter at least one row before saving.'
          )
        }


        const csv = [
          headers
            .map(escapeCSV)
            .join(','),

          ...dataRows.map(
            (row) =>
              headers
                .map(
                  (_, index) =>
                    escapeCSV(
                      row[index] ?? ''
                    )
                )
                .join(',')
          ),
        ].join('\n')


        let filename =
          newDatasetName.trim()


        if (!filename) {
          filename =
            'New-SSAS-Dataset'
        }


        if (
          !filename
            .toLowerCase()
            .endsWith('.csv')
        ) {
          filename += '.csv'
        }


        const file =
          new File(
            [csv],
            filename,
            {
              type: 'text/csv',
            }
          )


        const formData =
          new FormData()


        formData.append(
          'file',
          file
        )


        const response =
          await api.post(
            '/datasets/upload',
            formData
          )


        const newDatasetId =
          response.data.id


        /*
         * Save Metric / Ordinal /
         * Nominal classifications.
         */

        for (
          let index = 0;
          index <
          headers.length;
          index += 1
        ) {
          const column =
            headers[index]


          const automaticLevel =
            detectManualLevel(
              dataRows.map(
                (row) =>
                  row[index]
              )
            )


          const level =
            manualLevels[index] ||
            automaticLevel


          await api.patch(
            `/datasets/${newDatasetId}/variables/${encodeURIComponent(column)}`,
            {
              measurement_level:
                level,
            }
          )
        }


        navigate(
          `/datasets/${newDatasetId}/workspace`
        )

      } catch (err) {
        setError(
          getErrorMessage(err)
        )

      } finally {
        setSaving(false)
      }
    }


  // ========================================================
  // SELECT VARIABLE
  // ========================================================

  const toggleVariable = (
    column
  ) => {
    setSelectedVariables(
      (previous) =>
        previous.includes(
          column
        )
          ? previous.filter(
              (item) =>
                item !==
                column
            )
          : [
              ...previous,
              column,
            ]
    )


    setCalculationComplete(
      false
    )
  }


  // ========================================================
  // CALCULATE DESCRIPTIVE STATISTICS
  // ========================================================

  const calculateDescriptive =
    async () => {
      if (
        !selectedVariables.length
      ) {
        setError(
          'Select at least one Metric variable.'
        )

        return
      }


      const selectedMetric =
        selectedVariables.filter(
          (column) =>
            measurementLevels[
              column
            ] === 'metric'
        )


      if (
        !selectedMetric.length
      ) {
        setError(
          'Descriptive numerical statistics require at least one Metric variable.'
        )

        return
      }


      setCalculating(true)
      setError('')
      setSuccess('')


      try {
        const [
          statisticsResponse,
          rowsResponse,
        ] =
          await Promise.all([
            api.get(
              `/statistics/descriptive/${datasetId}`
            ),

            api.get(
              `/datasets/${datasetId}/data`,
              {
                params: {
                  limit: 5000,
                },
              }
            ),
          ])


        const allResults =
          statisticsResponse
            .data
            .results ||
          {}


        const filteredResults = {}


        selectedMetric.forEach(
          (column) => {
            if (
              allResults[column]
            ) {
              filteredResults[
                column
              ] =
                allResults[column]
            }
          }
        )


        setDescriptiveResults(
          filteredResults
        )


        setFullRows(
          rowsResponse
            .data
            .rows ||
          []
        )


        setCalculationComplete(
          true
        )


        setSuccess(
          'Descriptive analysis completed successfully.'
        )

      } catch (err) {
        setError(
          getErrorMessage(err)
        )

      } finally {
        setCalculating(false)
      }
    }


  // ========================================================
  // FORMAT RESULT
  // ========================================================

  const resultValue = (
    result,
    key
  ) => {
    if (
      key ===
      'confidence_interval_95'
    ) {
      const interval =
        result[
          'confidence_interval_95'
        ]


      if (!interval) {
        return '—'
      }


      return (
        `${formatNumber(
          interval.lower
        )} – ${formatNumber(
          interval.upper
        )}`
      )
    }


    return formatNumber(
      result[key]
    )
  }


  // ========================================================
  // EXPORT ROWS FOR MODAL
  // ========================================================

  const transferExportRows =
    isNewDataset
      ? manualRows
      : columns.length
        ? previewRows.map(
            (row) =>
              columns.map(
                (column) =>
                  row[column] ?? ''
              )
          )
        : []


  // ========================================================
  // RENDER
  // ========================================================

  return (
    <AppShell>

      <div className="ssas-workspace">

        {/* ==================================================
            HEADER
        ================================================== */}

        <div className="ssas-workspace-header">

          <div>

            <span className="workspace-eyebrow">
              SSAS DATA WORKSPACE
            </span>


            <h1>
              {isNewDataset
                ? 'Enter New Data'
                : dataset
                    ?.original_filename ||
                  'Dataset Workspace'}
            </h1>


            <p>
              Enter, import, classify,
              analyse and visualize data
              in one workspace.
            </p>

          </div>


          <button
            className="workspace-secondary-button"
            onClick={() =>
              navigate(
                '/datasets'
              )
            }
          >
            <ArrowLeft size={16} />

            Back to Datasets
          </button>

        </div>


        {/* ==================================================
            ALERTS
        ================================================== */}

        {error && (
          <div className="workspace-alert error">
            {error}
          </div>
        )}


        {success && (
          <div className="workspace-alert success">
            {success}
          </div>
        )}


        {/* ==================================================
            TOP MENU
        ================================================== */}

        <div className="workspace-menu">

          <button
            className={
              isNewDataset
                ? 'workspace-menu-item active'
                : 'workspace-menu-item'
            }
            onClick={() =>
              navigate(
                '/datasets/new'
              )
            }
          >
            <FilePlus2 size={16} />

            Enter New Data
          </button>


          <button
            type="button"
            className="workspace-menu-item"
            onClick={() =>
              setTransferModalOpen(
                true
              )
            }
          >
            <Upload size={16} />

            Export / Import
          </button>


          {!isNewDataset && (
            <button
              className="workspace-menu-item"
              onClick={() =>
                navigate(
                  `/datasets/${datasetId}/prepare`
                )
              }
            >
              <Sparkles size={16} />

              Prepare Data
            </button>
          )}

        </div>


        {/* ==================================================
            NEW DATA
        ================================================== */}

        {isNewDataset && (
          <div className="workspace-panel">

            <div className="panel-heading">

              <div>

                <h2>
                  Enter New Dataset
                </h2>

                <p>
                  Type directly into the spreadsheet,
                  paste cells, or import an Excel/CSV
                  file into the form.
                </p>

              </div>

            </div>


            <label className="dataset-name-field">

              Dataset Name

              <input
                value={newDatasetName}
                onChange={(event) =>
                  setNewDatasetName(
                    event.target.value
                  )
                }
              />

            </label>


            <div className="spreadsheet-paste-message">

              <strong>
                Paste directly into the table
              </strong>

              <span>
                Copy a table from Excel,
                click the first empty heading
                or first data cell and press{' '}
                <b>Ctrl + V</b>.
                You can also use{' '}
                <b>Export / Import</b>
                above.
              </span>

            </div>


            <div className="spreadsheet-container">

              <table className="ssas-spreadsheet">

                <thead>

                  {/* MEASUREMENT LEVEL */}

                  <tr className="level-row">

                    <th>
                      Level
                    </th>


                    {manualColumns.map(
                      (
                        column,
                        columnIndex
                      ) => {
                        const automatic =
                          detectManualLevel(
                            manualRows.map(
                              (row) =>
                                row[
                                  columnIndex
                                ]
                            )
                          )


                        const selectedLevel =
                          manualLevels[
                            columnIndex
                          ] ||
                          automatic


                        return (
                          <th
                            key={
                              columnIndex
                            }
                          >

                            <select
                              value={
                                selectedLevel
                              }
                              title={
                                `Automatically detected as ${automatic}`
                              }
                              onChange={(event) =>
                                updateManualLevel(
                                  columnIndex,
                                  event.target.value
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

                          </th>
                        )
                      }
                    )}

                  </tr>


                  {/* VARIABLE NAMES */}

                  <tr>

                    <th>
                      Case
                    </th>


                    {manualColumns.map(
                      (
                        column,
                        columnIndex
                      ) => (
                        <th
                          key={
                            columnIndex
                          }
                        >

                          <input
                            value={column}

                            placeholder={
                              `Column ${
                                columnIndex + 1
                              }`
                            }

                            title={
                              'Enter a variable name or paste an Excel/CSV table here.'
                            }

                            onChange={(event) =>
                              updateManualColumn(
                                columnIndex,
                                event.target.value
                              )
                            }

                            onPaste={(event) =>
                              pasteDatasetFromHeader(
                                event,
                                columnIndex
                              )
                            }
                          />

                        </th>
                      )
                    )}

                  </tr>

                </thead>


                <tbody>

                  {manualRows.map(
                    (
                      row,
                      rowIndex
                    ) => (
                      <tr
                        key={rowIndex}
                        className="manual-data-row"
                      >

                        {/* CASE / DELETE */}

                        <td className="case-column">

                          <div className="case-control">

                            <span className="case-number">
                              {rowIndex + 1}
                            </span>


                            <button
                              type="button"
                              className="case-delete-button"
                              title={
                                `Delete Case ${
                                  rowIndex + 1
                                }`
                              }
                              onClick={() =>
                                deleteManualRow(
                                  rowIndex
                                )
                              }
                            >
                              <Trash2 size={15} />
                            </button>

                          </div>

                        </td>


                        {/* DATA CELLS */}

                        {manualColumns.map(
                          (
                            _,
                            columnIndex
                          ) => (
                            <td
                              key={
                                columnIndex
                              }
                            >

                              <input
                                value={
                                  row[
                                    columnIndex
                                  ] ?? ''
                                }

                                onChange={(event) =>
                                  updateManualCell(
                                    rowIndex,
                                    columnIndex,
                                    event.target.value
                                  )
                                }

                                onPaste={(event) =>
                                  pasteIntoDataCells(
                                    event,
                                    rowIndex,
                                    columnIndex
                                  )
                                }
                              />

                            </td>
                          )
                        )}

                      </tr>
                    )
                  )}

                </tbody>

              </table>

            </div>


            <div className="spreadsheet-actions">

              <button
                className="workspace-secondary-button"
                onClick={
                  addManualRow
                }
              >
                <Plus size={15} />

                Add Row
              </button>


              <button
                className="workspace-secondary-button"
                onClick={
                  addManualColumn
                }
              >
                <Plus size={15} />

                Add Variable
              </button>


              <button
                className="workspace-primary-button"
                disabled={saving}
                onClick={
                  saveManualDataset
                }
              >
                <Save size={15} />

                {saving
                  ? 'Saving...'
                  : 'Save Dataset'}
              </button>

            </div>

          </div>
        )}


        {/* ==================================================
            EXISTING DATASET
        ================================================== */}

        {!isNewDataset && (
          <>

            <div className="workspace-panel">

              <div className="panel-heading">

                <div>

                  <h2>
                    Dataset
                  </h2>

                  <p>
                    SSAS automatically detected
                    measurement levels. Change any
                    classification if required.
                  </p>

                </div>


                <span className="dataset-summary">

                  {dataset?.row_count || 0}
                  {' '}rows

                  {' • '}

                  {dataset?.column_count || 0}
                  {' '}variables

                </span>

              </div>


              {loading ? (
                <div className="workspace-loading">
                  Loading dataset...
                </div>

              ) : (
                <div className="spreadsheet-container">

                  <table className="ssas-spreadsheet">

                    <thead>

                      <tr className="level-row">

                        <th>
                          Level
                        </th>


                        {columns.map(
                          (column) => (
                            <th
                              key={column}
                            >

                              <select
                                value={
                                  measurementLevels[
                                    column
                                  ] ||
                                  'nominal'
                                }
                                onChange={(event) =>
                                  updateMeasurementLevel(
                                    column,
                                    event.target.value
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

                            </th>
                          )
                        )}

                      </tr>


                      <tr>

                        <th>
                          Case
                        </th>


                        {columns.map(
                          (column) => (
                            <th
                              key={column}
                            >
                              {column}
                            </th>
                          )
                        )}

                      </tr>

                    </thead>


                    <tbody>

                      {previewRows.map(
                        (
                          row,
                          rowIndex
                        ) => (
                          <tr
                            key={
                              rowIndex
                            }
                          >

                            <td className="case-column">
                              {rowIndex + 1}
                            </td>


                            {columns.map(
                              (column) => (
                                <td
                                  key={column}
                                >
                                  {String(
                                    row[
                                      column
                                    ] ?? ''
                                  )}
                                </td>
                              )
                            )}

                          </tr>
                        )
                      )}

                    </tbody>

                  </table>

                </div>
              )}

            </div>


            {/* ==================================================
                ANALYSIS MENU
            ================================================== */}

            <div className="analysis-menu">

              {analysisMethods.map(
                (
                  method,
                  index
                ) => (
                  <button
                    key={method}
                    className={
                      index === 0
                        ? 'analysis-item active'
                        : 'analysis-item future'
                    }
                    disabled={
                      index !== 0
                    }
                  >
                    {method}
                  </button>
                )
              )}

            </div>


            {/* ==================================================
                DESCRIPTIVE
            ================================================== */}

            <div className="workspace-panel">

              <div className="descriptive-title">

                <BarChart3 size={20} />

                <div>

                  <h2>
                    Descriptive / Charts
                  </h2>

                  <p>
                    Select variables and statistics
                    to calculate.
                  </p>

                </div>

              </div>


              <div className="variable-groups">

                {/* METRIC */}

                <div className="variable-group">

                  <h3>
                    Metric Variables
                  </h3>


                  {metricVariables.length
                    ? metricVariables.map(
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

                            {variable.name}

                          </label>
                        )
                      )
                    : (
                      <p>
                        No Metric variables.
                      </p>
                    )}

                </div>


                {/* ORDINAL */}

                <div className="variable-group">

                  <h3>
                    Ordinal Variables
                  </h3>


                  {ordinalVariables.length
                    ? ordinalVariables.map(
                        (variable) => (
                          <span
                            key={
                              variable.name
                            }
                            className="variable-pill"
                          >
                            {variable.name}
                          </span>
                        )
                      )
                    : (
                      <p>
                        No Ordinal variables.
                      </p>
                    )}

                </div>


                {/* NOMINAL */}

                <div className="variable-group">

                  <h3>
                    Nominal Variables
                  </h3>


                  {nominalVariables.length
                    ? nominalVariables.map(
                        (variable) => (
                          <span
                            key={
                              variable.name
                            }
                            className="variable-pill"
                          >
                            {variable.name}
                          </span>
                        )
                      )
                    : (
                      <p>
                        No Nominal variables.
                      </p>
                    )}

                </div>

              </div>


              <div className="statistics-section">

                <h3>
                  Calculate
                </h3>


                <div className="statistics-options">

                  {statisticOptions.map(
                    ([
                      key,
                      label,
                    ]) => (
                      <label
                        key={key}
                      >

                        <input
                          type="checkbox"
                          checked={
                            selectedStatistics[
                              key
                            ] ||
                            false
                          }
                          onChange={(event) =>
                            setSelectedStatistics(
                              (previous) => ({
                                ...previous,

                                [key]:
                                  event.target.checked,
                              })
                            )
                          }
                        />

                        {label}

                      </label>
                    )
                  )}

                </div>


                <button
                  className="workspace-primary-button calculate-button"
                  disabled={
                    calculating
                  }
                  onClick={
                    calculateDescriptive
                  }
                >
                  <Sparkles size={16} />

                  {calculating
                    ? 'Calculating...'
                    : 'Calculate'}
                </button>

              </div>

            </div>


            {/* ==================================================
                RESULTS
            ================================================== */}

            {calculationComplete && (
              <div className="workspace-panel">

                <h2>
                  Descriptive Statistics
                </h2>


                {Object.entries(
                  descriptiveResults
                ).map(
                  ([
                    column,
                    result,
                  ]) => {
                    const values =
                      fullRows
                        .map(
                          (row) =>
                            Number(
                              row[column]
                            )
                        )
                        .filter(
                          Number.isFinite
                        )


                    return (
                      <div
                        key={column}
                        className="descriptive-result-block"
                      >

                        <h3>
                          {column}
                        </h3>


                        <div className="result-layout">

                          <table className="descriptive-result-table">

                            <tbody>

                              {statisticOptions
                                .filter(
                                  ([key]) =>
                                    selectedStatistics[
                                      key
                                    ]
                                )
                                .map(
                                  ([
                                    key,
                                    label,
                                  ]) => (
                                    <tr
                                      key={key}
                                    >

                                      <td>
                                        {label}
                                      </td>

                                      <td>
                                        {resultValue(
                                          result,
                                          key
                                        )}
                                      </td>

                                    </tr>
                                  )
                                )}

                            </tbody>

                          </table>


                          <div className="descriptive-chart">

                            <div className="chart-controls">

                              <label>

                                <input
                                  type="checkbox"
                                  checked={
                                    showNormalCurve
                                  }
                                  onChange={(event) =>
                                    setShowNormalCurve(
                                      event.target.checked
                                    )
                                  }
                                />

                                Normal Distribution

                              </label>

                            </div>


                            <Plot
                              data={(() => {
                                const traces = [
                                  {
                                    type:
                                      'histogram',

                                    x:
                                      values,

                                    histnorm:
                                      'probability density',

                                    name:
                                      column,
                                  },
                                ]


                                if (
                                  showNormalCurve &&
                                  values.length &&
                                  result
                                    .standard_deviation >
                                    0
                                ) {
                                  const minimum =
                                    Math.min(
                                      ...values
                                    )

                                  const maximum =
                                    Math.max(
                                      ...values
                                    )

                                  const mean =
                                    result.mean

                                  const sd =
                                    result
                                      .standard_deviation

                                  const pointCount =
                                    100

                                  const range =
                                    maximum -
                                    minimum

                                  const step =
                                    range === 0
                                      ? 1
                                      : range /
                                        (
                                          pointCount -
                                          1
                                        )


                                  const x =
                                    Array.from(
                                      {
                                        length:
                                          pointCount,
                                      },
                                      (
                                        _,
                                        index
                                      ) =>
                                        minimum +
                                        index *
                                          step
                                    )


                                  const y =
                                    x.map(
                                      (value) =>
                                        (
                                          1 /
                                          (
                                            sd *
                                            Math.sqrt(
                                              2 *
                                              Math.PI
                                            )
                                          )
                                        ) *
                                        Math.exp(
                                          -0.5 *
                                          Math.pow(
                                            (
                                              value -
                                              mean
                                            ) /
                                              sd,
                                            2
                                          )
                                        )
                                    )


                                  traces.push({
                                    type:
                                      'scatter',

                                    mode:
                                      'lines',

                                    x,
                                    y,

                                    name:
                                      'Normal distribution',
                                  })
                                }


                                return traces

                              })()}

                              layout={{
                                autosize: true,

                                height: 420,

                                title: {
                                  text:
                                    `Histogram — ${column}`,
                                },

                                xaxis: {
                                  title: {
                                    text:
                                      column,
                                  },
                                },

                                yaxis: {
                                  title: {
                                    text:
                                      'Probability Density',
                                  },
                                },

                                margin: {
                                  l: 60,
                                  r: 20,
                                  t: 60,
                                  b: 60,
                                },
                              }}

                              config={{
                                responsive: true,

                                displaylogo: false,

                                toImageButtonOptions: {
                                  format: 'png',

                                  filename:
                                    `${column}-histogram`,
                                },
                              }}

                              useResizeHandler

                              style={{
                                width: '100%',
                              }}
                            />

                          </div>

                        </div>

                      </div>
                    )
                  }
                )}

              </div>
            )}

          </>
        )}


        {/* ==================================================
            EXPORT / IMPORT MODAL
        ================================================== */}

        <DataTransferModal
          open={
            transferModalOpen
          }

          onClose={() =>
            setTransferModalOpen(
              false
            )
          }

          onImport={
            handleTransferImport
          }

          exportColumns={
            isNewDataset
              ? manualColumns
              : columns
          }

          exportRows={
            transferExportRows
          }

          datasetName={
            isNewDataset
              ? newDatasetName
              : dataset
                  ?.original_filename ||
                'SSAS-Dataset'
          }
        />

      </div>

    </AppShell>
  )
}
