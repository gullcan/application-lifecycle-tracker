interface DashboardSummaryProps {
  isReady: boolean
  totalCount: number
  followUpCount: number
  activeCount: number
}

export function DashboardSummary({
  isReady,
  totalCount,
  followUpCount,
  activeCount,
}: DashboardSummaryProps) {
  return (
    <section
      className="summary-grid"
      aria-label="Başvuru özeti"
    >
      <article className="summary-card">
        <span>Listelenen başvuru</span>
        <strong>{isReady ? totalCount : '—'}</strong>
        <p>İlk 100 başvuru gösteriliyor.</p>
      </article>

      <article className="summary-card">
        <span>Takip bekleyen</span>
        <strong>{isReady ? followUpCount : '—'}</strong>
        <p>Bugün ilgilenmen gereken başvurular.</p>
      </article>

      <article className="summary-card">
        <span>Aktif süreçler</span>
        <strong>{isReady ? activeCount : '—'}</strong>
        <p>Henüz terminal duruma ulaşmayan kayıtlar.</p>
      </article>
    </section>
  )
}
