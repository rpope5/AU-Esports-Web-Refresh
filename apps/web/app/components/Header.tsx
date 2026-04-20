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
      className="text-white text-sm font-medium flex items-center hover:text-gray-300 transition-colors">
      <Image src="/back.png" alt="back arrow" width={40} height={40} className="w-10 h-10" /> Back to Athletics
    </a>
  );
}
