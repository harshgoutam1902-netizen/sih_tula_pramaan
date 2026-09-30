export default function AdvisoryBadge() {
  return (
    <div className="flex items-center gap-2">
      <span className="px-2 py-1 text-xs font-semibold bg-blue-100 text-blue-800 rounded">
        Advisory only
      </span>
      <span className="px-2 py-1 text-xs font-semibold bg-yellow-100 text-yellow-800 rounded">
        DRAFT
      </span>
    </div>
  );
}
