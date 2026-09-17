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

import { useAuth } from '../context/AuthContext'
import './StatisticsCalculatorLanding.css'

const STATISTICAL_METHODS = [
  {
    label: 'Prepare Data',
    category: 'Data Preparation',
    method: 'descriptive',
    keywords: ['clean', 'prepare', 'missing', 'dataset', 'preprocessing'],
  },

  {
    label: 'Descriptive Statistics',
    category: 'Descriptive Statistics',
    method: 'descriptive',
    keywords: ['summary', 'describe', 'statistics'],
  },
  {
    label: 'Mean',
    category: 'Descriptive Statistics',
    method: 'descriptive',
    keywords: ['average', 'arithmetic mean'],
  },
  {
    label: 'Median',
    category: 'Descriptive Statistics',
    method: 'descriptive',
    keywords: ['middle', 'central tendency'],
  },
  {
    label: 'Mode',
    category: 'Descriptive Statistics',
    method: 'descriptive',
    keywords: ['frequency', 'most common'],
  },
  {
    label: 'Standard Deviation',
    category: 'Descriptive Statistics',
    method: 'descriptive',
    keywords: ['sd', 'spread', 'dispersion'],
  },
  {
    label: 'Variance',
    category: 'Descriptive Statistics',
    method: 'descriptive',
    keywords: ['spread', 'dispersion'],
  },
  {
    label: 'Frequency Table',
    category: 'Descriptive Statistics',
    method: 'descriptive',
    keywords: ['frequency', 'count', 'table'],
  },
  {
    label: 'Confidence Interval',
    category: 'Descriptive Statistics',
    method: 'descriptive',
    keywords: ['ci', 'confidence interval'],
  },
  {
    label: 'Normality Test',
    category: 'Descriptive Statistics',
    method: 'descriptive',
    keywords: ['normality', 'shapiro', 'distribution'],
  },

  {
    label: 'Hypothesis Testing',
    category: 'Hypothesis Tests',
    method: 'hypothesis',
    keywords: ['hypothesis', 'significance', 'p value'],
  },
  {
    label: 'One Sample t-Test',
    category: 'Hypothesis Tests',
    method: 'hypothesis',
    keywords: ['t test', 'one sample'],
  },
  {
    label: 'Independent Samples t-Test',
    category: 'Hypothesis Tests',
    method: 'hypothesis',
    keywords: ['independent', 'two sample', 't test'],
  },
  {
    label: 'Paired Samples t-Test',
    category: 'Hypothesis Tests',
    method: 'hypothesis',
    keywords: ['paired', 'before after', 't test'],
  },
  {
    label: 'Mann-Whitney U Test',
    category: 'Hypothesis Tests',
    method: 'hypothesis',
    keywords: ['nonparametric', 'independent'],
  },
  {
    label: 'Wilcoxon Signed-Rank Test',
    category: 'Hypothesis Tests',
    method: 'hypothesis',
    keywords: ['wilcoxon', 'nonparametric', 'paired'],
  },
  {
    label: 'Chi-Square Test',
    category: 'Hypothesis Tests',
    method: 'hypothesis',
    keywords: ['chi square', 'categorical', 'association'],
  },
  {
    label: 'ANOVA',
    category: 'Hypothesis Tests',
    method: 'hypothesis',
    keywords: ['analysis of variance', 'groups', 'means'],
  },
  {
    label: 'Kruskal-Wallis Test',
    category: 'Hypothesis Tests',
    method: 'hypothesis',
    keywords: ['kruskal', 'nonparametric', 'anova'],
  },

  {
    label: 'Correlation',
    category: 'Correlation',
    method: 'correlation',
    keywords: ['relationship', 'association'],
  },
  {
    label: 'Pearson Correlation',
    category: 'Correlation',
    method: 'correlation',
    keywords: ['pearson', 'linear'],
  },
  {
    label: 'Spearman Correlation',
    category: 'Correlation',
    method: 'correlation',
    keywords: ['spearman', 'rank', 'ordinal'],
  },
  {
    label: 'Kendall Correlation',
    category: 'Correlation',
    method: 'correlation',
    keywords: ['kendall', 'tau', 'rank'],
  },
  {
    label: 'Correlation Matrix',
    category: 'Correlation',
    method: 'correlation',
    keywords: ['matrix', 'correlation'],
  },

  {
    label: 'Regression',
    category: 'Regression',
    method: 'regression',
    keywords: ['regression', 'prediction', 'relationship'],
  },
  {
    label: 'Linear Regression',
    category: 'Regression',
    method: 'regression',
    keywords: ['ols', 'linear model'],
  },
  {
    label: 'Multiple Linear Regression',
    category: 'Regression',
    method: 'regression',
    keywords: ['multiple regression', 'predictors'],
  },
  {
    label: 'Regression Diagnostics',
    category: 'Regression',
    method: 'regression',
    keywords: ['vif', 'residuals', 'diagnostics'],
  },

  {
    label: 'Predictive Analytics',
    category: 'Predictive Analytics',
    method: 'predictive',
    keywords: ['future', 'prediction', 'machine learning'],
  },
  {
    label: 'Decision Tree',
    category: 'Predictive Analytics',
    method: 'predictive',
    keywords: ['tree', 'machine learning', 'prediction'],
  },
  {
    label: 'Random Forest',
    category: 'Predictive Analytics',
    method: 'predictive',
    keywords: ['forest', 'machine learning', 'prediction'],
  },
  {
    label: 'Gradient Boosting',
    category: 'Predictive Analytics',
    method: 'predictive',
    keywords: ['boosting', 'machine learning', 'prediction'],
  },

  {
    label: 'ANCOVA',
    category: 'ANCOVA',
    method: 'ancova',
    keywords: ['analysis covariance', 'covariate', 'adjusted means'],
  },

  {
    label: 'Survival Analysis',
    category: 'Survival Analysis',
    method: 'survival',
    keywords: ['survival', 'time to event', 'censoring'],
  },
  {
    label: 'Kaplan-Meier Analysis',
    category: 'Survival Analysis',
    method: 'survival',
    keywords: ['kaplan meier', 'survival'],
  },
  {
    label: 'Log-Rank Test',
    category: 'Survival Analysis',
    method: 'survival',
    keywords: ['log rank', 'survival groups'],
  },

  {
    label: 'Exploratory Factor Analysis',
    category: 'EFA / PCA',
    method: 'factor',
    keywords: ['efa', 'factor analysis', 'latent variables'],
  },
  {
    label: 'Principal Component Analysis',
    category: 'EFA / PCA',
    method: 'factor',
    keywords: ['pca', 'principal components'],
  },

  {
    label: 'Reliability Analysis',
    category: 'Reliability',
    method: 'reliability',
    keywords: ['reliability', 'internal consistency'],
  },
  {
    label: "Cronbach's Alpha",
    category: 'Reliability',
    method: 'reliability',
    keywords: ['cronbach', 'alpha', 'reliability'],
  },

  {
    label: 'Cluster Analysis',
    category: 'Cluster',
    method: 'cluster',
    keywords: ['cluster', 'groups', 'segmentation'],
  },
  {
    label: 'K-Means Clustering',
    category: 'Cluster',
    method: 'cluster',
    keywords: ['kmeans', 'clusters'],
  },

  {
    label: 'Measurement System Analysis',
    category: 'MSA',
    method: 'msa',
    keywords: ['msa', 'measurement system'],
  },
  {
    label: 'Process Capability',
    category: 'Process Capability',
    method: 'capability',
    keywords: ['cp', 'cpk', 'capability'],
  },
  {
    label: 'Statistical Process Control',
    category: 'SPC',
    method: 'spc',
    keywords: ['spc', 'control chart', 'process monitoring'],
  },
  {
    label: 'Design of Experiments',
    category: 'DoE',
    method: 'doe',
    keywords: ['doe', 'experiment', 'factorial'],
  },

  {
    label: 'Charts and Visualization',
    category: 'Visualization',
    method: 'descriptive',
    keywords: ['graph', 'chart', 'plot'],
  },
  {
    label: 'Bar Chart',
    category: 'Visualization',
    method: 'descriptive',
    keywords: ['bar', 'chart'],
  },
  {
    label: 'Histogram',
    category: 'Visualization',
    method: 'descriptive',
    keywords: ['distribution', 'histogram'],
  },
  {
    label: 'Scatter Plot',
    category: 'Visualization',
    method: 'correlation',
    keywords: ['scatter', 'plot', 'relationship'],
  },
  {
    label: 'Line Chart',
    category: 'Visualization',
    method: 'descriptive',
    keywords: ['line', 'time series'],
  },
  {
    label: 'Boxplot',
    category: 'Visualization',
    method: 'descriptive',
    keywords: ['box plot', 'outlier', 'distribution'],
  },
]

function normalizeSearchText(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
}

function getMatchScore(item, query) {
  const normalizedQuery = normalizeSearchText(query)
  const label = normalizeSearchText(item.label)
  const category = normalizeSearchText(item.category)
  const keywords = item.keywords
    .map(normalizeSearchText)
    .join(' ')

  if (!normalizedQuery) return 1
  if (label === normalizedQuery) return 100
  if (label.startsWith(normalizedQuery)) return 80
  if (label.includes(normalizedQuery)) return 60
  if (category.includes(normalizedQuery)) return 40
  if (keywords.includes(normalizedQuery)) return 30

  const searchable = `${label} ${category} ${keywords}`
  const words = normalizedQuery.split(/\s+/)

  return words.every((word) => searchable.includes(word))
    ? 20
    : 0
}

function datasetPathForMethod(item) {
  const params = new URLSearchParams()

  if (item?.method) {
    params.set('method', item.method)
  }

  if (item?.label) {
    params.set('selected', item.label)
  }

  return `/datasets?${params.toString()}`
}

export default function StatisticsCalculatorLanding() {
  const navigate = useNavigate()
  const location = useLocation()
  const isDashboard = location.pathname === '/dashboard'
  const { user, logout } = useAuth()

  const [query, setQuery] = useState('')
  const [searchFocused, setSearchFocused] = useState(false)

  const filteredMethods = useMemo(() => {
    const normalizedQuery = normalizeSearchText(query)

    if (!normalizedQuery) {
      return STATISTICAL_METHODS
    }

    return STATISTICAL_METHODS
      .map((item) => ({
        ...item,
        score: getMatchScore(item, normalizedQuery),
      }))
      .filter((item) => item.score > 0)
      .sort((first, second) => second.score - first.score)
  }, [query])

  const suggestions = useMemo(() => {
    if (!query.trim()) return []
    return filteredMethods.slice(0, 8)
  }, [query, filteredMethods])

  const goToDataFirst = (destination = '/datasets') => {
    if (user) {
      navigate(destination)
      return
    }

    navigate('/login', {
      state: {
        from: destination,
      },
    })
  }

  const openMethod = (item) => {
    if (!item) return
    setSearchFocused(false)
    goToDataFirst(datasetPathForMethod(item))
  }

  const handleSubmit = (event) => {
    event.preventDefault()

    if (filteredMethods.length > 0) {
      openMethod(filteredMethods[0])
    }
  }

  const clearSearch = () => {
    setQuery('')
    setSearchFocused(true)
  }

  const handleLogout = async () => {
    try {
      await logout()
    } finally {
      navigate('/')
    }
  }

  const focusSearch = () => {
    const input = document.getElementById(
      'statistics-method-search'
    )

    input?.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    })

    window.setTimeout(() => input?.focus(), 300)
  }

  return (
    <div
      className={
        isDashboard
          ? 'statistics-calculator-page dashboard-video-mode'
          : 'statistics-calculator-page'
      }
    >
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
        <header className="statistics-calculator-header">
          <button
            type="button"
            className="statistics-calculator-brand"
            onClick={() => navigate(user ? '/dashboard' : '/')}
          >
            <BarChart3 size={38} />

            <div>
              <strong>SSAS</strong>
              <span>
                Smart Statistical Analysis System
              </span>
            </div>
          </button>

          <nav className="statistics-calculator-navigation">
            <button
              type="button"
              className="active"
              onClick={() => navigate(user ? '/dashboard' : '/')}
            >
              Statistics Calculator
            </button>

            {user && (
              <button
                type="button"
                onClick={() => navigate('/survey')}
              >
                Survey
              </button>
            )}

            {user && (
              <button
                type="button"
                onClick={() => navigate('/datasets')}
              >
                Datasets
              </button>
            )}

            {user && (
              <button
                type="button"
                onClick={() => navigate('/analysis')}
              >
                Analysis
              </button>
            )}

            {user && (
              <button
                type="button"
                onClick={() => navigate('/visualizations')}
              >
                Visualization
              </button>
            )}

            {user && (
              <button
                type="button"
                onClick={() => navigate('/reports')}
              >
                Reports
              </button>
            )}
          </nav>

          <div className="statistics-calculator-header-actions">
            {user ? (
              <>
                <button
                  type="button"
                  onClick={() => navigate('/datasets')}
                >
                  <User size={18} />
                  {user.username || user.name || 'Workspace'}
                </button>

                <button
                  type="button"
                  onClick={handleLogout}
                >
                  <LogOut size={18} />
                  Sign out
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={() => navigate('/login')}
              >
                Login
              </button>
            )}

            <Search
              size={22}
              onClick={focusSearch}
              style={{ cursor: 'pointer' }}
            />
          </div>
        </header>

        <section className="statistics-calculator-hero">
          <div className="statistics-calculator-hero-content">
            <span className="statistics-calculator-eyebrow">
              SMART STATISTICAL ANALYSIS SYSTEM
            </span>

            <h1>
              Statistical analysis from data to report.
            </h1>

            <p>
              Upload or paste your dataset, prepare the data,
              run statistical analysis, create visualizations,
              and generate a report through one guided workflow.
            </p>

            <div className="statistics-calculator-hero-actions">
              <button
                type="button"
                className="statistics-primary-action"
                onClick={() => goToDataFirst('/datasets')}
              >
                Start now
                <ArrowRight size={18} />
              </button>

              {user && (
                <button
                  type="button"
                  className="statistics-secondary-action"
                  onClick={() => navigate('/reports')}
                >
                  <FileText size={18} />
                  Reports
                </button>
              )}
            </div>
          </div>
        </section>

        <section className="statistics-search-section">
          <div className="statistics-search-heading">
            <Database size={22} />
            <div>
              <h2>Choose a statistical method</h2>
              <p>
                SSAS will take you to Datasets first so the
                selected method always has data to work with.
              </p>
            </div>
          </div>

          <form
            className="statistics-method-search"
            onSubmit={handleSubmit}
          >
            <Search size={20} />

            <input
              id="statistics-method-search"
              type="search"
              value={query}
              placeholder="Search ANOVA, correlation, regression, predictive analytics..."
              onChange={(event) => setQuery(event.target.value)}
              onFocus={() => setSearchFocused(true)}
              onBlur={() => {
                window.setTimeout(
                  () => setSearchFocused(false),
                  150
                )
              }}
            />

            {query && (
              <button
                type="button"
                className="statistics-search-clear"
                onClick={clearSearch}
                aria-label="Clear search"
              >
                <X size={18} />
              </button>
            )}

            <button
              type="submit"
              className="statistics-search-submit"
            >
              Search
            </button>

            {searchFocused && suggestions.length > 0 && (
              <div className="statistics-search-suggestions">
                {suggestions.map((item) => (
                  <button
                    key={`${item.category}-${item.label}`}
                    type="button"
                    onMouseDown={(event) => event.preventDefault()}
                    onClick={() => openMethod(item)}
                  >
                    <strong>{item.label}</strong>
                    <span>{item.category}</span>
                  </button>
                ))}
              </div>
            )}
          </form>

          <div className="statistics-method-grid">
            {filteredMethods.map((item) => (
              <button
                key={`${item.category}-${item.label}`}
                type="button"
                className="statistics-method-chip"
                onClick={() => openMethod(item)}
              >
                {item.label}
              </button>
            ))}
          </div>

          {!filteredMethods.length && (
            <div className="statistics-no-results">
              No matching statistical method was found.
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
