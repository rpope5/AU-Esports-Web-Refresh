'use client';

import { usePathname } from 'next/navigation';

export default function Header() {
  const pathname = usePathname();
  const isAdmin = pathname.startsWith('/admin');

  if (isAdmin) {
    return null;
  }

  return (
    <a
      href="https://goashlandeagles.com/"
      className="text-white text-sm font-medium flex items-center gap-2 hover:text-gray-300 transition-colors"
    >
      ← Back to Athletics
    </a>
  );
}