import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  useSearchParams,
} from 'react-router-dom'

import {
  BarChart3,
  Database,
} from 'lucide-react'

import AppShell
  from '../../components/AppShell'

import api
  from '../../api/api'

import DescriptiveAnalysis
  from './methods/DescriptiveAnalysis'

import HypothesisAnalysis
  from './methods/HypothesisAnalysis'

import CorrelationAnalysis
  from './methods/CorrelationAnalysis'

import RegressionAnalysis
  from './methods/RegressionAnalysis'

import PredictiveAnalysis
  from './methods/PredictiveAnalysis'

import AncovaAnalysis
  from './methods/AncovaAnalysis'

import SurvivalAnalysis
  from './methods/SurvivalAnalysis'

import EfaPcaAnalysis
  from './methods/EfaPcaAnalysis'

import ReliabilityAnalysis
  from './methods/ReliabilityAnalysis'

import ClusterAnalysis
  from './methods/ClusterAnalysis'

import './AnalysisPage.css'


// ==========================================================
// STATISTICAL METHODS
// ==========================================================

const ANALYSIS_METHODS = [
  {
    key: 'descriptive',
    label: 'Descriptive Statistics',
  },
  {
    key: 'hypothesis',
    label: 'Hypothesis Tests',
  },
  {
    key: 'correlation',
    label: 'Correlation',
  },
  {
    key: 'regression',
    label: 'Regression',
  },
  {
    key: 'predictive',
    label: 'Predictive Analytics',
  },
  {
    key: 'ancova',
    label: 'ANCOVA',
  },
  {
    key: 'survival',
    label: 'Survival Analysis',
  },
  {
    key: 'factor',
    label: 'EFA / PCA',
  },
  {
    key: 'reliability',
    label: 'Reliability',
  },
  {
    key: 'cluster',
    label: 'Cluster',
  },
  {
    key: 'msa',
    label: 'MSA',
  },
  {
    key: 'capability',
    label: 'Process Capability',
  },
  {
    key: 'spc',
    label: 'SPC',
  },
  {
    key: 'doe',
    label: 'DoE',
  },
]


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
    'Unable to load datasets.'
  )
}


// ==========================================================
// VALID ANALYSIS METHOD
// ==========================================================

function getValidMethod(
  method
) {
  const exists =
    ANALYSIS_METHODS.some(
      (
        item
      ) =>
        item.key ===
        method
    )


  if (
    exists
  ) {
    return method
  }


  return 'descriptive'
}


// ==========================================================
// MAIN ANALYSIS PAGE
// ==========================================================

export default function AnalysisPage() {

  // ========================================================
  // URL SEARCH PARAMETERS
  // ========================================================

  const [
    searchParams,
    setSearchParams,
  ] = useSearchParams()


  const methodFromUrl =
    searchParams.get(
      'method'
    )


  // ========================================================
  // DATASET STATE
  // ========================================================

  const [
    datasets,
    setDatasets,
  ] = useState([])


  const [
    selectedDatasetId,
    setSelectedDatasetId,
  ] = useState('')


  // ========================================================
  // ACTIVE ANALYSIS METHOD
  // ========================================================

  const [
    activeMethod,
    setActiveMethod,
  ] = useState(
    () =>
      getValidMethod(
        methodFromUrl
      )
  )


  // ========================================================
  // GENERAL PAGE STATE
  // ========================================================

  const [
    loading,
    setLoading,
  ] = useState(true)


  const [
    error,
    setError,
  ] = useState('')


  // ========================================================
  // LOAD DATASETS
  // ========================================================

  useEffect(
    () => {

      const loadDatasets =
        async () => {

          setLoading(
            true
          )

          setError(
            ''
          )


          try {

            const response =
              await api.get(
                '/datasets'
              )


            const loaded =
              response
                .data
                ?.datasets
              ||
              []


            setDatasets(
              loaded
            )


            if (
              loaded.length
              >
              0
            ) {

              setSelectedDatasetId(
                (
                  current
                ) => {

                  const currentStillExists =
                    loaded.some(
                      (
                        dataset
                      ) =>
                        dataset.id
                        ===
                        current
                    )


                  if (
                    current
                    &&
                    currentStillExists
                  ) {
                    return current
                  }


                  return (
                    loaded[
                      0
                    ].id
                  )
                }
              )
            }

            else {

              setSelectedDatasetId(
                ''
              )
            }

          } catch (
            err
          ) {

            setError(
              getErrorMessage(
                err
              )
            )

          } finally {

            setLoading(
              false
            )
          }
        }


      loadDatasets()

    },

    []
  )


  // ========================================================
  // SYNC METHOD FROM URL
  // ========================================================

  useEffect(
    () => {

      if (
        !methodFromUrl
      ) {
        return
      }


      const validMethod =
        getValidMethod(
          methodFromUrl
        )


      if (
        validMethod
        !==
        activeMethod
      ) {

        setActiveMethod(
          validMethod
        )
      }

    },

    [
      methodFromUrl,
      activeMethod,
    ]
  )


  // ========================================================
  // SELECTED DATASET
  // ========================================================

  const selectedDataset =
    useMemo(
      () =>

        datasets.find(
          (
            dataset
          ) =>
            dataset.id
            ===
            selectedDatasetId
        )
        ||
        null,

      [
        datasets,
        selectedDatasetId,
      ]
    )


  // ========================================================
  // CURRENT METHOD INFORMATION
  // ========================================================

  const currentMethod =
    useMemo(
      () =>

        ANALYSIS_METHODS.find(
          (
            method
          ) =>
            method.key
            ===
            activeMethod
        )
        ||
        ANALYSIS_METHODS[
          0
        ],

      [
        activeMethod,
      ]
    )


  // ========================================================
  // CHANGE METHOD
  // ========================================================

  const changeMethod =
    (
      methodKey
    ) => {

      const validMethod =
        getValidMethod(
          methodKey
        )


      setActiveMethod(
        validMethod
      )


      setSearchParams({
        method:
          validMethod,
      })
    }


  // ========================================================
  // RENDER ACTIVE METHOD
  // ========================================================

  const renderMethod =
    () => {

      // ----------------------------------------------------
      // NO DATASET
      // ----------------------------------------------------

      if (
        !selectedDataset
      ) {

        return (

          <div className="analysis-no-dataset">


            <Database
              size={34}
            />


            <h3>
              Select a dataset
            </h3>


            <p>

              A dataset is required
              before statistical
              analysis can be performed.

            </p>

          </div>

        )
      }


      // ----------------------------------------------------
      // DESCRIPTIVE STATISTICS
      // ----------------------------------------------------

      if (
        activeMethod ===
        'descriptive'
      ) {

        return (

          <DescriptiveAnalysis
            dataset={
              selectedDataset
            }
          />

        )
      }


      // ----------------------------------------------------
      // HYPOTHESIS TESTS
      // ----------------------------------------------------

      if (
        activeMethod ===
        'hypothesis'
      ) {

        return (

          <HypothesisAnalysis
            dataset={
              selectedDataset
            }
          />

        )
      }


      // ----------------------------------------------------
      // CORRELATION
      // ----------------------------------------------------

      if (
        activeMethod ===
        'correlation'
      ) {

        return (

          <CorrelationAnalysis
            dataset={
              selectedDataset
            }
          />

        )
      }


      // ----------------------------------------------------
      // REGRESSION
      // ----------------------------------------------------

      if (
        activeMethod ===
        'regression'
      ) {

        return (

          <RegressionAnalysis
            dataset={
              selectedDataset
            }
          />

        )
      }


      // ----------------------------------------------------
      // PREDICTIVE ANALYTICS
      // ----------------------------------------------------

      if (
        activeMethod ===
        'predictive'
      ) {

        return (

          <PredictiveAnalysis
            dataset={
              selectedDataset
            }
          />

        )
      }


      // ----------------------------------------------------
      // ANCOVA
      // ----------------------------------------------------

      if (
        activeMethod ===
        'ancova'
      ) {

        return (

          <AncovaAnalysis
            dataset={
              selectedDataset
            }
          />

        )
      }


      // ----------------------------------------------------
      // SURVIVAL ANALYSIS
      // ----------------------------------------------------

      if (
        activeMethod ===
        'survival'
      ) {

        return (

          <SurvivalAnalysis
            dataset={
              selectedDataset
            }
          />

        )
      }


      // ----------------------------------------------------
      // EFA / PCA
      //
      // IMPORTANT:
      // The menu key is "factor".
      // Do not use "efa-pca" here.
      // ----------------------------------------------------

      if (
        activeMethod ===
        'factor'
      ) {

        return (

          <EfaPcaAnalysis
            dataset={
              selectedDataset
            }
          />

        )
      }


      // ----------------------------------------------------
      // RELIABILITY ANALYSIS
      // ----------------------------------------------------

      if (
        activeMethod ===
        'reliability'
      ) {

        return (

          <ReliabilityAnalysis
            dataset={
              selectedDataset
            }
          />

        )
      }


      // ----------------------------------------------------
      // CLUSTER ANALYSIS
      // ----------------------------------------------------

      if (
        activeMethod ===
        'cluster'
      ) {

        return (

          <ClusterAnalysis
            dataset={
              selectedDataset
            }
          />

        )
      }


      // ----------------------------------------------------
      // NOT YET IMPLEMENTED
      // ----------------------------------------------------

      return (

        <div className="analysis-method-placeholder">


          <h2>
            {
              currentMethod
                ?.label
            }
          </h2>


          <p>

            This statistical method
            will use the same SSAS
            configuration, structured
            result tables,
            interpretation and
            explanation workflow.

          </p>


          <div className="analysis-method-placeholder-note">

            This statistical method
            has not yet been
            implemented.

          </div>

        </div>

      )
    }


  // ========================================================
  // RENDER PAGE
  // ========================================================

  return (

    <AppShell>


      <div className="analysis-page">


        {/* ==================================================
            PAGE HEADER
            ================================================== */}

        <header className="analysis-page-header">


          <div>


            <span className="analysis-eyebrow">

              STATISTICAL ANALYSIS

            </span>


            <h1>
              Statistical Analysis
            </h1>


            <p>

              Configure statistical
              methods, calculate
              results and review them
              in structured tables.

            </p>

          </div>

        </header>


        {/* ==================================================
            PAGE ERROR
            ================================================== */}

        {error && (

          <div className="analysis-error">

            {error}

          </div>

        )}


        {/* ==================================================
            DATASET SELECTOR
            ================================================== */}

        <section className="analysis-dataset-selector">


          <div className="analysis-dataset-icon">


            <Database
              size={20}
            />


          </div>


          <div className="analysis-dataset-content">


            <label>
              Dataset
            </label>


            <select
              value={
                selectedDatasetId
              }

              disabled={
                loading
              }

              onChange={
                (
                  event
                ) =>
                  setSelectedDatasetId(
                    event
                      .target
                      .value
                  )
              }
            >


              {!datasets.length && (

                <option value="">

                  {
                    loading
                      ?
                      'Loading datasets...'
                      :
                      'No datasets available'
                  }

                </option>

              )}


              {datasets.map(
                (
                  dataset
                ) => (

                  <option
                    key={
                      dataset.id
                    }

                    value={
                      dataset.id
                    }
                  >

                    {
                      dataset
                        .original_filename
                      ||
                      dataset
                        .filename
                      ||
                      'Dataset'
                    }

                  </option>

                )
              )}

            </select>


            {selectedDataset && (

              <span className="analysis-dataset-summary">


                {
                  selectedDataset
                    .row_count
                  ??
                  0
                }


                {' rows · '}


                {
                  selectedDataset
                    .column_count
                  ??
                  0
                }


                {' columns'}

              </span>

            )}

          </div>

        </section>


        {/* ==================================================
            STATISTICAL METHOD MENU
            ================================================== */}

        <nav className="analysis-method-menu">


          {ANALYSIS_METHODS.map(
            (
              method
            ) => (

              <button
                key={
                  method.key
                }

                type="button"

                className={
                  activeMethod
                  ===
                  method.key
                    ?
                    'active'
                    :
                    ''
                }

                onClick={() =>
                  changeMethod(
                    method.key
                  )
                }
              >

                {
                  method.label
                }

              </button>

            )
          )}

        </nav>


        {/* ==================================================
            ACTIVE ANALYSIS METHOD
            ================================================== */}

        <main className="analysis-workspace">


          {/* METHOD TITLE */}

          <div className="analysis-workspace-title">


            <BarChart3
              size={19}
            />


            <div>


              <span>
                Analysis Method
              </span>


              <h2>

                {
                  currentMethod
                    ?.label
                }

              </h2>

            </div>

          </div>


          {/* ACTIVE COMPONENT */}

          {
            renderMethod()
          }

        </main>

      </div>

    </AppShell>

  )
}
