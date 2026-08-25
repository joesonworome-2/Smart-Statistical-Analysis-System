import AppShell from './AppShell'


export default function ModulePlaceholder({
  title,
  description,
  icon,
}) {
  return (
    <AppShell>

      <div className="module-content">

        <div className="module-placeholder-icon">
          {icon}
        </div>

        <span className="eyebrow dark">
          SSAS MODULE
        </span>

        <h1>
          {title}
        </h1>

        <p>
          {description}
        </p>

        <div className="module-placeholder-status">
          Backend service is available.
          Frontend functionality will
          be connected next.
        </div>

      </div>

    </AppShell>
  )
}
