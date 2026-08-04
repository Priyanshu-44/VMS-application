export default function ComingSoon({ title }) {
  return (
    <div className="p-6 h-full flex items-center justify-center">
      <div className="text-center text-text-dim">
        <div className="text-lg font-medium text-text mb-1">{title}</div>
        <div className="text-sm">Landing in Stage 4.</div>
      </div>
    </div>
  )
}
