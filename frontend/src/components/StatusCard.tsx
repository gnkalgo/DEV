export function StatusCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <article className="card widget">
      <h2>{title}</h2>
      {children}
    </article>
  );
}
