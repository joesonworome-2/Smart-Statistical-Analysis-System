import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  Calculator,
} from 'lucide-react'

import api from '../../../api/api'
import ResultTable
  from '../components/ResultTable'


// ==========================================================
// AVAILABLE DESCRIPTIVE STATISTICS
// ==========================================================

const METRIC_OPTIONS = [
  {
    key: 'mean',
    label: 'Mean',
    defaultChecked: true,
  },
  {
    key: 'median',
    label: 'Median',
    defaultChecked: true,
  },
  {
    key: 'mode',
    label: 'Mode',
    defaultChecked: false,
  },
  {
    key: 'sum',
    label: 'Sum',
    defaultChecked: false,
  },
  {
    key: 'standard_deviation',
    label: 'Std. Deviation',
    defaultChecked: true,
  },
  {
    key: 'variance',
    label: 'Variance',
    defaultChecked: false,
  },
  {
    key: 'minimum',
    label: 'Minimum',
    defaultChecked: true,
  },
  {
    key: 'maximum',
    label: 'Maximum',
    defaultChecked: true,
  },
  {
    key: 'range',
    label: 'Range',
    defaultChecked: true,
  },
  {
    key: 'q1',
    label: 'Quartile 1',
    defaultChecked: false,
  },
  {
    key: 'q2',
    label: 'Quartile 2',
    defaultChecked: false,
  },
  {
    key: 'q3',
    label: 'Quartile 3',
    defaultChecked: false,
  },
  {
    key: 'iqr',
    label: 'Interquartile Range',
    defaultChecked: false,
  },
  {
    key: 'median_absolute_deviation',
    label: 'Median absolute deviation',
    defaultChecked: false,
  },
  {
    key: 'skewness',
    label: 'Skew',
    defaultChecked: false,
  },
  {
    key: 'kurtosis',
    label: 'Kurtosis',
    defaultChecked: false,
  },
  {
    key: 'count',
    label: 'Number of values',
    defaultChecked: true,
  },
  {
    key: 'confidence_interval_95',
    label: '95% Confidence interval for mean',
    defaultChecked: false,
  },
  {
    key: 'mean_std',
    label: 'Mean ± Std.',
    defaultChecked: false,
  },
]


const NOMINAL_OPTIONS = [
  {
    key: 'frequency',
    label: 'Frequency',
    defaultChecked: true,
  },
  {
    key: 'percent',
    label: '%',
    defaultChecked: false,
  },
  {
    key: 'valid_percent',
    label: 'Valid %',
    defaultChecked: false,
  },
]


// ==========================================================
// HELPERS
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
    'Unable to calculate descriptive statistics.'
  )
}


function initializeOptions(
  definitions
) {
  const result = {}

  definitions.forEach(
    (option) => {
      result[
        option.key
      ] =
        option.defaultChecked
    }
  )

  return result
}


function normalizeVariable(
  item
) {
  if (
    typeof item === 'string'
  ) {
    return {
      name: item,
      measurement_level:
        'nominal',
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
      item.measurement_level ||
      item.inferred_measurement_level ||
      'nominal',
  }
}


function normalizeVariablesResponse(
  responseData,
  dataset
) {
  const raw =
    responseData?.variables ||
    responseData?.columns ||
    (
      Array.isArray(
        responseData
      )
        ? responseData
        : []
    )

  if (
    Array.isArray(raw) &&
    raw.length
  ) {
    return raw
      .map(
        normalizeVariable
      )
      .filter(
        (item) =>
          item.name
      )
  }

  return (
    dataset?.columns || []
  ).map(
    (column) => ({
      name: column,
      measurement_level:
        'nominal',
    })
  )
}


function selectedKeys(
  options
) {
  return Object
    .entries(options)
    .filter(
      ([, checked]) =>
        checked
    )
    .map(
      ([key]) =>
        key
    )
}


function formatSimple(value) {
  if (
    value === null ||
    value === undefined
  ) {
    return '—'
  }

  if (
    typeof value !== 'number'
  ) {
    return String(value)
  }

  if (
    Number.isInteger(value)
  ) {
    return value
      .toLocaleString()
  }

  return Number(
    value.toFixed(4)
  ).toLocaleString()
}


function metricStatisticValue(
  statistics,
  key
) {
  if (!statistics) {
    return null
  }

  if (
    key === 'q2'
  ) {
    return (
      statistics.q2 ??
      statistics.median
    )
  }

  if (
    key === 'confidence_interval_95'
  ) {
    const interval =
      statistics
        .confidence_interval_95

    if (!interval) {
      return null
    }

    return `${
      formatSimple(
        interval.lower
      )
    } – ${
      formatSimple(
        interval.upper
      )
    }`
  }

  if (
    key === 'mean_std'
  ) {
    if (
      statistics.mean === null ||
      statistics.mean === undefined ||
      statistics
        .standard_deviation === null ||
      statistics
        .standard_deviation === undefined
    ) {
      return null
    }

    return `${
      formatSimple(
        statistics.mean
      )
    } ± ${
      formatSimple(
        statistics
          .standard_deviation
      )
    }`
  }

  return statistics[key]
}


function frequencyRowsFromResponse(
  responseData,
  chosenOptions
) {
  const source =
    responseData
      ?.frequency_table ||
    responseData
      ?.frequencies ||
    responseData
      ?.results ||
    responseData

  if (
    Array.isArray(source)
  ) {
    return source.map(
      (item) => {
        const normalized =
          typeof item === 'object'
            ? item
            : {
                value: item,
              }

        const category =
          normalized.value ??
          normalized.category ??
          normalized.label ??
          normalized.name ??
          ''

        const frequency =
          normalized.frequency ??
          normalized.count ??
          normalized.n ??
          null

        const percent =
          normalized.percent ??
          normalized.percentage ??
          null

        const validPercent =
          normalized.valid_percent ??
          normalized.valid_percentage ??
          percent

        const row = {
          Category: category,
        }

        if (
          chosenOptions.includes(
            'frequency'
          )
        ) {
          row.Frequency =
            frequency
        }

        if (
          chosenOptions.includes(
            'percent'
          )
        ) {
          row['%'] =
            percent
        }

        if (
          chosenOptions.includes(
            'valid_percent'
          )
        ) {
          row['Valid %'] =
            validPercent
        }

        return row
      }
    )
  }

  if (
    source &&
    typeof source === 'object'
  ) {
    const entries =
      Object.entries(source)

    const total =
      entries.reduce(
        (
          sum,
          [, value]
        ) => {
          if (
            typeof value === 'number'
          ) {
            return sum + value
          }

          return (
            sum +
            Number(
              value?.frequency ??
              value?.count ??
              0
            )
          )
        },
        0
      )

    return entries.map(
      ([category, value]) => {
        const frequency =
          typeof value === 'number'
            ? value
            : (
                value?.frequency ??
                value?.count ??
                0
              )

        const calculatedPercent =
          total
            ? (
                Number(frequency) /
                total
              ) * 100
            : null

        const row = {
          Category: category,
        }

        if (
          chosenOptions.includes(
            'frequency'
          )
        ) {
          row.Frequency =
            frequency
        }

        if (
          chosenOptions.includes(
            'percent'
          )
        ) {
          row['%'] =
            calculatedPercent
        }

        if (
          chosenOptions.includes(
            'valid_percent'
          )
        ) {
          row['Valid %'] =
            calculatedPercent
        }

        return row
      }
    )
  }

  return []
}


function buildDescriptiveInterpretation(
  metricTable,
  frequencyTables
) {
  const sentences = []

  if (
    metricTable?.rows?.length
  ) {
    const variables =
      metricTable.columns
        .slice(1)

    const meanRow =
      metricTable.rows.find(
        (row) =>
          row.Statistic === 'Mean'
      )

    const medianRow =
      metricTable.rows.find(
        (row) =>
          row.Statistic === 'Median'
      )

    if (meanRow) {
      const parts =
        variables
          .slice(0, 4)
          .map(
            (variable) => {
              const mean =
                meanRow[variable]

              const median =
                medianRow?.[variable]

              if (
                mean === null ||
                mean === undefined
              ) {
                return null
              }

              let text =
                `${variable} has a mean of ${formatSimple(mean)}`

              if (
                median !== null &&
                median !== undefined
              ) {
                text +=
                  ` and a median of ${formatSimple(median)}`
              }

              return text
            }
          )
          .filter(Boolean)

      if (parts.length) {
        sentences.push(
          parts.join('; ') + '.'
        )
      }
    }

    if (!sentences.length) {
      sentences.push(
        `Descriptive statistics were calculated for ${variables.join(', ')}.`
      )
    }
  }

  if (
    frequencyTables.length
  ) {
    const names =
      frequencyTables.map(
        (table) =>
          table.title
            .replace(
              / frequencies$/i,
              ''
            )
      )

    sentences.push(
      `Frequency distributions were calculated for ${names.join(', ')}.`
    )
  }

  return sentences.join(' ')
}


// ==========================================================
// COMPONENT
// ==========================================================

export default function DescriptiveAnalysis({
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
    metricOptions,
    setMetricOptions,
  ] = useState(
    () =>
      initializeOptions(
        METRIC_OPTIONS
      )
  )

  const [
    nominalOptions,
    setNominalOptions,
  ] = useState(
    () =>
      initializeOptions(
        NOMINAL_OPTIONS
      )
  )

  const [
    loadingVariables,
    setLoadingVariables,
  ] = useState(false)

  const [
    calculating,
    setCalculating,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState('')

  const [
    saveNotice,
    setSaveNotice,
  ] = useState('')

  const [
    metricTable,
    setMetricTable,
  ] = useState(null)

  const [
    frequencyTables,
    setFrequencyTables,
  ] = useState([])


  // ========================================================
  // LOAD VARIABLES
  // ========================================================

  useEffect(
    () => {
      if (!datasetId) {
        setVariables([])
        setSelectedVariables([])
        return
      }

      const loadVariables =
        async () => {
          setLoadingVariables(true)
          setError('')
          setSaveNotice('')
          setMetricTable(null)
          setFrequencyTables([])

          try {
            const response =
              await api.get(
                `/datasets/${datasetId}/variables`
              )

            const normalized =
              normalizeVariablesResponse(
                response.data,
                dataset
              )

            setVariables(
              normalized
            )

            setSelectedVariables([])

          } catch (err) {
            const fallback =
              (
                dataset?.columns || []
              ).map(
                (column) => ({
                  name: column,
                  measurement_level:
                    'nominal',
                })
              )

            setVariables(
              fallback
            )

            setError(
              getErrorMessage(err)
            )

          } finally {
            setLoadingVariables(false)
          }
        }

      loadVariables()
    },
    [
      datasetId,
      dataset,
    ]
  )


  // ========================================================
  // VARIABLE GROUPS
  // ========================================================

  const metricVariables =
    useMemo(
      () =>
        variables.filter(
          (variable) =>
            variable.measurement_level ===
            'metric'
        ),
      [variables]
    )

  const ordinalVariables =
    useMemo(
      () =>
        variables.filter(
          (variable) =>
            variable.measurement_level ===
            'ordinal'
        ),
      [variables]
    )

  const nominalVariables =
    useMemo(
      () =>
        variables.filter(
          (variable) =>
            variable.measurement_level ===
            'nominal'
        ),
      [variables]
    )


  // ========================================================
  // SELECTION HELPERS
  // ========================================================

  const isSelected =
    (name) =>
      selectedVariables.includes(
        name
      )

  const toggleVariable =
    (name) => {
      setSelectedVariables(
        (previous) =>
          previous.includes(name)
            ? previous.filter(
                (item) =>
                  item !== name
              )
            : [
                ...previous,
                name,
              ]
      )
    }

  const toggleMetricOption =
    (key) => {
      setMetricOptions(
        (previous) => ({
          ...previous,
          [key]:
            !previous[key],
        })
      )
    }

  const toggleNominalOption =
    (key) => {
      setNominalOptions(
        (previous) => ({
          ...previous,
          [key]:
            !previous[key],
        })
      )
    }


  // ========================================================
  // SAVE EXACT DISPLAYED RESULT FOR REPORT GENERATION
  // ========================================================

  const saveDisplayedResult =
    async (
      tables,
      interpretation,
      selectedMetric,
      selectedCategorical,
      chosenMetricOptions,
      chosenNominalOptions
    ) => {
      if (!tables.length) {
        return
      }

      await api.post(
        '/statistics/results',
        {
          dataset_id:
            datasetId,

          dataset_name:
            dataset?.original_filename ||
            dataset?.filename ||
            'Dataset',

          method:
            'descriptive',

          title:
            'Descriptive statistics',

          configuration: {
            metric_variables:
              selectedMetric,

            categorical_variables:
              selectedCategorical,

            metric_statistics:
              chosenMetricOptions,

            frequency_statistics:
              chosenNominalOptions,
          },

          tables,

          assumptions:
            null,

          interpretation,

          apa:
            null,

          metadata: {
            source:
              'descriptive_analysis',

            exact_displayed_result:
              true,
          },
        }
      )
    }


  // ========================================================
  // CALCULATE
  // ========================================================

  const calculate =
    async () => {
      if (!datasetId) {
        setError(
          'Select a dataset first.'
        )
        return
      }

      if (!selectedVariables.length) {
        setError(
          'Select at least one variable.'
        )
        return
      }

      setCalculating(true)
      setError('')
      setSaveNotice('')
      setMetricTable(null)
      setFrequencyTables([])

      try {
        const selectedMetric =
          selectedVariables.filter(
            (name) =>
              metricVariables.some(
                (variable) =>
                  variable.name === name
              )
          )

        const selectedNominal =
          selectedVariables.filter(
            (name) =>
              nominalVariables.some(
                (variable) =>
                  variable.name === name
              )
          )

        const selectedOrdinal =
          selectedVariables.filter(
            (name) =>
              ordinalVariables.some(
                (variable) =>
                  variable.name === name
              )
          )

        const selectedCategorical = [
          ...selectedNominal,
          ...selectedOrdinal,
        ]

        const chosenMetricOptions =
          selectedKeys(
            metricOptions
          )

        const chosenNominalOptions =
          selectedKeys(
            nominalOptions
          )

        let nextMetricTable =
          null

        const nextFrequencyTables = []


        // --------------------------------------------------
        // METRIC TABLE
        // --------------------------------------------------
        if (
          selectedMetric.length
        ) {
          const response =
            await api.get(
              `/statistics/descriptive/${datasetId}`
            )

          const statistics =
            response.data.results ||
            {}

          const tableRows =
            chosenMetricOptions.map(
              (statisticKey) => {
                const option =
                  METRIC_OPTIONS.find(
                    (item) =>
                      item.key ===
                      statisticKey
                  )

                const row = {
                  Statistic:
                    option?.label ||
                    statisticKey,
                }

                selectedMetric.forEach(
                  (variable) => {
                    row[variable] =
                      metricStatisticValue(
                        statistics[variable],
                        statisticKey
                      )
                  }
                )

                return row
              }
            )

          nextMetricTable = {
            title:
              'Descriptive statistics',

            columns: [
              'Statistic',
              ...selectedMetric,
            ],

            rows:
              tableRows,
          }
        }


        // --------------------------------------------------
        // NOMINAL / ORDINAL FREQUENCY TABLES
        // --------------------------------------------------
        for (
          const variable
          of selectedCategorical
        ) {
          const response =
            await api.get(
              `/statistics/smart/frequencies/${datasetId}`,
              {
                params: {
                  column:
                    variable,
                },
              }
            )

          const rawRows =
            frequencyRowsFromResponse(
              response.data,
              chosenNominalOptions
            )

          const columns = [
            variable,
          ]

          if (
            chosenNominalOptions.includes(
              'frequency'
            )
          ) {
            columns.push(
              'Frequency'
            )
          }

          if (
            chosenNominalOptions.includes(
              'percent'
            )
          ) {
            columns.push('%')
          }

          if (
            chosenNominalOptions.includes(
              'valid_percent'
            )
          ) {
            columns.push(
              'Valid %'
            )
          }

          const renamedRows =
            rawRows.map(
              (row) => {
                const next = {
                  [variable]:
                    row.Category,
                }

                if (
                  columns.includes(
                    'Frequency'
                  )
                ) {
                  next.Frequency =
                    row.Frequency
                }

                if (
                  columns.includes('%')
                ) {
                  next['%'] =
                    row['%']
                }

                if (
                  columns.includes(
                    'Valid %'
                  )
                ) {
                  next['Valid %'] =
                    row['Valid %']
                }

                return next
              }
            )

          nextFrequencyTables.push({
            title:
              `${variable} frequencies`,

            columns,

            rows:
              renamedRows,
          })
        }


        // --------------------------------------------------
        // DISPLAY RESULTS
        // --------------------------------------------------
        setMetricTable(
          nextMetricTable
        )

        setFrequencyTables(
          nextFrequencyTables
        )


        // --------------------------------------------------
        // SAVE EXACTLY WHAT THE USER SEES
        // --------------------------------------------------
        const reportTables = [
          ...(
            nextMetricTable
              ? [nextMetricTable]
              : []
          ),
          ...nextFrequencyTables,
        ]

        const interpretation =
          buildDescriptiveInterpretation(
            nextMetricTable,
            nextFrequencyTables
          )

        try {
          await saveDisplayedResult(
            reportTables,
            interpretation,
            selectedMetric,
            selectedCategorical,
            chosenMetricOptions,
            chosenNominalOptions
          )

          setSaveNotice(
            'These results were saved and will be included in the SSAS report.'
          )

        } catch (saveError) {
          setSaveNotice(
            'Results were calculated, but SSAS could not save this result to the report history.'
          )

          console.error(
            'Unable to save descriptive result:',
            saveError
          )
        }

      } catch (err) {
        setError(
          getErrorMessage(err)
        )

      } finally {
        setCalculating(false)
      }
    }


  // ========================================================
  // RENDER VARIABLE GROUP
  // ========================================================

  const renderVariableGroup =
    (
      title,
      items
    ) => (
      <div className="analysis-variable-group">

        <h4>
          {title}
        </h4>

        {items.length ? (
          <div className="analysis-variable-list">

            {items.map(
              (variable) => (
                <label
                  key={
                    variable.name
                  }
                >
                  <input
                    type="checkbox"
                    checked={
                      isSelected(
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
            )}

          </div>
        ) : (
          <span className="analysis-empty-variable-group">
            No variables
          </span>
        )}

      </div>
    )


  // ========================================================
  // RENDER
  // ========================================================

  if (
    loadingVariables
  ) {
    return (
      <div className="analysis-method-loading">
        Loading variable information...
      </div>
    )
  }

  return (
    <div className="descriptive-analysis">

      <section className="analysis-configuration">

        <div className="analysis-section-label">
          Configuration
        </div>

        <div className="analysis-variable-grid">

          {renderVariableGroup(
            'Metric Variables',
            metricVariables
          )}

          {renderVariableGroup(
            'Ordinal Variables',
            ordinalVariables
          )}

          {renderVariableGroup(
            'Nominal Variables',
            nominalVariables
          )}

        </div>

        <div className="descriptive-calculation-options">

          <h4>
            Calculate
          </h4>

          <div className="descriptive-option-layout">

            <div className="descriptive-metric-options">

              {METRIC_OPTIONS.map(
                (option) => (
                  <label
                    key={
                      option.key
                    }
                  >
                    <input
                      type="checkbox"
                      checked={
                        metricOptions[
                          option.key
                        ]
                      }
                      onChange={() =>
                        toggleMetricOption(
                          option.key
                        )
                      }
                    />

                    <span>
                      {option.label}
                    </span>
                  </label>
                )
              )}

            </div>

            <div className="descriptive-nominal-options">

              {NOMINAL_OPTIONS.map(
                (option) => (
                  <label
                    key={
                      option.key
                    }
                  >
                    <input
                      type="checkbox"
                      checked={
                        nominalOptions[
                          option.key
                        ]
                      }
                      onChange={() =>
                        toggleNominalOption(
                          option.key
                        )
                      }
                    />

                    <span>
                      {option.label}
                    </span>
                  </label>
                )
              )}

            </div>

          </div>

          <button
            type="button"
            className="analysis-calculate-button"
            disabled={
              calculating
            }
            onClick={
              calculate
            }
          >
            <Calculator
              size={16}
            />

            {calculating
              ? 'Calculating...'
              : 'Calculate'}
          </button>

        </div>

      </section>

      {error && (
        <div className="analysis-error">
          {error}
        </div>
      )}

      {saveNotice && (
        <div className="analysis-result-save-notice">
          {saveNotice}
        </div>
      )}

      {(
        metricTable ||
        frequencyTables.length > 0
      ) && (
        <section className="analysis-results-container">

          <div className="analysis-section-label">
            Results
          </div>

          {metricTable && (
            <ResultTable
              title={
                metricTable.title
              }
              columns={
                metricTable.columns
              }
              rows={
                metricTable.rows
              }
            />
          )}

          {frequencyTables.map(
            (table) => (
              <ResultTable
                key={
                  table.title
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
          )}

        </section>
      )}

    </div>
  )
}
