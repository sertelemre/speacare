import React from 'react';

export function RightSidebar() {
  return (
    <aside className="w-80 flex-shrink-0 border-l border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900">
      <h2 className="text-lg font-semibold">Notes</h2>
      <div className="mt-4">
        <div className="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
          <h3 className="font-semibold">Meeting Summary</h3>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-sm">
            <li>Decision: Proceed with A/B test.</li>
            <li>Action: PM to define test segments.</li>
            <li>Risk: Potential churn from enterprise clients.</li>
          </ul>
        </div>
      </div>
    </aside>
  );
}
