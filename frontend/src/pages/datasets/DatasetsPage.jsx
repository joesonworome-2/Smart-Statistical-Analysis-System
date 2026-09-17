import DataWorkspacePage
  from './DataWorkspacePage'


// ==========================================================
// DATASET DASHBOARD
// ==========================================================
//
// /datasets now opens directly into the spreadsheet
// workspace.
//
// DataWorkspacePage handles:
// - Entering new data
// - Copy / paste
// - CSV / Excel upload
// - Saved datasets
// - Autosave
// - Data preparation
//
// ==========================================================


function sortNewestFirst(
  items
) {
  return [
    ...(items || []),
  ].sort(
    (
      a,
      b
    ) => {
      const bTime =
        Date.parse(
          b?.created_at ||
          b?.updated_at ||
          ''
        ) || 0

      const aTime =
        Date.parse(
          a?.created_at ||
          a?.updated_at ||
          ''
        ) || 0

      if (
        bTime !== aTime
      ) {
        return (
          bTime -
          aTime
        )
      }

      return String(
        b?.id || ''
      ).localeCompare(
        String(
          a?.id || ''
        )
      )
    }
  )
}


export default function DatasetsPage() {
  return (
    <DataWorkspacePage />
  )
}
