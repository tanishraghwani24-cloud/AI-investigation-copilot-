export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">
        AI Investigation Copilot
      </h1>
      <p className="text-lg text-gray-600 mb-8 max-w-2xl">
        Fraud Investigation & Decision Intelligence Platform
      </p>
      <button className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors">
        New Investigation
      </button>
    </div>
  );
}
