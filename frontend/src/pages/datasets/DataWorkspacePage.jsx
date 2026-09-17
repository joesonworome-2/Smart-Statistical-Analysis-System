import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'

import {
  BarChart3,
  Check,
  Cloud,
  Download,
  FileSpreadsheet,
  Plus,
  Ruler,
  Trash2,
  Upload,
} from 'lucide-react'

import {
  useNavigate,
  useParams,
  useSearchParams,
} from 'react-router-dom'

import api
  from '../../api/api'

import AppShell
  from '../../components/AppShell'

import './DataWorkspacePage.css'


// ==========================================================
// CONFIGURATION
// ==========================================================

const DEFAULT_COLUMNS = 10

const DEFAULT_ROWS = 14

const AUTOSAVE_DELAY = 1000


// ==========================================================
// ERROR HELPER
// ==========================================================

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

  if (
    Array.isArray(
      detail
    )
  ) {
    return detail
      .map(
        (
          item
        ) =>
          item?.msg ||
          String(
            item
          )
      )
      .join(
        ', '
      )
  }

  return (
    error?.message ||
    'Something went wrong.'
  )
}


// ==========================================================
// CREATE EMPTY ROWS
// ==========================================================

function createRows(
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
// CSV LINE PARSER
// ==========================================================

function parseCSVLine(
  line
) {
  const values = []

  let current = ''

  let insideQuotes =
    false

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
        line[
          index + 1
        ] === '"'
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
      character === ',' &&
      !insideQuotes
    ) {
      values.push(
        current.trim()
      )

      current = ''

      continue
    }

    current +=
      character
  }

  values.push(
    current.trim()
  )

  return values
}


// ==========================================================
// CLIPBOARD PARSER
// ==========================================================

function parseClipboardData(
  text
) {
  const cleaned =
    String(
      text || ''
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
    cleaned.split(
      '\n'
    )

  while (
    lines.length &&
    !lines[
      lines.length - 1
    ].trim()
  ) {
    lines.pop()
  }

  const tabSeparated =
    cleaned.includes(
      '\t'
    )

  return lines.map(
    (
      line
    ) => {
      if (
        tabSeparated
      ) {
        return line
          .split(
            '\t'
          )
          .map(
            (
              value
            ) =>
              value.trim()
          )
      }

      return parseCSVLine(
        line
      )
    }
  )
}


// ==========================================================
// CSV EXPORT HELPER
// ==========================================================

function escapeCSV(
  value
) {
  const text =
    value === null ||
    value === undefined
      ? ''
      : String(
          value
        )

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

function detectMeasurementLevel(
  values
) {
  const clean =
    values
      .map(
        (
          value
        ) =>
          String(
            value ?? ''
          ).trim()
      )
      .filter(
        Boolean
      )

  if (
    !clean.length
  ) {
    return 'nominal'
  }

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

      'primary',
      'secondary',
      'tertiary',

      'beginner',
      'intermediate',
      'advanced',

      'bachelor',
      'master',
      'phd',

      'first',
      'second',
      'third',
      'fourth',
      'fifth',
    ])

  const normalized =
    clean.map(
      (
        value
      ) =>
        value.toLowerCase()
    )

  const allOrdinal =
    normalized.every(
      (
        value
      ) =>
        ordinalTerms.has(
          value
        )
    )

  if (
    allOrdinal
  ) {
    return 'ordinal'
  }

  const numeric =
    clean.every(
      (
        value
      ) =>
        value !== '' &&
        !Number.isNaN(
          Number(
            value
          )
        )
    )

  if (
    numeric
  ) {
    const uniqueCount =
      new Set(
        clean
      ).size

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
// NORMALIZE SPREADSHEET
// ==========================================================

function normalizeGrid(
  columns,
  rows
) {
  const usedIndexes =
    columns
      .map(
        (
          _,
          index
        ) =>
          index
      )
      .filter(
        (
          columnIndex
        ) => {
          const header =
            String(
              columns[
                columnIndex
              ] ?? ''
            ).trim()

          const hasData =
            rows.some(
              (
                row
              ) =>
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
      )

  if (
    !usedIndexes.length
  ) {
    throw new Error(
      'Enter at least one variable before saving the dataset.'
    )
  }

  const headers =
    usedIndexes.map(
      (
        columnIndex,
        index
      ) => {
        const current =
          String(
            columns[
              columnIndex
            ] ?? ''
          ).trim()

        return (
          current ||
          `Variable${index + 1}`
        )
      }
    )

  const dataRows =
    rows
      .filter(
        (
          row
        ) =>
          usedIndexes.some(
            (
              columnIndex
            ) =>
              String(
                row?.[
                  columnIndex
                ] ?? ''
              ).trim() !== ''
          )
      )
      .map(
        (
          row
        ) =>
          usedIndexes.map(
            (
              columnIndex
            ) =>
              row?.[
                columnIndex
              ] ?? ''
          )
      )

  if (
    !dataRows.length
  ) {
    throw new Error(
      'Enter at least one data row before saving.'
    )
  }

  const records =
    dataRows.map(
      (
        row
      ) => {
        const record = {}

        headers.forEach(
          (
            header,
            index
          ) => {
            record[
              header
            ] =
              row[
                index
              ] ?? ''
          }
        )

        return record
      }
    )

  return {
    headers,
    dataRows,
    records,
    usedIndexes,
  }
}


// ==========================================================
// MEASUREMENT LEVEL ICON
// ==========================================================

function MeasurementIcon({
  level,
}) {
  if (
    level ===
    'metric'
  ) {
    return (
      <Ruler
        size={14}
        strokeWidth={2.1}
      />
    )
  }

  if (
    level ===
    'ordinal'
  ) {
    return (
      <BarChart3
        size={14}
        strokeWidth={2.1}
      />
    )
  }

  return (
    <span
      className="measurement-nominal-icon"
      aria-hidden="true"
    >
      <i />
      <i />
      <i />
    </span>
  )
}


// ==========================================================
// DATA WORKSPACE
// ==========================================================

export default function DataWorkspacePage() {
  const {
    datasetId,
  } = useParams()

  const [
    searchParams,
  ] = useSearchParams()

  const navigate =
    useNavigate()

  const fileInputRef =
    useRef(null)

  const autosaveTimerRef =
    useRef(null)

  const loadedRef =
    useRef(false)

  const saveInProgressRef =
    useRef(false)


  // ========================================================
  // CURRENT WORKFLOW
  // ========================================================

  const isNew =
    !datasetId

  const requestedMethod =
    searchParams.get(
      'method'
    ) ||
    'descriptive'

  const selectedMethod =
    searchParams.get(
      'selected'
    ) ||
    ''


  // ========================================================
  // DATASET STATE
  // ========================================================

  const [
    dataset,
    setDataset,
  ] = useState(null)

  const [
    datasetName,
    setDatasetName,
  ] = useState(
    'New-SSAS-Dataset'
  )

  const [
    columns,
    setColumns,
  ] = useState(
    Array(
      DEFAULT_COLUMNS
    ).fill('')
  )

  const [
    rows,
    setRows,
  ] = useState(
    createRows(
      DEFAULT_ROWS,
      DEFAULT_COLUMNS
    )
  )

  const [
    measurementLevels,
    setMeasurementLevels,
  ] = useState({})

  const [
    activeCell,
    setActiveCell,
  ] = useState({
    area:
      'header',

    rowIndex:
      0,

    columnIndex:
      0,
  })


  // ========================================================
  // SAVED DATASETS
  // ========================================================

  const [
    savedDatasets,
    setSavedDatasets,
  ] = useState([])

  const [
    loadingSavedDatasets,
    setLoadingSavedDatasets,
  ] = useState(false)


  // ========================================================
  // PAGE STATE
  // ========================================================

  const [
    loading,
    setLoading,
  ] = useState(
    !isNew
  )

  const [
    saving,
    setSaving,
  ] = useState(false)

  const [
    uploading,
    setUploading,
  ] = useState(false)

  const [
    saveState,
    setSaveState,
  ] = useState(
    isNew
      ? 'ready'
      : 'loading'
  )

  const [
    error,
    setError,
  ] = useState('')

  const [
    success,
    setSuccess,
  ] = useState('')

  const [
    transferOpen,
    setTransferOpen,
  ] = useState(false)

  const [
    settingsOpen,
    setSettingsOpen,
  ] = useState(false)


  // ========================================================
  // WORKFLOW QUERY
  // ========================================================

  const workflowQuery =
    () => {
      const params =
        new URLSearchParams()

      params.set(
        'method',
        requestedMethod
      )

      if (
        selectedMethod
      ) {
        params.set(
          'selected',
          selectedMethod
        )
      }

      return params.toString()
    }


  // ========================================================
  // NAVIGATE TO PREPARE
  // ========================================================

  const goToPrepare =
    (
      id
    ) => {
      navigate(
        `/datasets/${id}/prepare?${workflowQuery()}`
      )
    }


  // ========================================================
  // OPEN SAVED DATASET
  // ========================================================

  const openSavedDataset =
    (
      id
    ) => {
      setTransferOpen(
        false
      )

      navigate(
        `/datasets/${id}/workspace?${workflowQuery()}`
      )
    }


  // ========================================================
  // LOAD SAVED DATASETS
  // ========================================================

  const loadSavedDatasets =
    async () => {
      setLoadingSavedDatasets(
        true
      )

      try {
        const response =
          await api.get(
            '/datasets'
          )

        setSavedDatasets(
          response
            .data
            ?.datasets ||
          []
        )

      } catch (
        err
      ) {
        console.error(
          'Unable to load saved datasets:',
          err
        )

      } finally {
        setLoadingSavedDatasets(
          false
        )
      }
    }


  useEffect(
    () => {
      loadSavedDatasets()
    },
    []
  )


  // ========================================================
  // RESET TO NEW DATASET
  // ========================================================

  const resetNewSheet =
    () => {
      if (
        autosaveTimerRef.current
      ) {
        window.clearTimeout(
          autosaveTimerRef.current
        )
      }

      loadedRef.current =
        false

      setDataset(
        null
      )

      setDatasetName(
        'New-SSAS-Dataset'
      )

      setColumns(
        Array(
          DEFAULT_COLUMNS
        ).fill('')
      )

      setRows(
        createRows(
          DEFAULT_ROWS,
          DEFAULT_COLUMNS
        )
      )

      setMeasurementLevels(
        {}
      )

      setActiveCell({
        area:
          'header',

        rowIndex:
          0,

        columnIndex:
          0,
      })

      setSaveState(
        'ready'
      )

      setError(
        ''
      )

      setSuccess(
        ''
      )
    }


  // ========================================================
  // ENTER NEW DATA
  // ========================================================

  const enterNewData =
    () => {
      resetNewSheet()

      setTransferOpen(
        false
      )

      setSettingsOpen(
        false
      )

      if (
        datasetId
      ) {
        navigate(
          `/datasets?${workflowQuery()}`
        )
      }
    }


  // ========================================================
  // LOAD EXISTING DATASET
  // ========================================================

  const loadExistingDataset =
    async () => {
      if (
        isNew
      ) {
        resetNewSheet()

        return
      }

      setLoading(
        true
      )

      setError(
        ''
      )

      loadedRef.current =
        false

      try {
        const [
          datasetResponse,
          variableResponse,
        ] =
          await Promise.all([
            api.get(
              `/datasets/${datasetId}`
            ),

            api.get(
              `/datasets/${datasetId}/variables`
            ),
          ])

        const allRows = []

        let loadedColumns = []

        let offset = 0

        const limit = 5000

        let hasMore = true

        while (
          hasMore
        ) {
          const response =
            await api.get(
              `/datasets/${datasetId}/data`,
              {
                params: {
                  offset,
                  limit,
                },
              }
            )

          const pageData =
            response.data ||
            {}

          if (
            !loadedColumns.length
          ) {
            loadedColumns =
              pageData.columns ||
              []
          }

          allRows.push(
            ...(
              pageData.rows ||
              []
            )
          )

          const returnedRows =
            pageData.returned_rows ??
            pageData.rows?.length ??
            0

          hasMore =
            Boolean(
              pageData.has_more
            )

          offset +=
            returnedRows

          if (
            !returnedRows
          ) {
            break
          }
        }

        if (
          !loadedColumns.length
        ) {
          loadedColumns =
            datasetResponse
              .data
              ?.columns ||
            []
        }

        const visibleColumnCount =
          Math.max(
            loadedColumns.length,
            DEFAULT_COLUMNS
          )

        const paddedColumns =
          Array.from(
            {
              length:
                visibleColumnCount,
            },
            (
              _,
              index
            ) =>
              loadedColumns[
                index
              ] ??
              ''
          )

        const gridRows =
          allRows.map(
            (
              record
            ) =>
              paddedColumns.map(
                (
                  column
                ) => {
                  if (
                    !column
                  ) {
                    return ''
                  }

                  return (
                    record?.[
                      column
                    ] ??
                    ''
                  )
                }
              )
          )

        const minimumRows =
          Math.max(
            gridRows.length +
              4,
            DEFAULT_ROWS
          )

        const paddedRows =
          Array.from(
            {
              length:
                minimumRows,
            },
            (
              _,
              index
            ) =>
              gridRows[
                index
              ] ||
              Array(
                visibleColumnCount
              ).fill('')
          )

        setDataset(
          datasetResponse.data
        )

        setDatasetName(
          String(
            datasetResponse
              .data
              ?.original_filename ||
            datasetResponse
              .data
              ?.filename ||
            'Dataset'
          ).replace(
            /\.[^/.]+$/,
            ''
          )
        )

        setColumns(
          paddedColumns
        )

        setRows(
          paddedRows
        )

        const levels = {}

        const variables =
          variableResponse
            .data
            ?.variables ||
          []

        variables.forEach(
          (
            variable
          ) => {
            levels[
              variable.name
            ] =
              variable
                .measurement_level ||
              'nominal'
          }
        )

        setMeasurementLevels(
          levels
        )

        setSaveState(
          'saved'
        )

        window.setTimeout(
          () => {
            loadedRef.current =
              true
          },
          150
        )

      } catch (
        err
      ) {
        setError(
          getErrorMessage(
            err
          )
        )

        setSaveState(
          'failed'
        )

      } finally {
        setLoading(
          false
        )
      }
    }


  useEffect(
    () => {
      loadExistingDataset()

      return () => {
        if (
          autosaveTimerRef.current
        ) {
          window.clearTimeout(
            autosaveTimerRef.current
          )
        }
      }
    },
    [
      datasetId,
    ]
  )


  // ========================================================
  // SAVE MEASUREMENT LEVELS
  // ========================================================

  const saveMeasurementLevels =
    async (
      id,
      headers,
      dataRows
    ) => {
      for (
        let index = 0;
        index < headers.length;
        index += 1
      ) {
        const header =
          headers[
            index
          ]

        const detected =
          detectMeasurementLevel(
            dataRows.map(
              (
                row
              ) =>
                row[
                  index
                ]
            )
          )

        const level =
          measurementLevels[
            header
          ] ||
          detected

        try {
          await api.patch(
            `/datasets/${id}/variables/${encodeURIComponent(header)}`,
            {
              measurement_level:
                level,
            }
          )

        } catch (
          err
        ) {
          console.warn(
            `Unable to save measurement level for ${header}`,
            err
          )
        }
      }
    }


  // ========================================================
  // UPLOAD A GRID AS A NEW DATASET
  // ========================================================

  const uploadGrid =
    async (
      gridColumns,
      gridRows,
      {
        redirect = true,
      } = {}
    ) => {
      if (
        saveInProgressRef.current
      ) {
        return null
      }

      saveInProgressRef.current =
        true

      setSaving(
        true
      )

      setSaveState(
        'saving'
      )

      setError(
        ''
      )

      try {
        const normalized =
          normalizeGrid(
            gridColumns,
            gridRows
          )

        const csv = [
          normalized
            .headers
            .map(
              escapeCSV
            )
            .join(','),

          ...normalized
            .dataRows
            .map(
              (
                row
              ) =>
                row
                  .map(
                    escapeCSV
                  )
                  .join(',')
            ),
        ].join(
          '\n'
        )

        let filename =
          datasetName.trim() ||
          'New-SSAS-Dataset'

        if (
          !filename
            .toLowerCase()
            .endsWith(
              '.csv'
            )
        ) {
          filename +=
            '.csv'
        }

        const file =
          new File(
            [
              csv,
            ],
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

        const response =
          await api.post(
            '/datasets/upload',
            formData
          )

        const newId =
          response
            .data
            ?.id

        if (
          !newId
        ) {
          throw new Error(
            'SSAS did not return the new dataset ID.'
          )
        }

        await saveMeasurementLevels(
          newId,
          normalized.headers,
          normalized.dataRows
        )

        setSaveState(
          'saved'
        )

        await loadSavedDatasets()

        if (
          redirect
        ) {
          goToPrepare(
            newId
          )
        }

        return newId

      } catch (
        err
      ) {
        setSaveState(
          'failed'
        )

        setError(
          getErrorMessage(
            err
          )
        )

        return null

      } finally {
        setSaving(
          false
        )

        saveInProgressRef.current =
          false
      }
    }


  // ========================================================
  // CREATE CURRENT NEW DATASET
  // ========================================================

  const createDataset =
    async (
      {
        redirect = true,
      } = {}
    ) => {
      return uploadGrid(
        columns,
        rows,
        {
          redirect,
        }
      )
    }


  // ========================================================
  // SAVE GRID DIRECTLY TO EXISTING DATASET
  // ========================================================

  const saveGridToExisting =
    async (
      id,
      gridColumns,
      gridRows,
      {
        silent = false,
      } = {}
    ) => {
      if (
        saveInProgressRef.current
      ) {
        return false
      }

      saveInProgressRef.current =
        true

      setSaving(
        true
      )

      setSaveState(
        'saving'
      )

      if (
        !silent
      ) {
        setError(
          ''
        )

        setSuccess(
          ''
        )
      }

      try {
        const normalized =
          normalizeGrid(
            gridColumns,
            gridRows
          )

        await api.put(
          `/datasets/${id}/data`,
          {
            columns:
              normalized.headers,

            rows:
              normalized.records,
          }
        )

        await saveMeasurementLevels(
          id,
          normalized.headers,
          normalized.dataRows
        )

        setSaveState(
          'saved'
        )

        if (
          !silent
        ) {
          setSuccess(
            'Dataset saved.'
          )
        }

        return true

      } catch (
        err
      ) {
        setSaveState(
          'failed'
        )

        if (
          !silent
        ) {
          setError(
            getErrorMessage(
              err
            )
          )
        }

        return false

      } finally {
        setSaving(
          false
        )

        saveInProgressRef.current =
          false
      }
    }


  // ========================================================
  // SAVE CURRENT EXISTING DATASET
  // ========================================================

  const saveExistingDataset =
    async (
      {
        silent = false,
      } = {}
    ) => {
      if (
        !datasetId
      ) {
        return false
      }

      return saveGridToExisting(
        datasetId,
        columns,
        rows,
        {
          silent,
        }
      )
    }


  // ========================================================
  // AUTOSAVE EXISTING DATASET
  // ========================================================

  useEffect(
    () => {
      if (
        isNew ||
        !loadedRef.current ||
        loading
      ) {
        return
      }

      setSaveState(
        'unsaved'
      )

      if (
        autosaveTimerRef.current
      ) {
        window.clearTimeout(
          autosaveTimerRef.current
        )
      }

      autosaveTimerRef.current =
        window.setTimeout(
          () => {
            saveExistingDataset({
              silent:
                true,
            })
          },
          AUTOSAVE_DELAY
        )

      return () => {
        if (
          autosaveTimerRef.current
        ) {
          window.clearTimeout(
            autosaveTimerRef.current
          )
        }
      }
    },
    [
      columns,
      rows,
      measurementLevels,
    ]
  )


  // ========================================================
  // UPDATE DATA CELL
  // ========================================================

  const updateCell =
    (
      rowIndex,
      columnIndex,
      value
    ) => {
      setRows(
        (
          previous
        ) => {
          const next =
            previous.map(
              (
                row
              ) => [
                ...row,
              ]
            )

          if (
            !next[
              rowIndex
            ]
          ) {
            next[
              rowIndex
            ] =
              Array(
                columns.length
              ).fill('')
          }

          next[
            rowIndex
          ][
            columnIndex
          ] =
            value

          return next
        }
      )
    }


  // ========================================================
  // UPDATE VARIABLE NAME
  // ========================================================

  const updateColumn =
    (
      columnIndex,
      value
    ) => {
      setColumns(
        (
          previous
        ) =>
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

  const updateMeasurementLevel =
    (
      column,
      value
    ) => {
      if (
        !column
      ) {
        return
      }

      setMeasurementLevels(
        (
          previous
        ) => ({
          ...previous,

          [column]:
            value,
        })
      )
    }


  // ========================================================
  // ADD CASE
  // ========================================================

  const addRow =
    () => {
      setRows(
        (
          previous
        ) => [
          ...previous,

          Array(
            columns.length
          ).fill(''),
        ]
      )
    }


  // ========================================================
  // DELETE CASE
  // ========================================================

  const deleteRow =
    (
      rowIndex
    ) => {
      setRows(
        (
          previous
        ) => {
          const next =
            previous.filter(
              (
                _,
                index
              ) =>
                index !==
                rowIndex
            )

          if (
            next.length
          ) {
            return next
          }

          return [
            Array(
              columns.length
            ).fill(''),
          ]
        }
      )
    }


  // ========================================================
  // ADD VARIABLE
  // ========================================================

  const addColumn =
    () => {
      setColumns(
        (
          previous
        ) => [
          ...previous,
          '',
        ]
      )

      setRows(
        (
          previous
        ) =>
          previous.map(
            (
              row
            ) => [
              ...row,
              '',
            ]
          )
      )
    }


  // ========================================================
  // FULL DATASET PASTE
  // ========================================================

  const applyFullDatasetPaste =
    async (
      matrix
    ) => {
      if (
        matrix.length <
        2
      ) {
        setError(
          'Paste a header row and at least one data row.'
        )

        return
      }

      const headerRow =
        matrix[
          0
        ] ||
        []

      const dataRows =
        matrix
          .slice(
            1
          )
          .filter(
            (
              row
            ) =>
              Array.isArray(
                row
              ) &&
              row.some(
                (
                  value
                ) =>
                  String(
                    value ?? ''
                  ).trim() !== ''
              )
          )

      const widths =
        dataRows.map(
          (
            row
          ) =>
            row.length
        )

      const width =
        Math.max(
          headerRow.length,
          ...widths,
          0
        )

      if (
        !width ||
        !dataRows.length
      ) {
        setError(
          'No complete dataset was found in the pasted content.'
        )

        return
      }

      const visibleWidth =
        Math.max(
          width,
          DEFAULT_COLUMNS
        )

      const nextColumns =
        Array.from(
          {
            length:
              visibleWidth,
          },
          (
            _,
            index
          ) =>
            index < width
              ? String(
                  headerRow[
                    index
                  ] ?? ''
                ).trim()
              : ''
        )

      const nextDataRows =
        dataRows.map(
          (
            sourceRow
          ) =>
            Array.from(
              {
                length:
                  visibleWidth,
              },
              (
                _,
                index
              ) =>
                index < width
                  ? String(
                      sourceRow[
                        index
                      ] ?? ''
                    )
                  : ''
            )
        )

      const nextRows = [
        ...nextDataRows,

        ...createRows(
          4,
          visibleWidth
        ),
      ]

      setColumns(
        nextColumns
      )

      setRows(
        nextRows
      )

      setMeasurementLevels(
        {}
      )

      setError(
        ''
      )

      setSuccess(
        `Pasted ${nextDataRows.length} cases and ${width} variables.`
      )

      // ------------------------------------------------------
      // NEW DATASET:
      // save immediately and continue to preparation
      // ------------------------------------------------------

      if (
        isNew
      ) {
        await uploadGrid(
          nextColumns,
          nextRows,
          {
            redirect:
              true,
          }
        )

        return
      }

      // ------------------------------------------------------
      // EXISTING DATASET:
      // replace data, save and continue to preparation
      // ------------------------------------------------------

      const saved =
        await saveGridToExisting(
          datasetId,
          nextColumns,
          nextRows
        )

      if (
        saved
      ) {
        goToPrepare(
          datasetId
        )
      }
    }


  // ========================================================
  // PASTE INTO CELLS
  // ========================================================

  const applyCellPaste =
    (
      matrix,
      startRow,
      startColumn
    ) => {
      if (
        !matrix.length
      ) {
        return
      }

      const widths =
        matrix.map(
          (
            row
          ) =>
            Array.isArray(
              row
            )
              ? row.length
              : 0
        )

      const width =
        Math.max(
          ...widths,
          0
        )

      if (
        !width
      ) {
        return
      }

      const requiredColumns =
        Math.max(
          columns.length,

          startColumn +
            width
        )

      const requiredRows =
        Math.max(
          rows.length,

          startRow +
            matrix.length
        )

      const nextColumns =
        Array.from(
          {
            length:
              requiredColumns,
          },
          (
            _,
            index
          ) =>
            columns[
              index
            ] ??
            ''
        )

      const nextRows =
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
                rows?.[
                  rowIndex
                ]?.[
                  columnIndex
                ] ??
                ''
            )
        )

      matrix.forEach(
        (
          sourceRow,
          rowOffset
        ) => {
          sourceRow.forEach(
            (
              value,
              columnOffset
            ) => {
              nextRows[
                startRow +
                rowOffset
              ][
                startColumn +
                columnOffset
              ] =
                String(
                  value ?? ''
                )
            }
          )
        }
      )

      setColumns(
        nextColumns
      )

      setRows(
        nextRows
      )
    }


  // ========================================================
  // PASTE EVENT
  // ========================================================

  const handlePaste =
    (
      event
    ) => {
      const text =
        event
          .clipboardData
          .getData(
            'text'
          )

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

      if (
        activeCell.area ===
        'header'
      ) {
        applyFullDatasetPaste(
          matrix
        )

        return
      }

      applyCellPaste(
        matrix,
        activeCell.rowIndex,
        activeCell.columnIndex
      )
    }


  // ========================================================
  // UPLOAD CSV / EXCEL
  // ========================================================

  const uploadFile =
    async (
      event
    ) => {
      const file =
        event
          .target
          .files?.[
            0
          ]

      if (
        !file
      ) {
        return
      }

      setUploading(
        true
      )

      setError(
        ''
      )

      setSuccess(
        ''
      )

      try {
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

        const newId =
          response
            .data
            ?.id

        if (
          !newId
        ) {
          throw new Error(
            'Dataset ID was not returned after upload.'
          )
        }

        await loadSavedDatasets()

        goToPrepare(
          newId
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
        setUploading(
          false
        )

        event.target.value =
          ''
      }
    }


  // ========================================================
  // EXPORT CURRENT DATA
  // ========================================================

  const exportCurrentData =
    () => {
      try {
        const normalized =
          normalizeGrid(
            columns,
            rows
          )

        const csv = [
          normalized
            .headers
            .map(
              escapeCSV
            )
            .join(','),

          ...normalized
            .dataRows
            .map(
              (
                row
              ) =>
                row
                  .map(
                    escapeCSV
                  )
                  .join(',')
            ),
        ].join(
          '\n'
        )

        const blob =
          new Blob(
            [
              csv,
            ],
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
          `${
            datasetName.trim() ||
            'dataset'
          }.csv`

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

        setSuccess(
          'Dataset exported successfully.'
        )

        setTransferOpen(
          false
        )

      } catch (
        err
      ) {
        setError(
          getErrorMessage(
            err
          )
        )
      }
    }


  // ========================================================
  // PREPARE DATA
  // ========================================================

  const handlePrepare =
    async () => {
      setError(
        ''
      )

      setSuccess(
        ''
      )

      if (
        isNew
      ) {
        await createDataset({
          redirect:
            true,
        })

        return
      }

      const saved =
        await saveExistingDataset()

      if (
        saved
      ) {
        goToPrepare(
          datasetId
        )
      }
    }


  // ========================================================
  // INFER MEASUREMENT LEVELS
  // ========================================================

  const inferredLevels =
    useMemo(
      () => {
        const result = {}

        columns.forEach(
          (
            column,
            columnIndex
          ) => {
            const name =
              String(
                column ||
                ''
              ).trim()

            if (
              !name
            ) {
              return
            }

            result[
              name
            ] =
              detectMeasurementLevel(
                rows.map(
                  (
                    row
                  ) =>
                    row[
                      columnIndex
                    ]
                )
              )
          }
        )

        return result
      },
      [
        columns,
        rows,
      ]
    )


  // ========================================================
  // DATASET COUNTS
  // ========================================================

  const caseCount =
    useMemo(
      () =>
        rows.filter(
          (
            row
          ) =>
            row.some(
              (
                value
              ) =>
                String(
                  value ?? ''
                ).trim() !== ''
            )
        ).length,
      [
        rows,
      ]
    )


  const variableCount =
    useMemo(
      () =>
        columns.filter(
          (
            column,
            columnIndex
          ) => {
            const hasName =
              String(
                column ||
                ''
              ).trim() !== ''

            const hasData =
              rows.some(
                (
                  row
                ) =>
                  String(
                    row?.[
                      columnIndex
                    ] ??
                    ''
                  ).trim() !== ''
              )

            return (
              hasName ||
              hasData
            )
          }
        ).length,
      [
        columns,
        rows,
      ]
    )


  // ========================================================
  // LOADING
  // ========================================================

  if (
    loading
  ) {
    return (
      <AppShell>

        <div className="ssas-sheet-loading">

          <span>
            Opening dataset...
          </span>

        </div>

      </AppShell>
    )
  }


  // ========================================================
  // RENDER
  // ========================================================

  return (
    <AppShell>

      <div
        className="ssas-sheet-page"
        onPaste={
          handlePaste
        }
      >

        {/* ==================================================
            TOOLBAR
            ================================================== */}

        <div className="ssas-sheet-toolbar">

          <div className="ssas-sheet-toolbar-left">

            {/* ENTER NEW DATA */}

            <button
              type="button"
              className="ssas-sheet-tab active"
              onClick={
                enterNewData
              }
            >
              enter new data
            </button>


            {/* EXPORT / IMPORT */}

            <div className="ssas-sheet-menu-wrap">

              <button
                type="button"
                className="ssas-sheet-tab"
                onClick={() => {
                  setTransferOpen(
                    (
                      current
                    ) =>
                      !current
                  )

                  setSettingsOpen(
                    false
                  )

                  if (
                    !transferOpen
                  ) {
                    loadSavedDatasets()
                  }
                }}
              >
                export / import
              </button>


              {transferOpen && (

                <div className="ssas-sheet-popover ssas-transfer-popover">

                  {/* UPLOAD */}

                  <button
                    type="button"
                    disabled={
                      uploading
                    }
                    onClick={() =>
                      fileInputRef
                        .current
                        ?.click()
                    }
                  >
                    <Upload
                      size={15}
                    />

                    {
                      uploading
                        ? 'Uploading...'
                        : 'Upload CSV / Excel'
                    }

                  </button>


                  {/* EXPORT */}

                  <button
                    type="button"
                    onClick={
                      exportCurrentData
                    }
                  >
                    <Download
                      size={15}
                    />

                    Export current data
                  </button>


                  <div className="ssas-sheet-popover-divider" />


                  <div className="ssas-saved-datasets-title">

                    Saved datasets

                  </div>


                  <div className="ssas-saved-datasets-list">

                    {loadingSavedDatasets && (

                      <div className="ssas-saved-dataset-empty">
                        Loading datasets...
                      </div>

                    )}


                    {!loadingSavedDatasets &&
                    !savedDatasets.length && (

                      <div className="ssas-saved-dataset-empty">
                        No saved datasets.
                      </div>

                    )}


                    {!loadingSavedDatasets &&
                    savedDatasets.map(
                      (
                        savedDataset
                      ) => (

                        <button
                          type="button"
                          key={
                            savedDataset.id
                          }
                          className="ssas-saved-dataset-button"
                          onClick={() =>
                            openSavedDataset(
                              savedDataset.id
                            )
                          }
                        >

                          <FileSpreadsheet
                            size={14}
                          />


                          <span>

                            {
                              savedDataset
                                .original_filename ||
                              savedDataset
                                .filename ||
                              'Dataset'
                            }

                          </span>


                          <small>
                            Open
                          </small>

                        </button>

                      )
                    )}

                  </div>

                </div>

              )}

            </div>


            {/* PREPARE DATA */}

            <button
              type="button"
              className="ssas-sheet-tab"
              disabled={
                saving
              }
              onClick={
                handlePrepare
              }
            >
              {
                saving
                  ? 'saving...'
                  : 'prepare data'
              }
            </button>


            {/* SETTINGS */}

            <div className="ssas-sheet-menu-wrap">

              <button
                type="button"
                className="ssas-sheet-tab"
                onClick={() => {
                  setSettingsOpen(
                    (
                      current
                    ) =>
                      !current
                  )

                  setTransferOpen(
                    false
                  )
                }}
              >
                settings
              </button>


              {settingsOpen && (

                <div className="ssas-sheet-popover settings">

                  <label>

                    Dataset name

                    <input
                      type="text"
                      value={
                        datasetName
                      }
                      disabled={
                        !isNew
                      }
                      onChange={
                        (
                          event
                        ) =>
                          setDatasetName(
                            event
                              .target
                              .value
                          )
                      }
                    />

                  </label>


                  <button
                    type="button"
                    onClick={
                      addRow
                    }
                  >
                    <Plus
                      size={15}
                    />

                    Add case
                  </button>


                  <button
                    type="button"
                    onClick={
                      addColumn
                    }
                  >
                    <Plus
                      size={15}
                    />

                    Add variable
                  </button>

                </div>

              )}

            </div>

          </div>


          {/* SAVE STATUS */}

          <div className="ssas-sheet-toolbar-right">

            <Cloud
              size={15}
            />


            <span>

              {
                saveState ===
                'saving'
                  ? 'saving changes...'

                  : saveState ===
                    'unsaved'
                    ? 'changes pending...'

                    : saveState ===
                      'failed'
                      ? 'save failed'

                      : saveState ===
                        'saved'
                        ? 'autosaved to SSAS'

                        : 'ready for data'
              }

            </span>


            {saveState ===
              'saved' && (

              <Check
                size={14}
              />

            )}

          </div>

        </div>


        {/* FILE UPLOAD */}

        <input
          ref={
            fileInputRef
          }
          type="file"
          hidden
          accept=".csv,.xlsx,.xls"
          onChange={
            uploadFile
          }
        />


        {/* ==================================================
            MESSAGES
            ================================================== */}

        {error && (

          <div className="ssas-sheet-message error">

            {error}

          </div>

        )}


        {success && (

          <div className="ssas-sheet-message success">

            {success}

          </div>

        )}


        {/* ==================================================
            SPREADSHEET
            ================================================== */}

        <div className="ssas-spreadsheet-frame">

          <div className="ssas-spreadsheet-scroll">

            <table className="ssas-spreadsheet">

              <thead>

                {/* ==========================================
                    MEASUREMENT LEVEL
                    ========================================== */}

                <tr className="measurement-row">

                  <th className="case-measurement-cell" />


                  {columns.map(
                    (
                      column,
                      columnIndex
                    ) => {
                      const name =
                        String(
                          column ||
                          ''
                        ).trim()

                      const level =
                        name
                          ? (
                              measurementLevels[
                                name
                              ] ||
                              inferredLevels[
                                name
                              ] ||
                              'nominal'
                            )
                          : ''

                      return (
                        <th
                          key={
                            `measurement-${columnIndex}`
                          }
                          className="measurement-cell"
                        >

                          {name && (

                            <label className="measurement-selector">

                              <select
                                value={
                                  level
                                }
                                onChange={
                                  (
                                    event
                                  ) =>
                                    updateMeasurementLevel(
                                      name,
                                      event
                                        .target
                                        .value
                                    )
                                }
                              >

                                <option value="nominal">
                                  nominal
                                </option>

                                <option value="metric">
                                  metric
                                </option>

                                <option value="ordinal">
                                  ordinal
                                </option>

                              </select>


                              <span className="measurement-content">

                                <span>
                                  {level}
                                </span>


                                <MeasurementIcon
                                  level={
                                    level
                                  }
                                />

                              </span>

                            </label>

                          )}

                        </th>
                      )
                    }
                  )}

                </tr>


                {/* ==========================================
                    VARIABLE NAMES
                    ========================================== */}

                <tr className="variable-row">

                  <th className="case-header-cell">
                    Case
                  </th>


                  {columns.map(
                    (
                      column,
                      columnIndex
                    ) => (

                      <th
                        key={
                          `header-${columnIndex}`
                        }
                        className="variable-header-cell"
                      >

                        <input
                          type="text"
                          value={
                            column
                          }
                          spellCheck="false"
                          onFocus={() =>
                            setActiveCell({
                              area:
                                'header',

                              rowIndex:
                                0,

                              columnIndex,
                            })
                          }
                          onChange={
                            (
                              event
                            ) =>
                              updateColumn(
                                columnIndex,
                                event
                                  .target
                                  .value
                              )
                          }
                        />

                      </th>

                    )
                  )}

                </tr>

              </thead>


              <tbody>

                {rows.map(
                  (
                    row,
                    rowIndex
                  ) => (

                    <tr
                      key={
                        `row-${rowIndex}`
                      }
                    >

                      {/* CASE NUMBER */}

                      <td className="case-number-cell">

                        <span>

                          {rowIndex + 1}

                        </span>


                        <button
                          type="button"
                          className="delete-case-button"
                          title="Delete case"
                          onClick={() =>
                            deleteRow(
                              rowIndex
                            )
                          }
                        >

                          <Trash2
                            size={11}
                          />

                        </button>

                      </td>


                      {/* DATA CELLS */}

                      {columns.map(
                        (
                          _,
                          columnIndex
                        ) => (

                          <td
                            key={
                              `cell-${rowIndex}-${columnIndex}`
                            }
                            className="data-cell"
                          >

                            <input
                              type="text"
                              value={
                                row?.[
                                  columnIndex
                                ] ??
                                ''
                              }
                              spellCheck="false"
                              onFocus={() =>
                                setActiveCell({
                                  area:
                                    'data',

                                  rowIndex,

                                  columnIndex,
                                })
                              }
                              onChange={
                                (
                                  event
                                ) =>
                                  updateCell(
                                    rowIndex,
                                    columnIndex,
                                    event
                                      .target
                                      .value
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

        </div>


        {/* ==================================================
            FOOTER
            ================================================== */}

        <div className="ssas-sheet-footer">

          <span>

            {
              dataset
                ? (
                    dataset
                      .original_filename ||
                    dataset
                      .filename ||
                    'Dataset'
                  )
                : datasetName
            }

          </span>


          <span>

            {caseCount}
            {' cases · '}
            {variableCount}
            {' variables'}

          </span>

        </div>

      </div>

    </AppShell>
  )
}
