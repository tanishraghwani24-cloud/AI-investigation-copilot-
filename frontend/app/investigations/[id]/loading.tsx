export default function InvestigationLoading() {
  return (
    <div className="space-y-6 animate-pulse">
      <div>
        <div className="mb-4 h-5 w-40 rounded bg-gray-200 dark:bg-gray-700" />
        <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="h-8 w-64 rounded bg-gray-200 dark:bg-gray-700" />
            <div className="h-5 w-48 rounded bg-gray-200 dark:bg-gray-700" />
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="h-6 w-24 rounded-full bg-gray-200 dark:bg-gray-700" />
            <div className="h-6 w-24 rounded-full bg-gray-200 dark:bg-gray-700" />
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-6">
          <div className="h-4 w-32 rounded bg-gray-100 dark:bg-gray-800" />
          <div className="h-4 w-32 rounded bg-gray-100 dark:bg-gray-800" />
        </div>
      </div>

      <section className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <div className="flex items-center gap-3 border-b border-gray-100 px-6 py-4 dark:border-gray-800">
          <div className="h-9 w-9 rounded-lg bg-gray-200 dark:bg-gray-700" />
          <div className="h-6 w-32 rounded bg-gray-200 dark:bg-gray-700" />
        </div>
        <div className="space-y-4 px-6 py-5">
          <div className="h-5 w-40 rounded bg-gray-200 mb-4 dark:bg-gray-700" />
          <div className="h-32 w-full rounded-lg bg-gray-100 dark:bg-gray-800" />
          <div className="h-5 w-32 rounded bg-gray-200 mb-4 mt-6 dark:bg-gray-700" />
          <div className="grid grid-cols-1 gap-x-8 gap-y-4 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="space-y-2">
                <div className="h-4 w-16 rounded bg-gray-200 dark:bg-gray-700" />
                <div className="h-5 w-24 rounded bg-gray-200 dark:bg-gray-700" />
              </div>
            ))}
          </div>
        </div>
      </section>

      {[1, 2, 3].map((i) => (
        <section key={i} className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <div className="flex items-center gap-3 border-b border-gray-100 px-6 py-4 dark:border-gray-800">
            <div className="h-9 w-9 rounded-lg bg-gray-200 dark:bg-gray-700" />
            <div className="h-6 w-48 rounded bg-gray-200 dark:bg-gray-700" />
          </div>
          <div className="px-6 py-5 space-y-3">
            <div className="h-4 w-full rounded bg-gray-100 dark:bg-gray-800" />
            <div className="h-4 w-5/6 rounded bg-gray-100 dark:bg-gray-800" />
            <div className="h-4 w-4/6 rounded bg-gray-100 dark:bg-gray-800" />
          </div>
        </section>
      ))}
    </div>
  );
}
