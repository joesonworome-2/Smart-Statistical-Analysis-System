import {
  Check,
  Copy,
  FilePlus2,
} from 'lucide-react'

import {
  useState,
} from 'react'


function displayValue(value) {
  if (
    value === null ||
    value === undefined ||
    value === ''
  ) {
    return '—'
  }

  if (
    typeof value === 'number'
  ) {
    if (
      Number.isInteger(value)
    ) {
      return value.toLocaleString()
    }

    const absolute =
      Math.abs(value)

    if (
      absolute > 0 &&
      absolute < 0.0001
    ) {
      return value.toExponential(4)
    }

    return Number(
      value.toFixed(5)
    ).toLocaleString()
  }

  return String(value)
}


export default function ResultTable({
  title,
  columns = [],
  rows = [],
  interpretation = '',
  onAddToReport = null,
}) {
  const [
    copied,
    setCopied,
  ] = useState(false)


  const copyTable =
    async () => {
      const lines = []

      lines.push(
        columns.join('\t')
      )

      rows.forEach(
        (row) => {
          lines.push(
            columns
              .map(
                (column) =>
                  displayValue(
                    row[column]
                  )
              )
              .join('\t')
          )
        }
      )

      await navigator
        .clipboard
        .writeText(
          lines.join('\n')
        )

      setCopied(true)

      window.setTimeout(
        () =>
          setCopied(false),
        1600
      )
    }


  return (
    <section className="analysis-result-section">

      <div className="analysis-result-heading">

        <h3>
          {title}
        </h3>

        <div className="analysis-result-actions">

          <button
            type="button"
            onClick={copyTable}
          >
            {copied ? (
              <Check size={14} />
            ) : (
              <Copy size={14} />
            )}

            {copied
              ? 'Copied'
              : 'Copy'}
          </button>


          {onAddToReport && (
            <button
              type="button"
              onClick={
                onAddToReport
              }
            >
              <FilePlus2
                size={14}
              />

              Add to Report
            </button>
          )}

        </div>

      </div>


      <div className="analysis-result-table-wrapper">

        <table className="analysis-result-table">

          <thead>

            <tr>

              {columns.map(
                (column) => (
                  <th key={column}>
                    {column}
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
                    `result-row-${rowIndex}`
                  }
                >

                  {columns.map(
                    (
                      column,
                      columnIndex
                    ) => (
                      <td
                        key={
                          `${rowIndex}-${column}`
                        }
                        className={
                          columnIndex === 0
                            ? 'result-row-label'
                            : ''
                        }
                      >
                        {displayValue(
                          row[column]
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


      {interpretation && (
        <div className="analysis-interpretation">

          <h4>
            Interpretation
          </h4>

          <p>
            {interpretation}
          </p>

        </div>
      )}

    </section>
  )
}
