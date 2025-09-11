"use client";

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

interface Channel {
  id: number;
  name: string;
  description: string;
}

const fetchChannels = async (): Promise<Channel[]> => {
  const { data } = await api.get('/api/channels/');
  return data;
};

export function LeftSidebar() {
  const { data: channels, isLoading, error } = useQuery<Channel[]>({
    queryKey: ['channels'],
    queryFn: fetchChannels,
  });

  return (
    <aside className="w-64 flex-shrink-0 border-r border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900">
      <h2 className="text-lg font-semibold">Channels</h2>
      <div className="mt-4 space-y-2">
        {isLoading && <p className="text-sm text-gray-500">Loading channels...</p>}
        {error && <p className="text-sm text-red-500">Error fetching channels.</p>}
        {channels && channels.map((channel) => (
          <p key={channel.id} className="text-sm text-gray-500 hover:text-gray-900 dark:hover:text-gray-50 cursor-pointer">
            # {channel.name}
          </p>
        ))}
        {!isLoading && !error && channels?.length === 0 && (
            <p className="text-sm text-gray-500">No channels found.</p>
        )}
      </div>
    </aside>
  );
}
