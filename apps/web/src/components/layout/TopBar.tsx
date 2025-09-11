import React from 'react';

export function TopBar() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-4 dark:border-gray-800 dark:bg-gray-950">
      <div className="font-semibold"># announcements</div>
      <div className="flex items-center space-x-2">
        <div className="h-8 w-8 rounded-full bg-gray-300 dark:bg-gray-700"></div>
        <div className="h-8 w-8 rounded-full bg-blue-300 dark:bg-blue-700"></div>
        <div className="h-8 w-8 rounded-full bg-green-300 dark:bg-green-700"></div>
      </div>
    </header>
  );
}
