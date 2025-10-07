"use client";

import React from 'react';
import { FileText, Image, Link, File, Calendar, User, Download, ExternalLink } from 'lucide-react';
import { useProjectStore } from '@/store/projectStore';
import { Button } from '@/components/ui/button';

const getAssetIcon = (assetType: string) => {
  switch (assetType) {
    case 'document':
    case 'analysis':
      return <FileText className="h-6 w-6" />;
    case 'image':
      return <Image className="h-6 w-6" />;
    case 'reference':
      return <Link className="h-6 w-6" />;
    default:
      return <File className="h-6 w-6" />;
  }
};

const formatFileSize = (bytes?: number) => {
  if (!bytes) return 'Unknown size';
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('tr-TR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const getAssetTypeLabel = (assetType: string) => {
  switch (assetType) {
    case 'document':
      return 'Document';
    case 'analysis':
      return 'Analysis Document';
    case 'image':
      return 'Image/Logo';
    case 'brochure':
      return 'Brochure';
    case 'reference':
      return 'Reference Link';
    case 'other':
      return 'Other';
    default:
      return assetType;
  }
};

export function AssetDetail() {
  const { selectedAsset } = useProjectStore();

  if (!selectedAsset) {
    return (
      <div className="w-80 flex-shrink-0 border-l border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            No Asset Selected
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            Select an asset to view its details and content.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-80 flex-shrink-0 border-l border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-800 flex flex-col">
      {/* Asset Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-start space-x-3 mb-4">
          <div className="flex-shrink-0">
            {getAssetIcon(selectedAsset.asset_type)}
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 break-words">
              {selectedAsset.name}
            </h2>
            <p className="text-sm text-blue-600 dark:text-blue-400 font-medium">
              {getAssetTypeLabel(selectedAsset.asset_type)}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-2">
          {selectedAsset.file && selectedAsset.file_url && (
            <Button size="sm" variant="outline" asChild>
              <a href={selectedAsset.file_url} target="_blank" rel="noopener noreferrer">
                <Download className="h-4 w-4 mr-2" />
                Download
              </a>
            </Button>
          )}
          {selectedAsset.url && (
            <Button size="sm" variant="outline" asChild>
              <a href={selectedAsset.url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4 mr-2" />
                Open Link
              </a>
            </Button>
          )}
        </div>
      </div>

      {/* Asset Info */}
      <div className="p-6 space-y-4">
        {/* Metadata */}
        <div className="space-y-3">
          <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
            <Calendar className="h-4 w-4 mr-2" />
            <span>Added {formatDate(selectedAsset.created_at)}</span>
          </div>
          
          <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
            <User className="h-4 w-4 mr-2" />
            <span>By {selectedAsset.created_by}</span>
          </div>

          {selectedAsset.file_size && (
            <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
              <File className="h-4 w-4 mr-2" />
              <span>{formatFileSize(selectedAsset.file_size)}</span>
            </div>
          )}

          {selectedAsset.mime_type && (
            <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
              <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                {selectedAsset.mime_type}
              </span>
            </div>
          )}
        </div>

        {/* Description */}
        {selectedAsset.description && (
          <div>
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
              Description
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
              {selectedAsset.description}
            </p>
          </div>
        )}

        {/* Summary */}
        {selectedAsset.summary && (
          <div>
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
              AI Summary
            </h4>
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
              <p className="text-sm text-blue-800 dark:text-blue-200 whitespace-pre-wrap">
                {selectedAsset.summary}
              </p>
            </div>
          </div>
        )}

        {/* File Preview */}
        {selectedAsset.file && selectedAsset.mime_type?.startsWith('image/') && (
          <div>
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
              Preview
            </h4>
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <img
                src={selectedAsset.file_url}
                alt={selectedAsset.name}
                className="w-full h-auto max-h-48 object-cover"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
