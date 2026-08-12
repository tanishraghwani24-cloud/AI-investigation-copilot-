import type { Metadata } from 'next';
import { Inter, Geist } from 'next/font/google';
import Link from 'next/link';
import './globals.css';
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'AI Investigation Copilot',
  description: 'Fraud Investigation & Decision Intelligence Platform',
};

const navItems = [
  { label: 'Dashboard', href: '/' },
  { label: 'Investigations', href: '/investigations' },
  { label: 'Reports', href: '#' },
  { label: 'Settings', href: '#' },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={cn("font-sans", geist.variable)}>
      <body className={`${inter.className} flex h-screen overflow-hidden bg-gray-50`}>
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
          <div className="h-16 flex items-center px-6 border-b border-gray-200">
            <Link href="/" className="text-lg font-semibold text-gray-900">
              Copilot
            </Link>
          </div>
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {navItems.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-100 transition-colors"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <header className="h-16 bg-white border-b border-gray-200 flex items-center px-6 justify-between">
            <h2 className="text-xl font-semibold text-gray-800">Investigation Copilot</h2>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">Analyst Mode</span>
              <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
            </div>
          </header>

          {/* Page Content */}
          <main className="flex-1 overflow-y-auto p-6">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
