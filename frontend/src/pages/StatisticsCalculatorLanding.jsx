import {
  useMemo,
  useState,
} from 'react'

import {
  ArrowRight,
  BarChart3,
  Database,
  FileText,
  LogOut,
  Search,
  User,
  X,
} from 'lucide-react'

import {
  useLocation,
  useNavigate,
} from 'react-router-dom'

import {
  useAuth,
} from '../context/AuthContext'

import './StatisticsCalculatorLanding.css'


// ==========================================================
// STATISTICAL METHODS
// ==========================================================

const STATISTICAL_METHODS = [

  // ========================================================
  // DATA PREPARATION
  // ========================================================

  {
    label:
      'Prepare Data',

    category:
      'Data Preparation',

    keywords: [
      'clean',
      'prepare',
      'missing',
      'dataset',
      'preprocessing',
      'upload',
      'data',
    ],

    path:
      '/datasets',
  },


  // ========================================================
  // DESCRIPTIVE STATISTICS
  // ========================================================

  {
    label:
      'Descriptive Statistics',

    category:
      'Descriptive Statistics',

    keywords: [
      'summary',
      'describe',
      'statistics',
    ],

    path:
      '/analysis?method=descriptive',
  },


  {
    label:
      'Mean',

    category:
      'Descriptive Statistics',

    keywords: [
      'average',
      'arithmetic mean',
    ],

    path:
      '/analysis?method=descriptive',
  },


  {
    label:
      'Median',

    category:
      'Descriptive Statistics',

    keywords: [
      'middle',
      'central tendency',
    ],

    path:
      '/analysis?method=descriptive',
  },


  {
    label:
      'Mode',

    category:
      'Descriptive Statistics',

    keywords: [
      'frequency',
      'most common',
    ],

    path:
      '/analysis?method=descriptive',
  },


  {
    label:
      'Mean, Median, Mode',

    category:
      'Descriptive Statistics',

    keywords: [
      'central tendency',
      'average',
    ],

    path:
      '/analysis?method=descriptive',
  },


  {
    label:
      'Standard Deviation',

    category:
      'Descriptive Statistics',

    keywords: [
      'sd',
      'spread',
      'dispersion',
    ],

    path:
      '/analysis?method=descriptive',
  },


  {
    label:
      'Variance',

    category:
      'Descriptive Statistics',

    keywords: [
      'spread',
      'dispersion',
    ],

    path:
      '/analysis?method=descriptive',
  },


  {
    label:
      'Range',

    category:
      'Descriptive Statistics',

    keywords: [
      'minimum',
      'maximum',
      'spread',
    ],

    path:
      '/analysis?method=descriptive',
  },


  {
    label:
      'Quartiles',

    category:
      'Descriptive Statistics',

    keywords: [
      'q1',
      'q2',
      'q3',
      'percentile',
    ],

    path:
      '/analysis?method=descriptive',
  },


  {
    label:
      'Skewness and Kurtosis',

    category:
      'Descriptive Statistics',

    keywords: [
      'skew',
      'kurtosis',
      'distribution',
      'shape',
    ],

    path:
      '/analysis?method=descriptive',
  },


  {
    label:
      'Frequency Table',

    category:
      'Descriptive Statistics',

    keywords: [
      'frequency',
      'count',
      'table',
    ],

    path:
      '/analysis?method=descriptive',
  },


  {
    label:
      'Confidence Interval for Mean',

    category:
      'Descriptive Statistics',

    keywords: [
      'confidence interval',
      'ci',
      'mean',
    ],

    path:
      '/analysis?method=descriptive',
  },


  {
    label:
      'Normality Test',

    category:
      'Descriptive Statistics',

    keywords: [
      'normal distribution',
      'normality',
      'shapiro',
    ],

    path:
      '/analysis?method=descriptive',
  },


  {
    label:
      'Shapiro-Wilk Test',

    category:
      'Descriptive Statistics',

    keywords: [
      'normality',
      'normal distribution',
      'shapiro',
    ],

    path:
      '/analysis?method=descriptive',
  },


  {
    label:
      'Kolmogorov-Smirnov Test',

    category:
      'Descriptive Statistics',

    keywords: [
      'normality',
      'distribution',
      'kolmogorov',
    ],

    path:
      '/analysis?method=descriptive',
  },


  // ========================================================
  // HYPOTHESIS TESTING
  // ========================================================

  {
    label:
      'Hypothesis Testing',

    category:
      'Hypothesis Tests',

    keywords: [
      'hypothesis',
      'significance',
      'p value',
    ],

    path:
      '/analysis?method=hypothesis',
  },


  {
    label:
      'p-Value',

    category:
      'Hypothesis Tests',

    keywords: [
      'significance',
      'probability',
    ],

    path:
      '/analysis?method=hypothesis',
  },


  {
    label:
      'One Sample t-Test',

    category:
      'Hypothesis Tests',

    keywords: [
      't test',
      'one sample',
      'mean',
    ],

    path:
      '/analysis?method=hypothesis',
  },


  {
    label:
      'Independent Samples t-Test',

    category:
      'Hypothesis Tests',

    keywords: [
      'independent',
      'two sample',
      't test',
    ],

    path:
      '/analysis?method=hypothesis',
  },


  {
    label:
      'Paired Samples t-Test',

    category:
      'Hypothesis Tests',

    keywords: [
      'paired',
      'dependent',
      'before after',
      't test',
    ],

    path:
      '/analysis?method=hypothesis',
  },


  {
    label:
      'Mann-Whitney U Test',

    category:
      'Hypothesis Tests',

    keywords: [
      'nonparametric',
      'independent',
      'groups',
    ],

    path:
      '/analysis?method=hypothesis',
  },


  {
    label:
      'Wilcoxon Signed-Rank Test',

    category:
      'Hypothesis Tests',

    keywords: [
      'wilcoxon',
      'nonparametric',
      'paired',
    ],

    path:
      '/analysis?method=hypothesis',
  },


  {
    label:
      'Chi-Square Test',

    category:
      'Hypothesis Tests',

    keywords: [
      'chi square',
      'categorical',
      'association',
    ],

    path:
      '/analysis?method=hypothesis',
  },


  {
    label:
      'ANOVA',

    category:
      'Hypothesis Tests',

    keywords: [
      'analysis variance',
      'groups',
      'means',
    ],

    path:
      '/analysis?method=hypothesis',
  },


  {
    label:
      'One-Way ANOVA',

    category:
      'Hypothesis Tests',

    keywords: [
      'anova',
      'one factor',
    ],

    path:
      '/analysis?method=hypothesis',
  },


  {
    label:
      'Kruskal-Wallis Test',

    category:
      'Hypothesis Tests',

    keywords: [
      'kruskal',
      'nonparametric',
      'anova',
      'groups',
    ],

    path:
      '/analysis?method=hypothesis',
  },


  {
    label:
      'Friedman Test',

    category:
      'Hypothesis Tests',

    keywords: [
      'friedman',
      'nonparametric',
      'repeated measures',
    ],

    path:
      '/analysis?method=hypothesis',
  },


  // ========================================================
  // CORRELATION
  // ========================================================

  {
    label:
      'Correlation',

    category:
      'Correlation',

    keywords: [
      'relationship',
      'association',
    ],

    path:
      '/analysis?method=correlation',
  },


  {
    label:
      'Pearson Correlation',

    category:
      'Correlation',

    keywords: [
      'pearson',
      'linear',
      'correlation',
    ],

    path:
      '/analysis?method=correlation',
  },


  {
    label:
      'Spearman Correlation',

    category:
      'Correlation',

    keywords: [
      'spearman',
      'rank',
      'ordinal',
    ],

    path:
      '/analysis?method=correlation',
  },


  {
    label:
      'Kendall Correlation',

    category:
      'Correlation',

    keywords: [
      'kendall',
      'tau',
      'rank',
    ],

    path:
      '/analysis?method=correlation',
  },


  {
    label:
      'Correlation Matrix',

    category:
      'Correlation',

    keywords: [
      'matrix',
      'correlation',
    ],

    path:
      '/analysis?method=correlation',
  },


  // ========================================================
  // REGRESSION
  // ========================================================

  {
    label:
      'Regression',

    category:
      'Regression',

    keywords: [
      'regression',
      'prediction',
      'relationship',
    ],

    path:
      '/analysis?method=regression',
  },


  {
    label:
      'Linear Regression',

    category:
      'Regression',

    keywords: [
      'ols',
      'linear model',
    ],

    path:
      '/analysis?method=regression',
  },


  {
    label:
      'Multiple Linear Regression',

    category:
      'Regression',

    keywords: [
      'multiple regression',
      'predictors',
    ],

    path:
      '/analysis?method=regression',
  },


  {
    label:
      'Regression Diagnostics',

    category:
      'Regression',

    keywords: [
      'vif',
      'residual',
      'diagnostics',
    ],

    path:
      '/analysis?method=regression',
  },


  // ========================================================
  // PREDICTIVE ANALYTICS
  // ========================================================

  {
    label:
      'Predictive Analytics',

    category:
      'Predictive Analytics',

    keywords: [
      'future',
      'prediction',
      'machine learning',
    ],

    path:
      '/analysis?method=predictive',
  },


  {
    label:
      'Decision Tree',

    category:
      'Predictive Analytics',

    keywords: [
      'machine learning',
      'tree',
      'prediction',
    ],

    path:
      '/analysis?method=predictive',
  },


  {
    label:
      'Random Forest',

    category:
      'Predictive Analytics',

    keywords: [
      'machine learning',
      'forest',
      'prediction',
    ],

    path:
      '/analysis?method=predictive',
  },


  {
    label:
      'Gradient Boosting',

    category:
      'Predictive Analytics',

    keywords: [
      'boosting',
      'machine learning',
      'prediction',
    ],

    path:
      '/analysis?method=predictive',
  },


  // ========================================================
  // ANCOVA
  // ========================================================

  {
    label:
      'ANCOVA',

    category:
      'ANCOVA',

    keywords: [
      'analysis covariance',
      'covariate',
      'adjusted means',
    ],

    path:
      '/analysis?method=ancova',
  },


  {
    label:
      'Analysis of Covariance',

    category:
      'ANCOVA',

    keywords: [
      'ancova',
      'covariate',
    ],

    path:
      '/analysis?method=ancova',
  },


  // ========================================================
  // SURVIVAL
  // ========================================================

  {
    label:
      'Survival Analysis',

    category:
      'Survival Analysis',

    keywords: [
      'survival',
      'time to event',
      'censoring',
    ],

    path:
      '/analysis?method=survival',
  },


  {
    label:
      'Kaplan-Meier Analysis',

    category:
      'Survival Analysis',

    keywords: [
      'kaplan meier',
      'survival',
    ],

    path:
      '/analysis?method=survival',
  },


  {
    label:
      'Log-Rank Test',

    category:
      'Survival Analysis',

    keywords: [
      'log rank',
      'survival groups',
    ],

    path:
      '/analysis?method=survival',
  },


  // ========================================================
  // EFA / PCA
  // ========================================================

  {
    label:
      'EFA / PCA',

    category:
      'EFA / PCA',

    keywords: [
      'factor',
      'principal components',
      'dimension reduction',
    ],

    path:
      '/analysis?method=factor',
  },


  {
    label:
      'Exploratory Factor Analysis',

    category:
      'EFA / PCA',

    keywords: [
      'efa',
      'factor analysis',
      'latent',
    ],

    path:
      '/analysis?method=factor',
  },


  {
    label:
      'Principal Component Analysis',

    category:
      'EFA / PCA',

    keywords: [
      'pca',
      'principal component',
      'dimension reduction',
    ],

    path:
      '/analysis?method=factor',
  },


  {
    label:
      'KMO Test',

    category:
      'EFA / PCA',

    keywords: [
      'kaiser meyer olkin',
      'factorability',
    ],

    path:
      '/analysis?method=factor',
  },


  {
    label:
      "Bartlett's Test of Sphericity",

    category:
      'EFA / PCA',

    keywords: [
      'bartlett',
      'factorability',
    ],

    path:
      '/analysis?method=factor',
  },


  // ========================================================
  // RELIABILITY
  // ========================================================

  {
    label:
      'Reliability Analysis',

    category:
      'Reliability',

    keywords: [
      'reliability',
      'internal consistency',
      'questionnaire',
    ],

    path:
      '/analysis?method=reliability',
  },


  {
    label:
      "Cronbach's Alpha",

    category:
      'Reliability',

    keywords: [
      'cronbach',
      'alpha',
      'internal consistency',
    ],

    path:
      '/analysis?method=reliability',
  },


  {
    label:
      'Item-Total Correlation',

    category:
      'Reliability',

    keywords: [
      'reliability',
      'item total',
    ],

    path:
      '/analysis?method=reliability',
  },


  {
    label:
      'Split-Half Reliability',

    category:
      'Reliability',

    keywords: [
      'split half',
      'spearman brown',
    ],

    path:
      '/analysis?method=reliability',
  },


  // ========================================================
  // CLUSTER ANALYSIS
  // ========================================================

  {
    label:
      'Cluster Analysis',

    category:
      'Cluster',

    keywords: [
      'clustering',
      'groups',
      'segmentation',
    ],

    path:
      '/analysis?method=cluster',
  },


  {
    label:
      'K-Means Clustering',

    category:
      'Cluster',

    keywords: [
      'kmeans',
      'cluster',
      'segmentation',
    ],

    path:
      '/analysis?method=cluster',
  },


  {
    label:
      'Hierarchical Clustering',

    category:
      'Cluster',

    keywords: [
      'hierarchical',
      'ward',
      'agglomerative',
    ],

    path:
      '/analysis?method=cluster',
  },


  {
    label:
      'Silhouette Analysis',

    category:
      'Cluster',

    keywords: [
      'silhouette',
      'cluster quality',
    ],

    path:
      '/analysis?method=cluster',
  },


  // ========================================================
  // MSA
  // ========================================================

  {
    label:
      'Measurement System Analysis',

    category:
      'MSA',

    keywords: [
      'msa',
      'measurement',
      'gage',
      'gauge',
    ],

    path:
      '/analysis?method=msa',
  },


  {
    label:
      'Gage R&R',

    category:
      'MSA',

    keywords: [
      'gauge',
      'repeatability',
      'reproducibility',
    ],

    path:
      '/analysis?method=msa',
  },


  // ========================================================
  // PROCESS CAPABILITY
  // ========================================================

  {
    label:
      'Process Capability',

    category:
      'Process Capability',

    keywords: [
      'cp',
      'cpk',
      'capability',
      'process',
    ],

    path:
      '/analysis?method=capability',
  },


  {
    label:
      'Cp',

    category:
      'Process Capability',

    keywords: [
      'process capability',
    ],

    path:
      '/analysis?method=capability',
  },


  {
    label:
      'Cpk',

    category:
      'Process Capability',

    keywords: [
      'process capability index',
    ],

    path:
      '/analysis?method=capability',
  },


  // ========================================================
  // SPC
  // ========================================================

  {
    label:
      'Statistical Process Control',

    category:
      'SPC',

    keywords: [
      'spc',
      'control chart',
      'process monitoring',
    ],

    path:
      '/analysis?method=spc',
  },


  {
    label:
      'Control Charts',

    category:
      'SPC',

    keywords: [
      'spc',
      'control limits',
    ],

    path:
      '/analysis?method=spc',
  },


  // ========================================================
  // DOE
  // ========================================================

  {
    label:
      'Design of Experiments',

    category:
      'DoE',

    keywords: [
      'doe',
      'experiment',
      'factorial',
    ],

    path:
      '/analysis?method=doe',
  },


  {
    label:
      'Factorial Design',

    category:
      'DoE',

    keywords: [
      'doe',
      'factorial',
      'experiment',
    ],

    path:
      '/analysis?method=doe',
  },


  // ========================================================
  // VISUALIZATIONS
  // ========================================================

  {
    label:
      'Charts and Visualization',

    category:
      'Visualization',

    keywords: [
      'graph',
      'chart',
      'plot',
    ],

    path:
      '/visualizations',
  },


  {
    label:
      'Bar Chart',

    category:
      'Visualization',

    keywords: [
      'bar',
      'chart',
    ],

    path:
      '/visualizations',
  },


  {
    label:
      'Histogram',

    category:
      'Visualization',

    keywords: [
      'distribution',
      'histogram',
    ],

    path:
      '/visualizations',
  },


  {
    label:
      'Scatter Plot',

    category:
      'Visualization',

    keywords: [
      'scatter',
      'correlation',
      'plot',
    ],

    path:
      '/visualizations',
  },


  {
    label:
      'Line Chart',

    category:
      'Visualization',

    keywords: [
      'line',
      'time series',
      'chart',
    ],

    path:
      '/visualizations',
  },


  {
    label:
      'Boxplot',

    category:
      'Visualization',

    keywords: [
      'box plot',
      'outlier',
      'distribution',
    ],

    path:
      '/visualizations',
  },


  {
    label:
      'Violin Plot',

    category:
      'Visualization',

    keywords: [
      'violin',
      'distribution',
    ],

    path:
      '/visualizations',
  },


  {
    label:
      'Q-Q Plot',

    category:
      'Visualization',

    keywords: [
      'qq',
      'quantile',
      'normality',
    ],

    path:
      '/visualizations',
  },

]


// ==========================================================
// NORMALIZE SEARCH
// ==========================================================

function normalizeSearchText(
  value
) {

  return String(
    value ||
    ''
  )
    .trim()
    .toLowerCase()
}


// ==========================================================
// SEARCH SCORE
// ==========================================================

function getMatchScore(
  item,
  query
) {

  const normalizedQuery =
    normalizeSearchText(
      query
    )


  const label =
    normalizeSearchText(
      item.label
    )


  const category =
    normalizeSearchText(
      item.category
    )


  const keywords =
    item.keywords
      .map(
        normalizeSearchText
      )
      .join(
        ' '
      )


  if (
    !normalizedQuery
  ) {

    return 1
  }


  if (
    label ===
    normalizedQuery
  ) {

    return 100
  }


  if (
    label.startsWith(
      normalizedQuery
    )
  ) {

    return 80
  }


  if (
    label.includes(
      normalizedQuery
    )
  ) {

    return 60
  }


  if (
    category.includes(
      normalizedQuery
    )
  ) {

    return 40
  }


  if (
    keywords.includes(
      normalizedQuery
    )
  ) {

    return 30
  }


  const words =
    normalizedQuery.split(
      /\s+/
    )


  const searchable =
    `
      ${label}
      ${category}
      ${keywords}
    `


  const matches =
    words.every(
      (
        word
      ) =>
        searchable.includes(
          word
        )
    )


  return (
    matches
      ?
      20
      :
      0
  )
}


// ==========================================================
// MAIN COMPONENT
// ==========================================================

export default function StatisticsCalculatorLanding() {

  const navigate =
    useNavigate()


  const location =
    useLocation()


  const isDashboard =
    location.pathname ===
    '/dashboard'

  const {
    user,
    logout,
  } = useAuth()


  const [
    query,
    setQuery,
  ] = useState('')


  const [
    searchFocused,
    setSearchFocused,
  ] = useState(false)


  // ========================================================
  // FILTER METHODS
  // ========================================================

  const filteredMethods =
    useMemo(
      () => {

        const normalizedQuery =
          normalizeSearchText(
            query
          )


        if (
          !normalizedQuery
        ) {

          return (
            STATISTICAL_METHODS
          )
        }


        return (
          STATISTICAL_METHODS
            .map(
              (
                item
              ) => ({
                ...item,

                score:
                  getMatchScore(
                    item,
                    normalizedQuery
                  ),
              })
            )
            .filter(
              (
                item
              ) =>
                item.score
                >
                0
            )
            .sort(
              (
                first,
                second
              ) =>
                second.score
                -
                first.score
            )
        )

      },

      [
        query,
      ]
    )


  // ========================================================
  // SUGGESTIONS
  // ========================================================

  const suggestions =
    useMemo(
      () => {

        if (
          !query.trim()
        ) {

          return []
        }


        return (
          filteredMethods.slice(
            0,
            8
          )
        )

      },

      [
        query,
        filteredMethods,
      ]
    )


  // ========================================================
  // OPEN METHOD
  // ========================================================

  const openMethod =
    (
      item
    ) => {

      if (
        !item
      ) {

        return
      }


      setSearchFocused(
        false
      )


      navigate(
        item.path
      )
    }


  // ========================================================
  // SEARCH SUBMIT
  // ========================================================

  const handleSubmit =
    (
      event
    ) => {

      event.preventDefault()


      if (
        filteredMethods.length
        >
        0
      ) {

        openMethod(
          filteredMethods[
            0
          ]
        )
      }
    }


  // ========================================================
  // CLEAR SEARCH
  // ========================================================

  const clearSearch =
    () => {

      setQuery(
        ''
      )


      setSearchFocused(
        true
      )
    }


  // ========================================================
  // LOGOUT
  // ========================================================

  const handleLogout =
    async () => {

      try {

        await logout()

      } finally {

        navigate(
          '/'
        )
      }
    }


  // ========================================================
  // SCROLL TO SEARCH
  // ========================================================

  const focusSearch =
    () => {

      const search =
        document.getElementById(
          'statistics-method-search'
        )


      if (
        !search
      ) {

        return
      }


      search.scrollIntoView({
        behavior:
          'smooth',

        block:
          'center',
      })


      window.setTimeout(
        () => {

          search.focus()

        },

        350
      )
    }


  // ========================================================
  // RENDER
  // ========================================================

return (

  <div
    className={
      isDashboard
        ?
        'statistics-calculator-page dashboard-video-mode'
        :
        'statistics-calculator-page'
    }
  >


    {/* ==================================================
        DASHBOARD VIDEO BACKGROUND
        ================================================== */}

    {isDashboard && (

      <div
        className="dashboard-video-background"
        aria-hidden="true"
      >

        <video
          className="dashboard-background-video"
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
        >

          <source
            src="/videos/dashboard-bg.mp4"
            type="video/mp4"
          />

        </video>


        <div className="dashboard-video-overlay" />

      </div>

    )}


    <div className="dashboard-video-content">

      {/* ==================================================
          HEADER
          ================================================== */}

      <header className="statistics-calculator-header">


        {/* LOGO */}

        <button
          type="button"

          className="statistics-calculator-brand"

          onClick={() =>
            navigate(
              user
                ?
                '/dashboard'
                :
                '/'
            )
          }
        >

          <BarChart3
            size={38}
          />


          <div>

            <strong>
              SSAS
            </strong>


            <span>
              Smart Statistical Analysis System
            </span>

          </div>

        </button>


        {/* NAVIGATION */}

        <nav className="statistics-calculator-navigation">


          <button
            type="button"

            className="active"

            onClick={() =>
              navigate(
                user
                  ?
                  '/dashboard'
                  :
                  '/'
              )
            }
          >

            Statistics Calculator

          </button>


          {user && (

            <button
              type="button"

              onClick={() =>
                navigate(
                  '/datasets'
                )
              }
            >

       {user && (

  <button
    type="button"

    onClick={() =>
      navigate(
        '/survey'
      )
    }
  >

    Survey

  </button>

)} 
             Datasets

            </button>

          )}


          <button
            type="button"

            onClick={() =>
              navigate(
                '/analysis'
              )
            }
          >

            Analysis

          </button>


          <button
            type="button"

            onClick={() =>
              navigate(
                '/visualizations'
              )
            }
          >

            Visualization

          </button>


          {user && (

            <button
              type="button"

              onClick={() =>
                navigate(
                  '/reports'
                )
              }
            >

              Reports

            </button>

          )}


          {user && (

            <button
              type="button"

              onClick={() =>
                navigate(
                  '/notifications'
                )
              }
            >

              Notifications

            </button>

          )}

        </nav>


        {/* USER / LOGIN */}

        <div className="statistics-calculator-header-actions">


          {user ? (

            <>

              <button
                type="button"

                onClick={() =>
                  navigate(
                    '/datasets'
                  )
                }
              >

                <User
                  size={18}
                />

                {
                  user.username
                  ||
                  'Workspace'
                }

              </button>


              <button
                type="button"

                onClick={
                  handleLogout
                }
              >

                <LogOut
                  size={18}
                />

                Sign out

              </button>

            </>

          ) : (

            <button
              type="button"

              onClick={() =>
                navigate(
                  '/login'
                )
              }
            >

              Login

            </button>

          )}


          <Search
            size={22}

            onClick={
              focusSearch
            }

            style={{
              cursor:
                'pointer',
            }}
          />

        </div>

      </header>


      {/* ==================================================
          HERO
          ================================================== */}

      <section className="statistics-calculator-hero">


        <div className="statistics-calculator-hero-content">


          <span className="statistics-calculator-eyebrow">

            SMART STATISTICAL ANALYSIS SYSTEM

          </span>


          <h1>

            Statistics Calculator

          </h1>


          <p>

            Select or search for a statistical method
            and SSAS will take you directly to the
            appropriate analysis workflow.

          </p>


          <button
            type="button"

            className="statistics-start-button"

            onClick={
              focusSearch
            }
          >

            Start now


            <ArrowRight
              size={18}
            />

          </button>

        </div>

      </section>


      {/* ==================================================
          SEARCH / METHOD DISCOVERY
          ================================================== */}

      <main className="statistics-calculator-content">


        <section className="statistics-method-discovery">


          {/* HEADING */}

          <div className="statistics-method-heading">


            <span>

              FIND AN ANALYSIS

            </span>


            <h2>

              What do you want to calculate?

            </h2>


            <p>

              Search by statistical method,
              test name, purpose or keyword.

            </p>

          </div>


          {/* =================================================
              SEARCH
              ================================================= */}

          <div className="statistics-search-wrapper">


            <form
              className={
                searchFocused
                  ?
                  'statistics-search-box focused'
                  :
                  'statistics-search-box'
              }

              onSubmit={
                handleSubmit
              }
            >


              <Search
                size={22}
              />


              <input
                id="statistics-method-search"

                type="text"

                autoComplete="off"

                placeholder="What do you want to calculate?"

                value={
                  query
                }

                onFocus={() =>
                  setSearchFocused(
                    true
                  )
                }

                onChange={
                  (
                    event
                  ) =>
                    setQuery(
                      event
                        .target
                        .value
                    )
                }
              />


              {query && (

                <button
                  type="button"

                  className="statistics-search-clear"

                  aria-label="Clear search"

                  onClick={
                    clearSearch
                  }
                >

                  <X
                    size={18}
                  />

                </button>

              )}

            </form>


            {/* =================================================
                LIVE SEARCH SUGGESTIONS
                ================================================= */}

            {
              searchFocused
              &&
              query.trim()
              &&
              (

                <div className="statistics-search-suggestions">


                  {
                    suggestions.length
                    >
                    0
                      ?
                      (

                        suggestions.map(
                          (
                            item,
                            index
                          ) => (

                            <button
                              key={
                                `${
                                  item.label
                                }-${
                                  index
                                }`
                              }

                              type="button"

                              onMouseDown={
                                (
                                  event
                                ) => {

                                  event.preventDefault()


                                  openMethod(
                                    item
                                  )
                                }
                              }
                            >


                              <div>

                                <strong>

                                  {
                                    item.label
                                  }

                                </strong>


                                <span>

                                  {
                                    item.category
                                  }

                                </span>

                              </div>


                              <ArrowRight
                                size={16}
                              />

                            </button>

                          )
                        )

                      )
                      :
                      (

                        <div className="statistics-search-no-suggestion">

                          No statistical method matches
                          &quot;{query}&quot;.

                        </div>

                      )
                  }

                </div>

              )
            }

          </div>


          {/* =================================================
              FILTER STATUS
              ================================================= */}

          {query.trim() && (

            <div className="statistics-filter-status">


              <span>


                {
                  filteredMethods.length
                }


                {' '}


                result


                {
                  filteredMethods.length
                  ===
                  1
                    ?
                    ''
                    :
                    's'
                }


                {' '}


                for


                {' '}


                <strong>

                  &quot;{query}&quot;

                </strong>


              </span>

            </div>

          )}


          {/* =================================================
              METHOD BUTTONS
              ================================================= */}

          <div className="statistics-method-chip-container">


            {
              filteredMethods.length
              >
              0
                ?
                (

                  filteredMethods.map(
                    (
                      item,
                      index
                    ) => (

                      <button
                        key={
                          `${
                            item.label
                          }-${
                            index
                          }`
                        }

                        type="button"

                        className="statistics-method-chip"

                        title={
                          item.category
                        }

                        onClick={() =>
                          openMethod(
                            item
                          )
                        }
                      >

                        {
                          item.label
                        }

                      </button>

                    )
                  )

                )
                :
                (

                  <div className="statistics-empty-results">


                    <Search
                      size={32}
                    />


                    <h3>

                      No matching analysis found

                    </h3>


                    <p>

                      Try another keyword such as
                      correlation, ANOVA, regression,
                      PCA, reliability or cluster.

                    </p>


                    <button
                      type="button"

                      onClick={
                        clearSearch
                      }
                    >

                      Clear Search

                    </button>

                  </div>

                )
            }

          </div>


          {/* =================================================
              AUTHENTICATED QUICK ACCESS
              ================================================= */}

          {user && (

            <section className="statistics-workspace-shortcuts">


              <div className="statistics-method-heading">


                <span>

                  YOUR WORKSPACE

                </span>


                <h2>

                  Continue working with SSAS

                </h2>


                <p>

                  Access your datasets, analysis,
                  visualizations and reports.

                </p>

              </div>


              <div className="statistics-workspace-grid">


                <button
                  type="button"

                  onClick={() =>
                    navigate(
                      '/datasets'
                    )
                  }
                >

                  <Database
                    size={24}
                  />


                  <div>

                    <strong>
                      Datasets
                    </strong>


                    <span>

                      Upload and manage datasets.

                    </span>

                  </div>

                </button>


                <button
                  type="button"

                  onClick={() =>
                    navigate(
                      '/analysis'
                    )
                  }
                >

                  <BarChart3
                    size={24}
                  />


                  <div>

                    <strong>
                      Statistical Analysis
                    </strong>


                    <span>

                      Run statistical methods.

                    </span>

                  </div>

                </button>


                <button
                  type="button"

                  onClick={() =>
                    navigate(
                      '/visualizations'
                    )
                  }
                >

                  <BarChart3
                    size={24}
                  />


                  <div>

                    <strong>
                      Visualizations
                    </strong>


                    <span>

                      Create charts and plots.

                    </span>

                  </div>

                </button>


                <button
                  type="button"

                  onClick={() =>
                    navigate(
                      '/reports'
                    )
                  }
                >

                  <FileText
                    size={24}
                  />


                  <div>

                    <strong>
                      Reports
                    </strong>


                    <span>

                      Review generated reports.

                    </span>

                  </div>

                </button>

              </div>

            </section>

          )}

        </section>

      </main>


    </div>


  </div>

  )
}
