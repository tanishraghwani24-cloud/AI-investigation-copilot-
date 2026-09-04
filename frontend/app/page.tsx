import Link from "next/link";
import MagnifyLens from "@/components/MagnifyLens";

export default function Home() {
  return (
    <div className="flex w-full flex-col items-center justify-center min-h-[60vh] px-2 text-center">
      <MagnifyLens />
      <p className="text-base sm:text-lg text-gray-600 mb-8 max-w-2xl dark:text-gray-300">
        Fraud Investigation & Decision Intelligence Platform
      </p>
      <Link
        href="/officer"
        className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors dark:bg-blue-500 dark:hover:bg-blue-400"
      >
        Go to Officer Inbox
      </Link>
    </div>
  );
}

