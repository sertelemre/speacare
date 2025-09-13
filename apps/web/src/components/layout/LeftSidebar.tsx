"use client";

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import api from '@/lib/api';
import { Bot, Settings } from 'lucide-react';

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
    <aside className="w-64 flex-shrink-0 border-r border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900 flex flex-col justify-between">
      <div>
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
      </div>

      <div>
        <div className="border-t border-gray-200 dark:border-gray-800 my-4" />
        <nav className="space-y-2">
          <Link href="/dashboard/bots" className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-50">
            <Bot className="h-4 w-4" />
            My Bots
          </Link>
          <Link href="#" className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-50">
            <Settings className="h-4 w-4" />
            Settings
          </Link>
        </nav>
      </div>
    </aside>
  );
}
