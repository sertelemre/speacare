"use client";

import React from 'react';
import { Bot as BotIcon, Calendar, User, Cpu, MessageSquare } from 'lucide-react';
import { useBotStore } from '@/store/botStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('tr-TR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export function BotDetail() {
  const { selectedBot } = useBotStore();

  if (!selectedBot) {
    return (
      <div className="w-80 flex-shrink-0 border-l border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <BotIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            No Bot Selected
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            Select a bot from the list to view its details.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-80 flex-shrink-0 border-l border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-800 flex flex-col">
      {/* Bot Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-start space-x-3 mb-4">
          <div className="flex-shrink-0">
            <BotIcon className="h-8 w-8 text-blue-500" />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 break-words">
              {selectedBot.name}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {selectedBot.title}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-2">
          <Button size="sm" variant="outline" className="flex-1">
            <MessageSquare className="h-4 w-4 mr-2" />
            Chat
          </Button>
        </div>
      </div>

      {/* Bot Info */}
      <div className="p-6 space-y-6 flex-1 overflow-y-auto">
        {/* Basic Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Basic Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
              <User className="h-4 w-4 mr-2" />
              <span className="font-medium">Character:</span>
              <span className="ml-2">{selectedBot.character}</span>
            </div>
            
            <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
              <Cpu className="h-4 w-4 mr-2" />
              <span className="font-medium">Provider:</span>
              <Badge variant="outline" className="ml-2">
                {selectedBot.llm_provider}
              </Badge>
            </div>

            <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
              <Cpu className="h-4 w-4 mr-2" />
              <span className="font-medium">Model:</span>
              <Badge variant="secondary" className="ml-2">
                {selectedBot.llm_model}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Job Description */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Job Description</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
              {selectedBot.job_description}
            </p>
          </CardContent>
        </Card>

        {/* Character Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Character Details</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
              {selectedBot.character}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
