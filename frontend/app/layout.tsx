import type { Metadata } from 'next';
import { Inter, Geist } from 'next/font/google';
import Link from 'next/link';
import './globals.css';
import { cn } from "@/lib/utils";
import GradientButtonGroup from "@/components/ui/GradientButtonGroup";

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
        {/* Main Content Area */}
        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          {/* Header */}
          <header className="flex min-h-16 items-center border-b border-gray-200 bg-white px-4 sm:min-h-20 sm:px-6 dark:border-gray-800 dark:bg-gray-900">
            <Link href="/" className="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white">
              <img src="/aria-logo2.png" alt="ARIA logo" className="h-9 w-auto" />
              ARIA
            </Link>
          </header>

          {/* Page Content */}
          <main className="flex-1 overflow-y-auto p-4 pb-28 sm:p-6 sm:pb-32">
            {children}
          </main>
        </div>
        <GradientButtonGroup />
      </body>
    </html>
  );
}
