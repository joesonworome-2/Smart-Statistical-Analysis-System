import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  Activity,
  BarChart3,
  Calculator,
  CheckCircle2,
  ChevronDown,
  Database,
  FlaskConical,
  LoaderCircle,
  Play,
  RefreshCw,
  Sigma,
  TrendingUp,
} from 'lucide-react'

import api from '../../api/api'
import AppShell from '../../components/AppShell'


const ANALYSIS_TYPES = [
  {
    value: 'descriptive',
    label: 'Descriptive Statistics',
    description:
      'Calculate count, mean, standard deviation, minimum, maximum and related summary statistics.',
  },
  {
    value: 'correlation',
    label: 'Correlation Analysis',
    description:
      'Measure relationships between variables using Pearson, Spearman or Kendall correlation.',
  },
  {
    value: 'one_sample_t',
    label: 'One-Sample T-Test',
    description:
      'Compare the mean of one variable against a known population mean.',
  },
  {
    value: 'independent_t',
    label: 'Independent T-Test',
    description:
      'Compare the means of two independent groups.',
  },
  {
    value: 'paired_t',
    label: 'Paired T-Test',
    description:
      'Compare two related or paired measurements.',
  },
  {
    value: 'chi_square',
    label: 'Chi-Square Test',
    description:
      'Test the association between two categorical variables.',
  },
  {
    value: 'shapiro',
    label: 'Shapiro-Wilk Normality Test',
    description:
      'Test whether a variable follows a normal distribution.',
  },
  {
    value: 'mann_whitney',
    label: 'Mann–Whitney U Test',
    description:
      'Non-parametric comparison of two independent groups.',
  },
  {
    value: 'wilcoxon',
    label: 'Wilcoxon Signed-Rank Test',
    description:
      'Non-parametric comparison of paired variables.',
  },
  {
    value: 'kruskal_wallis',
    label: 'Kruskal–Wallis Test',
    description:
      'Non-parametric comparison across multiple groups.',
  },
  {
    value: 'anova',
    label: 'One-Way ANOVA',
    description:
      'Compare the means of a numeric variable across multiple groups.',
  },
  {
    value: 'confidence_interval',
    label: 'Confidence Interval',
    description:
      'Estimate a confidence interval for the mean of a selected variable.',
  },
  {
    value: 'regression',
    label: 'Simple Linear Regression',
    description:
      'Model the relationship between an independent variable and dependent variable.',
  },
]


const INITIAL_FORM = {
  column: '',
  column1: '',
  column2: '',
  groupColumn: '',
  group1: '',
  group2: '',
  valueColumn: '',
  xVariable: '',
  yVariable: '',
  populationMean: '',
  confidence: '0.95',
  correlationMethod: 'pearson',
}


export default function AnalysisPage() {
  const [datasets, setDatasets] =
    useState([])

  const [selectedDatasetId, setSelectedDatasetId] =
    useState('')

  const [analysisType, setAnalysisType] =
    useState('descriptive')

  const [form, setForm] =
    useState(INITIAL_FORM)

  const [correlationColumns, setCorrelationColumns] =
    useState([])

  const [result, setResult] =
    useState(null)

  const [loadingDatasets, setLoadingDatasets] =
    useState(true)

  const [running, setRunning] =
    useState(false)

  const [error, setError] =
    useState('')


  const selectedDataset =
    useMemo(
      () =>
        datasets.find(
          (dataset) =>
            dataset.id ===
            selectedDatasetId
        ),
      [
        datasets,
        selectedDatasetId,
      ]
    )


  const selectedAnalysis =
    ANALYSIS_TYPES.find(
      (item) =>
        item.value ===
        analysisType
    )


  const columns =
    selectedDataset?.columns || []


  const loadDatasets = async () => {
    setLoadingDatasets(true)
    setError('')

    try {
      const response =
        await api.get('/datasets')

      const items =
        response.data.datasets || []

      setDatasets(items)

      if (
        items.length > 0 &&
        !selectedDatasetId
      ) {
        setSelectedDatasetId(
          items[0].id
        )
      }

    } catch (err) {
      setError(
        getErrorMessage(
          err,
          'Unable to load datasets.'
        )
      )

    } finally {
      setLoadingDatasets(false)
    }
  }


  useEffect(() => {
    loadDatasets()
  }, [])


  useEffect(() => {
    setForm(INITIAL_FORM)
    setCorrelationColumns([])
    setResult(null)
    setError('')
  }, [
    selectedDatasetId,
    analysisType,
  ])


  const updateForm = (
    field,
    value
  ) => {
    setForm((previous) => ({
      ...previous,
      [field]: value,
    }))
  }


  const toggleCorrelationColumn =
    (column) => {

      setCorrelationColumns(
        (previous) => {

          if (
            previous.includes(column)
          ) {
            return previous.filter(
              (item) =>
                item !== column
            )
          }

          return [
            ...previous,
            column,
          ]
        }
      )
    }


  const runAnalysis =
    async () => {

      if (!selectedDatasetId) {
        setError(
          'Please select a dataset.'
        )
        return
      }

      setRunning(true)
      setError('')
      setResult(null)

      try {
        let response

        switch (analysisType) {

          case 'descriptive':

            response =
              await api.get(
                `/statistics/descriptive/${selectedDatasetId}`
              )

            break


          case 'correlation':

            response =
              await api.post(
                `/statistics/correlation/${selectedDatasetId}`,
                {
                  columns:
                    correlationColumns
                      .length > 0
                      ? correlationColumns
                      : null,

                  method:
                    form
                      .correlationMethod,
                }
              )

            break


          case 'one_sample_t':

            requireFields(
              {
                column:
                  form.column,

                populationMean:
                  form.populationMean,
              },
              {
                column:
                  'Variable',

                populationMean:
                  'Population mean',
              }
            )

            response =
              await api.post(
                `/statistics/one-sample-t/${selectedDatasetId}`,
                {
                  column:
                    form.column,

                  population_mean:
                    Number(
                      form.populationMean
                    ),
                }
              )

            break


          case 'independent_t':

            requireFields(
              {
                column:
                  form.column,

                groupColumn:
                  form.groupColumn,

                group1:
                  form.group1,

                group2:
                  form.group2,
              },
              {
                column:
                  'Value variable',

                groupColumn:
                  'Group variable',

                group1:
                  'Group 1',

                group2:
                  'Group 2',
              }
            )

            response =
              await api.post(
                `/statistics/independent-t/${selectedDatasetId}`,
                {
                  column:
                    form.column,

                  group_column:
                    form.groupColumn,

                  group1:
                    parseGroupValue(
                      form.group1
                    ),

                  group2:
                    parseGroupValue(
                      form.group2
                    ),
                }
              )

            break


          case 'paired_t':

            requireFields(
              {
                column1:
                  form.column1,

                column2:
                  form.column2,
              },
              {
                column1:
                  'First variable',

                column2:
                  'Second variable',
              }
            )

            response =
              await api.post(
                `/statistics/paired-t/${selectedDatasetId}`,
                {
                  column1:
                    form.column1,

                  column2:
                    form.column2,
                }
              )

            break


          case 'chi_square':

            requireFields(
              {
                column1:
                  form.column1,

                column2:
                  form.column2,
              },
              {
                column1:
                  'First variable',

                column2:
                  'Second variable',
              }
            )

            response =
              await api.post(
                `/statistics/chi-square/${selectedDatasetId}`,
                {
                  column1:
                    form.column1,

                  column2:
                    form.column2,
                }
              )

            break


          case 'shapiro':

            requireFields(
              {
                column:
                  form.column,
              },
              {
                column:
                  'Variable',
              }
            )

            response =
              await api.post(
                `/statistics/shapiro/${selectedDatasetId}`,
                {
                  column:
                    form.column,
                }
              )

            break


          case 'mann_whitney':

            requireFields(
              {
                column:
                  form.column,

                groupColumn:
                  form.groupColumn,

                group1:
                  form.group1,

                group2:
                  form.group2,
              },
              {
                column:
                  'Value variable',

                groupColumn:
                  'Group variable',

                group1:
                  'Group 1',

                group2:
                  'Group 2',
              }
            )

            response =
              await api.post(
                `/statistics/mann-whitney/${selectedDatasetId}`,
                {
                  column:
                    form.column,

                  group_column:
                    form.groupColumn,

                  group1:
                    parseGroupValue(
                      form.group1
                    ),

                  group2:
                    parseGroupValue(
                      form.group2
                    ),
                }
              )

            break


          case 'wilcoxon':

            requireFields(
              {
                column1:
                  form.column1,

                column2:
                  form.column2,
              },
              {
                column1:
                  'First variable',

                column2:
                  'Second variable',
              }
            )

            response =
              await api.post(
                `/statistics/wilcoxon/${selectedDatasetId}`,
                {
                  column1:
                    form.column1,

                  column2:
                    form.column2,
                }
              )

            break


          case 'kruskal_wallis':

            requireFields(
              {
                valueColumn:
                  form.valueColumn,

                groupColumn:
                  form.groupColumn,
              },
              {
                valueColumn:
                  'Value variable',

                groupColumn:
                  'Group variable',
              }
            )

            response =
              await api.post(
                `/statistics/kruskal-wallis/${selectedDatasetId}`,
                {
                  value_column:
                    form.valueColumn,

                  group_column:
                    form.groupColumn,
                }
              )

            break


          case 'anova':

            requireFields(
              {
                valueColumn:
                  form.valueColumn,

                groupColumn:
                  form.groupColumn,
              },
              {
                valueColumn:
                  'Value variable',

                groupColumn:
                  'Group variable',
              }
            )

            response =
              await api.post(
                `/statistics/anova/${selectedDatasetId}`,
                {
                  value_column:
                    form.valueColumn,

                  group_column:
                    form.groupColumn,
                }
              )

            break


          case 'confidence_interval':

            requireFields(
              {
                column:
                  form.column,
              },
              {
                column:
                  'Variable',
              }
            )

            response =
              await api.post(
                `/statistics/confidence-interval/${selectedDatasetId}`,
                {
                  column:
                    form.column,

                  confidence:
                    Number(
                      form.confidence
                    ),
                }
              )

            break


          case 'regression':

            requireFields(
              {
                xVariable:
                  form.xVariable,

                yVariable:
                  form.yVariable,
              },
              {
                xVariable:
                  'Independent variable',

                yVariable:
                  'Dependent variable',
              }
            )

            response =
              await api.post(
                `/analysis/regression/${selectedDatasetId}`,
                null,
                {
                  params: {
                    x_variable:
                      form.xVariable,

                    y_variable:
                      form.yVariable,
                  },
                }
              )

            break


          default:
            throw new Error(
              'Unsupported analysis type.'
            )
        }

        setResult(
          response.data
        )

      } catch (err) {
        setError(
          getErrorMessage(
            err,
            'Statistical analysis failed.'
          )
        )

      } finally {
        setRunning(false)
      }
    }


  return (
    <AppShell>

      <header className="analysis-header">

        <div>
          <span className="eyebrow dark">
            STATISTICAL ANALYSIS
          </span>

          <h1>
            Analyze Your Data
          </h1>

          <p>
            Select a dataset and
            statistical method,
            configure the required
            variables and run the
            analysis.
          </p>
        </div>

        <div className="analysis-header-icon">
          <Sigma size={29} />
        </div>

      </header>


      {error && (
        <div className="alert error">
          {error}
        </div>
      )}


      <section className="analysis-grid">

        <div className="analysis-sidebar-panel">

          <div className="analysis-section-title">
            <Database size={18} />

            <div>
              <strong>
                Dataset
              </strong>

              <span>
                Choose data to analyze
              </span>
            </div>
          </div>


          {loadingDatasets ? (

            <div className="analysis-loading">
              <LoaderCircle
                className="spin-icon"
                size={22}
              />

              Loading datasets...
            </div>

          ) : (

            <div className="analysis-field">

              <label>
                Select Dataset
              </label>

              <div className="select-wrapper">

                <select
                  value={
                    selectedDatasetId
                  }
                  onChange={(event) =>
                    setSelectedDatasetId(
                      event.target.value
                    )
                  }
                >
                  {datasets.map(
                    (dataset) => (
                      <option
                        value={dataset.id}
                        key={dataset.id}
                      >
                        {
                          dataset
                            .original_filename
                        }
                      </option>
                    )
                  )}
                </select>

                <ChevronDown
                  size={16}
                />

              </div>

            </div>
          )}


          {selectedDataset && (
            <div className="selected-dataset-card">

              <strong>
                {
                  selectedDataset
                    .original_filename
                }
              </strong>

              <div>
                <span>
                  {
                    selectedDataset
                      .row_count
                  } rows
                </span>

                <span>
                  {
                    selectedDataset
                      .column_count
                  } columns
                </span>
              </div>

              <div className="analysis-column-list">

                {
                  selectedDataset
                    .columns
                    .map(
                      (column) => (
                        <span
                          key={column}
                        >
                          {column}
                        </span>
                      )
                    )
                }

              </div>

            </div>
          )}


          <div className="analysis-divider" />


          <div className="analysis-section-title">
            <FlaskConical size={18} />

            <div>
              <strong>
                Analysis Method
              </strong>

              <span>
                Select statistical test
              </span>
            </div>
          </div>


          <div className="analysis-field">

            <label>
              Analysis
            </label>

            <div className="select-wrapper">

              <select
                value={analysisType}
                onChange={(event) =>
                  setAnalysisType(
                    event.target.value
                  )
                }
              >
                {
                  ANALYSIS_TYPES.map(
                    (type) => (
                      <option
                        key={
                          type.value
                        }
                        value={
                          type.value
                        }
                      >
                        {
                          type.label
                        }
                      </option>
                    )
                  )
                }
              </select>

              <ChevronDown
                size={16}
              />

            </div>

          </div>


          <div className="analysis-description">
            <Calculator size={18} />

            <p>
              {
                selectedAnalysis
                  ?.description
              }
            </p>
          </div>


          <button
            className="analysis-run-button"
            onClick={runAnalysis}
            disabled={
              running ||
              !selectedDatasetId
            }
          >

            {running ? (
              <>
                <LoaderCircle
                  size={18}
                  className="spin-icon"
                />

                Running Analysis...
              </>
            ) : (
              <>
                <Play size={18} />

                Run Analysis
              </>
            )}

          </button>


          <button
            className="analysis-refresh-button"
            onClick={loadDatasets}
          >
            <RefreshCw size={16} />
            Refresh Datasets
          </button>

        </div>


        <div className="analysis-workspace">

          <section className="analysis-config-card">

            <div className="analysis-card-header">

              <div>
                <span className="eyebrow dark">
                  CONFIGURATION
                </span>

                <h2>
                  {
                    selectedAnalysis
                      ?.label
                  }
                </h2>
              </div>

              <Activity size={24} />

            </div>


            <AnalysisForm
              type={analysisType}
              columns={columns}
              form={form}
              updateForm={
                updateForm
              }
              correlationColumns={
                correlationColumns
              }
              toggleCorrelationColumn={
                toggleCorrelationColumn
              }
            />

          </section>


          <section className="analysis-results-card">

            <div className="analysis-card-header">

              <div>
                <span className="eyebrow dark">
                  RESULTS
                </span>

                <h2>
                  Analysis Results
                </h2>
              </div>

              {result && (
                <CheckCircle2
                  size={25}
                  className="result-success-icon"
                />
              )}

            </div>


            {!result ? (

              <div className="analysis-empty-results">

                <BarChart3 size={45} />

                <h3>
                  No analysis results yet
                </h3>

                <p>
                  Configure your
                  statistical analysis
                  and click Run Analysis.
                </p>

              </div>

            ) : (

              <ResultViewer
                result={result}
              />

            )}

          </section>

        </div>

      </section>

    </AppShell>
  )
}


function AnalysisForm({
  type,
  columns,
  form,
  updateForm,
  correlationColumns,
  toggleCorrelationColumn,
}) {

  if (
    type ===
    'descriptive'
  ) {
    return (
      <InfoBox>
        Descriptive statistics will
        automatically analyze the
        compatible variables in the
        selected dataset.
      </InfoBox>
    )
  }


  if (
    type ===
    'correlation'
  ) {
    return (
      <>
        <FieldLabel>
          Correlation Method
        </FieldLabel>

        <select
          className="analysis-select"
          value={
            form.correlationMethod
          }
          onChange={(event) =>
            updateForm(
              'correlationMethod',
              event.target.value
            )
          }
        >
          <option value="pearson">
            Pearson
          </option>

          <option value="spearman">
            Spearman
          </option>

          <option value="kendall">
            Kendall
          </option>
        </select>


        <FieldLabel>
          Variables
        </FieldLabel>

        <p className="analysis-help">
          Select variables to include.
          Leaving all unchecked allows
          the backend to use compatible
          columns automatically.
        </p>

        <div className="column-checkbox-grid">

          {columns.map(
            (column) => (

              <label
                key={column}
                className="column-checkbox"
              >

                <input
                  type="checkbox"
                  checked={
                    correlationColumns
                      .includes(
                        column
                      )
                  }
                  onChange={() =>
                    toggleCorrelationColumn(
                      column
                    )
                  }
                />

                <span>
                  {column}
                </span>

              </label>

            )
          )}

        </div>
      </>
    )
  }


  if (
    type ===
    'one_sample_t'
  ) {
    return (
      <>
        <ColumnSelect
          label="Variable"
          columns={columns}
          value={form.column}
          onChange={(value) =>
            updateForm(
              'column',
              value
            )
          }
        />

        <NumberField
          label="Population Mean"
          value={
            form.populationMean
          }
          onChange={(value) =>
            updateForm(
              'populationMean',
              value
            )
          }
          placeholder="e.g. 75"
        />
      </>
    )
  }


  if (
    type ===
    'independent_t' ||
    type ===
    'mann_whitney'
  ) {
    return (
      <>
        <ColumnSelect
          label="Value Variable"
          columns={columns}
          value={form.column}
          onChange={(value) =>
            updateForm(
              'column',
              value
            )
          }
        />

        <ColumnSelect
          label="Group Variable"
          columns={columns}
          value={
            form.groupColumn
          }
          onChange={(value) =>
            updateForm(
              'groupColumn',
              value
            )
          }
        />

        <div className="analysis-two-column">

          <TextField
            label="Group 1 Value"
            value={form.group1}
            onChange={(value) =>
              updateForm(
                'group1',
                value
              )
            }
            placeholder="e.g. Male"
          />

          <TextField
            label="Group 2 Value"
            value={form.group2}
            onChange={(value) =>
              updateForm(
                'group2',
                value
              )
            }
            placeholder="e.g. Female"
          />

        </div>
      </>
    )
  }


  if (
    type ===
    'paired_t' ||
    type ===
    'wilcoxon' ||
    type ===
    'chi_square'
  ) {
    return (
      <div className="analysis-two-column">

        <ColumnSelect
          label="First Variable"
          columns={columns}
          value={form.column1}
          onChange={(value) =>
            updateForm(
              'column1',
              value
            )
          }
        />

        <ColumnSelect
          label="Second Variable"
          columns={columns}
          value={form.column2}
          onChange={(value) =>
            updateForm(
              'column2',
              value
            )
          }
        />

      </div>
    )
  }


  if (
    type ===
    'shapiro'
  ) {
    return (
      <ColumnSelect
        label="Variable"
        columns={columns}
        value={form.column}
        onChange={(value) =>
          updateForm(
            'column',
            value
          )
        }
      />
    )
  }


  if (
    type ===
      'kruskal_wallis' ||
    type ===
      'anova'
  ) {
    return (
      <div className="analysis-two-column">

        <ColumnSelect
          label="Value Variable"
          columns={columns}
          value={
            form.valueColumn
          }
          onChange={(value) =>
            updateForm(
              'valueColumn',
              value
            )
          }
        />

        <ColumnSelect
          label="Group Variable"
          columns={columns}
          value={
            form.groupColumn
          }
          onChange={(value) =>
            updateForm(
              'groupColumn',
              value
            )
          }
        />

      </div>
    )
  }


  if (
    type ===
    'confidence_interval'
  ) {
    return (
      <div className="analysis-two-column">

        <ColumnSelect
          label="Variable"
          columns={columns}
          value={form.column}
          onChange={(value) =>
            updateForm(
              'column',
              value
            )
          }
        />

        <div>
          <FieldLabel>
            Confidence Level
          </FieldLabel>

          <select
            className="analysis-select"
            value={
              form.confidence
            }
            onChange={(event) =>
              updateForm(
                'confidence',
                event.target.value
              )
            }
          >
            <option value="0.90">
              90%
            </option>

            <option value="0.95">
              95%
            </option>

            <option value="0.99">
              99%
            </option>
          </select>
        </div>

      </div>
    )
  }


  if (
    type ===
    'regression'
  ) {
    return (
      <>
        <div className="analysis-two-column">

          <ColumnSelect
            label="Independent Variable (X)"
            columns={columns}
            value={
              form.xVariable
            }
            onChange={(value) =>
              updateForm(
                'xVariable',
                value
              )
            }
          />

          <ColumnSelect
            label="Dependent Variable (Y)"
            columns={columns}
            value={
              form.yVariable
            }
            onChange={(value) =>
              updateForm(
                'yVariable',
                value
              )
            }
          />

        </div>

        <InfoBox>
          Linear regression should
          normally use numeric
          variables for both X and Y.
        </InfoBox>
      </>
    )
  }


  return null
}


function ColumnSelect({
  label,
  columns,
  value,
  onChange,
}) {
  return (
    <div>
      <FieldLabel>
        {label}
      </FieldLabel>

      <select
        className="analysis-select"
        value={value}
        onChange={(event) =>
          onChange(
            event.target.value
          )
        }
      >
        <option value="">
          Select variable...
        </option>

        {columns.map(
          (column) => (
            <option
              key={column}
              value={column}
            >
              {column}
            </option>
          )
        )}
      </select>
    </div>
  )
}


function FieldLabel({
  children,
}) {
  return (
    <label className="analysis-label">
      {children}
    </label>
  )
}


function TextField({
  label,
  value,
  onChange,
  placeholder,
}) {
  return (
    <div>
      <FieldLabel>
        {label}
      </FieldLabel>

      <input
        className="analysis-input"
        value={value}
        onChange={(event) =>
          onChange(
            event.target.value
          )
        }
        placeholder={placeholder}
      />
    </div>
  )
}


function NumberField({
  label,
  value,
  onChange,
  placeholder,
}) {
  return (
    <div>
      <FieldLabel>
        {label}
      </FieldLabel>

      <input
        className="analysis-input"
        type="number"
        step="any"
        value={value}
        onChange={(event) =>
          onChange(
            event.target.value
          )
        }
        placeholder={placeholder}
      />
    </div>
  )
}


function InfoBox({
  children,
}) {
  return (
    <div className="analysis-info-box">
      <Activity size={18} />
      <p>{children}</p>
    </div>
  )
}


function ResultViewer({
  result,
}) {
  return (
    <div className="result-viewer">

      <div className="result-status">

        <CheckCircle2 size={20} />

        <div>
          <strong>
            Analysis completed
          </strong>

          <span>
            Results returned by SSAS
          </span>
        </div>

      </div>

      <ResultNode
        value={result}
      />

    </div>
  )
}


function ResultNode({
  value,
  name,
}) {

  if (
    value === null ||
    value === undefined
  ) {
    return (
      <ResultValue
        name={name}
        value="-"
      />
    )
  }


  if (
    typeof value !==
    'object'
  ) {
    return (
      <ResultValue
        name={name}
        value={
          formatResultValue(
            value
          )
        }
      />
    )
  }


  if (
    Array.isArray(value)
  ) {
    return (
      <div className="result-array">

        {name && (
          <h4>
            {
              humanize(
                name
              )
            }
          </h4>
        )}

        {value.map(
          (
            item,
            index
          ) => (

            <div
              key={index}
              className="result-array-item"
            >

              <ResultNode
                value={item}
                name={
                  typeof item ===
                  'object'
                    ? `Item ${
                        index + 1
                      }`
                    : undefined
                }
              />

            </div>

          )
        )}

      </div>
    )
  }


  return (
    <div className="result-object">

      {name && (
        <h4>
          {humanize(name)}
        </h4>
      )}

      <div className="result-object-grid">

        {Object.entries(
          value
        ).map(
          ([key, item]) => (

            <ResultNode
              key={key}
              name={key}
              value={item}
            />

          )
        )}

      </div>

    </div>
  )
}


function ResultValue({
  name,
  value,
}) {
  return (
    <div className="result-value-card">

      <span>
        {
          name
            ? humanize(name)
            : 'Value'
        }
      </span>

      <strong>
        {String(value)}
      </strong>

    </div>
  )
}


function humanize(value) {
  return String(value)
    .replaceAll('_', ' ')
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase()
    )
}


function formatResultValue(value) {
  if (
    typeof value ===
    'number'
  ) {
    if (
      Number.isInteger(value)
    ) {
      return value
    }

    return Number(
      value.toFixed(6)
    )
  }

  if (
    typeof value ===
    'boolean'
  ) {
    return value
      ? 'Yes'
      : 'No'
  }

  return value
}


function parseGroupValue(value) {
  const trimmed =
    value.trim()

  if (
    trimmed === ''
  ) {
    return trimmed
  }

  const numeric =
    Number(trimmed)

  if (
    !Number.isNaN(numeric)
  ) {
    return numeric
  }

  return trimmed
}


function requireFields(
  values,
  labels
) {

  const missing =
    Object.entries(values)
      .filter(
        ([, value]) =>
          value === '' ||
          value === null ||
          value === undefined
      )
      .map(
        ([key]) =>
          labels[key] || key
      )


  if (
    missing.length > 0
  ) {
    throw new Error(
      `Please provide: ${
        missing.join(', ')
      }.`
    )
  }
}


function getErrorMessage(
  error,
  fallback
) {

  if (
    error instanceof Error &&
    !error.response
  ) {
    return error.message
  }


  const detail =
    error.response
      ?.data
      ?.detail


  if (
    typeof detail ===
    'string'
  ) {
    return detail
  }


  if (
    Array.isArray(detail)
  ) {
    return detail
      .map(
        (item) =>
          item.msg ||
          JSON.stringify(
            item
          )
      )
      .join(' ')
  }


  return fallback
}
