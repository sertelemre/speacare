"use client";

import React from 'react';
import { useChannelSocket } from '@/hooks/useChannelSocket';

export function MainContent() {
  // For now, hardcode channel ID 1 to test the WebSocket connection.
  // In a real app, this would come from the URL or a global state.
  useChannelSocket(1);

  return (
    <main className="flex-1 p-4">
      <div className="space-y-4">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 flex-shrink-0 rounded-full bg-gray-300 dark:bg-gray-700"></div>
          <div className="flex-1">
            <p className="font-semibold">Jules</p>
            <p className="text-gray-700 dark:text-gray-300">
              Hey team, what are our thoughts on the new pricing model proposal?
            </p>
          </div>
        </div>
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 flex-shrink-0 rounded-full bg-blue-300 dark:bg-blue-700"></div>
          <div className="flex-1">
            <p className="font-semibold">Analyst Bot</p>
            <p className="text-gray-700 dark:text-gray-300">
              Based on the provided data, the new model projects a 15% increase in MRR, but it might alienate our enterprise customers. I suggest we run an A/B test on a small segment first.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
