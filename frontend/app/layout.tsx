import type { Metadata } from 'next';
import { Inter, Geist } from 'next/font/google';
import Link from 'next/link';
import './globals.css';
import { cn } from "@/lib/utils";
import { MobileNav } from "@/components/layout/MobileNav";
import { NAV_ITEMS } from "@/components/layout/navItems";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Autonomous Risk Investigation Agent',
  description: 'Fraud Investigation & Decision Intelligence Platform',
};

/**
 * Applies the stored theme before the first paint so a reload does not flash
 * the light palette before hydration restores the dark one. Falls back to the
 * OS preference the first time, when nothing has been stored yet.
 */
const THEME_INIT_SCRIPT = `
try {
  var stored = localStorage.getItem('aria-theme');
  var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (stored ? stored === 'dark' : prefersDark) {
    document.documentElement.classList.add('dark');
  }
} catch (e) {}
`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={cn("font-sans", geist.variable)} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body className={`${inter.className} flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-950`}>
        {/* Sidebar — hidden below md, where MobileNav takes over */}
        <aside className="hidden w-64 shrink-0 flex-col border-r border-gray-200 bg-white md:flex dark:border-gray-800 dark:bg-gray-900">
          <div className="h-16 flex items-center px-6 border-b border-gray-200 dark:border-gray-800">
            <Link href="/" className="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white">
              <img src="/aria-logo2.png" alt="ARIA logo" className="h-9 w-auto" />
              ARIA
            </Link>
          </div>
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-100 transition-colors dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-white"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>

        {/* Main Content Area */}
        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          {/* Header */}
          <header className="min-h-16 sm:min-h-20 bg-white border-b border-gray-200 grid grid-cols-[1fr_auto_1fr] items-center gap-2 px-4 sm:px-6 dark:border-gray-800 dark:bg-gray-900">
            <div className="justify-self-start">
              <MobileNav />
            </div>
            <div className="justify-self-center"></div>
            <div className="flex items-center gap-2 justify-self-end">
              <ThemeToggle />
            </div>
          </header>

          {/* Page Content */}
          <main className="flex-1 overflow-y-auto p-4 sm:p-6">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
