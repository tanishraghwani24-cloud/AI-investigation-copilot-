import Link from 'next/link';
import { GitBranch, MessageCircle, Briefcase, Mail } from 'lucide-react';
import { NAV_ITEMS } from '@/components/layout/navItems';

export function Footer() {
  return (
    <footer className="-mx-4 sm:-mx-6 -mb-12 sm:-mb-16 border-t border-gray-200 bg-white pt-12 pb-8 sm:pt-16 sm:pb-12 dark:border-gray-800 dark:bg-[#0B1120]">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-4 lg:gap-12">
          
          {/* Brand Col */}
          <div className="md:col-span-1">
            <Link href="/" className="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white mb-4">
              <img src="/aria-logo4.png" alt="ARIA logo" className="h-8 w-auto dark:brightness-0 dark:invert" />
              ARIA
            </Link>
            <p className="text-sm text-gray-500 dark:text-gray-400 max-w-xs leading-relaxed">
              Autonomous Risk Investigation Agent. Bringing risk signals and investigation context into one defensible decision workflow.
            </p>
          </div>

          {/* Navigation Col */}
          <div className="md:col-span-1">
            <h3 className="text-sm font-semibold text-gray-900 tracking-wider uppercase mb-4 dark:text-white">
              Platform
            </h3>
            <ul className="space-y-3">
              {NAV_ITEMS.map((item) => (
                <li key={item.label}>
                  <Link 
                    href={item.href} 
                    className="text-sm text-gray-500 hover:text-purple-600 transition-colors dark:text-gray-400 dark:hover:text-purple-400 inline-flex items-center gap-2 group"
                  >
                    <item.icon className="h-4 w-4 text-gray-400 group-hover:text-purple-500 transition-colors" />
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources Col */}
          <div className="md:col-span-1">
            <h3 className="text-sm font-semibold text-gray-900 tracking-wider uppercase mb-4 dark:text-white">
              Resources
            </h3>
            <ul className="space-y-3">
              {['Documentation', 'API Reference', 'Case Studies', 'Blog'].map((item) => (
                <li key={item}>
                  <Link href="#" className="text-sm text-gray-500 hover:text-purple-600 transition-colors dark:text-gray-400 dark:hover:text-purple-400">
                    {item}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Connect Col */}
          <div className="md:col-span-1">
            <h3 className="text-sm font-semibold text-gray-900 tracking-wider uppercase mb-4 dark:text-white">
              Connect
            </h3>
            <div className="flex space-x-4 mb-6">
              <a href="#" className="text-gray-400 hover:text-purple-600 transition-colors dark:hover:text-purple-400">
                <span className="sr-only">Twitter</span>
                <MessageCircle className="h-5 w-5" />
              </a>
              <a href="#" className="text-gray-400 hover:text-purple-600 transition-colors dark:hover:text-purple-400">
                <span className="sr-only">GitHub</span>
                <GitBranch className="h-5 w-5" />
              </a>
              <a href="#" className="text-gray-400 hover:text-purple-600 transition-colors dark:hover:text-purple-400">
                <span className="sr-only">LinkedIn</span>
                <Briefcase className="h-5 w-5" />
              </a>
            </div>
            <a href="mailto:contact@example.com" className="inline-flex items-center justify-center gap-2 rounded-lg bg-gray-100 px-4 py-2.5 text-sm font-medium text-gray-900 transition-all hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-100 dark:hover:bg-gray-700 dark:hover:ring-1 dark:hover:ring-purple-500/50 w-full sm:w-auto">
              <Mail className="h-4 w-4" />
              Contact Us
            </a>
          </div>

        </div>

        <div className="mt-12 border-t border-gray-200 pt-8 flex flex-col md:flex-row justify-between items-center gap-4 dark:border-gray-800">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            &copy; {new Date().getFullYear()} ARIA. All rights reserved.
          </p>
          <div className="flex space-x-6 text-sm text-gray-500 dark:text-gray-400">
            <Link href="#" className="hover:text-purple-600 transition-colors dark:hover:text-purple-400">Privacy Policy</Link>
            <Link href="#" className="hover:text-purple-600 transition-colors dark:hover:text-purple-400">Terms of Service</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
