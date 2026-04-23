'use client';

import Image from "next/image";
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
      className="inline-flex items-center gap-2 whitespace-nowrap text-xs font-medium text-white transition-colors hover:text-gray-300 sm:text-sm"
    >
      <Image src="/back.png" alt="back arrow" width={40} height={40} className="h-8 w-8 sm:h-10 sm:w-10" />
      <span>Back to Athletics</span>
    </a>
  );
}
