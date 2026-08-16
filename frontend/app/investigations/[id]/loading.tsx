export default function InvestigationLoading() {
  return (
    <div className="flex items-center justify-center py-20" role="status">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
      <span className="sr-only">Loading investigation</span>
    </div>
  );
}
